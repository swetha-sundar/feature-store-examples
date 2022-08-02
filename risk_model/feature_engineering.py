import pandas as pd
import datetime
from sklearn.preprocessing import OneHotEncoder
import warnings
warnings.filterwarnings("ignore")

application_train = pd.read_csv('../data/application_train.csv')
application_test = pd.read_csv('../data/application_test.csv')
bureau = pd.read_csv('../data/bureau.csv')
bureau_balance = pd.read_csv('../data/bureau_balance.csv')
credit_card_balance = pd.read_csv('../data/credit_card_balance.csv')
installments_payments = pd.read_csv('../data/installments_payments.csv')
pos_cash_balance = pd.read_csv('../data/POS_CASH_balance.csv')
previous_application = pd.read_csv('../data/previous_application.csv')

application_train['EVENT_TIMESTAMP'] = datetime.datetime(2022, 8, 3)
application_train['CREATED_TIMESTAMP'] = datetime.datetime.now()


# Static Features

###
# Top features for static feature views:
# - OCCUPATION_TYPE
# - AMT_INCOME_TOTAL
# - NAME_INCOME_TYPE
# - DAYS_LAST_PHONE_CHANGE
# - ORGANIZATION_TYPE
# - AMT_CREDIT
# - AMT_GOODS_PRICE
# - DAYS_REGISTRATION
# - AMT_ANNUITY
# - CODE_GENDER
# - DAYS_ID_PUBLISH
# - NAME_EDUCATION_TYPE
# - DAYS_EMPLOYED
# - DAYS_BIRTH
# - EXT_SOURCE_1
# - EXT_SOURCE_2
# - EXT_SOURCE_3
###

application_train.to_parquet('../data/static_feature_table.parquet')

# BUREAU FEATURES


def bureauBalanceRollingCreditLoan(df):
    df_final = df.copy()
    df_final['STATUS'] = df_final['STATUS'].replace(['X', 'C'], '0')
    df_final['STATUS'] = pd.to_numeric(df_final['STATUS'])
    df_final = df_final.groupby("SK_ID_BUREAU")['STATUS'].agg(
        lambda x: x.ewm(span=x.shape[0], adjust=False).mean().mean()
    )
    df_final = df_final.reset_index(name="CREDIT_STATUS_EMA_AVG")
    df_final = df_final.set_index('SK_ID_BUREAU')
    return df_final


bureauBalanceRollingCreditLoan(bureau_balance)


def aggCountBureau(df):
    agg = df.groupby("SK_ID_CURR")
    # count number of loans
    df_final = pd.DataFrame(agg['SK_ID_CURR'].agg(
        'count').reset_index(name='NUM_CREDIT_COUNT'))
    # count number of loans prolonged
    loans_prolonged = agg['CNT_CREDIT_PROLONG'].sum().reset_index(
        name='CREDIT_PROLONG_COUNT').set_index("SK_ID_CURR")
    df_final = df_final.join(loans_prolonged, on='SK_ID_CURR')
    # count percentage of active loans
    active_loans = agg['CREDIT_ACTIVE'].value_counts(
    ).reset_index(name='ACTIVE_LOANS_COUNT')
    active_loans = active_loans[active_loans['CREDIT_ACTIVE'] == 'Active'][[
        'SK_ID_CURR', 'ACTIVE_LOANS_COUNT']].set_index("SK_ID_CURR")
    df_final = df_final.join(active_loans, on='SK_ID_CURR')
    df_final['ACTIVE_LOANS_PERCENT'] = df_final['ACTIVE_LOANS_COUNT'] / \
        df_final['NUM_CREDIT_COUNT']
    df_final.drop(["ACTIVE_LOANS_COUNT"], axis=1, inplace=True)
    df_final['ACTIVE_LOANS_PERCENT'] = df_final['ACTIVE_LOANS_PERCENT'].fillna(
        0)
    # count credit type
    # one hot encode
    ohe = OneHotEncoder(sparse=False)
    ohe_fit = ohe.fit_transform(df[["CREDIT_TYPE"]])
    credit_type = pd.DataFrame(
        ohe_fit, columns=ohe.get_feature_names(["CREDIT_TYPE"]))
    credit_type.insert(loc=0, column='SK_ID_CURR', value=df['SK_ID_CURR'])
    credit_type = credit_type.groupby("SK_ID_CURR").sum()
    df_final = df_final.join(credit_type, on="SK_ID_CURR")
    df_final = df_final.set_index("SK_ID_CURR")
    return df_final


aggCountBureau(bureau)


def aggAvgBureau(df):
    agg = df.groupby('SK_ID_CURR')
    # average of CREDIT_DAY_OVERDUE
    final_df = agg['CREDIT_DAY_OVERDUE'].mean().reset_index(
        name="CREDIT_DAY_OVERDUE_MEAN")
    # average of days between credits of DAYS_CREDIT
    days_credit_between = pd.DataFrame(df['SK_ID_CURR'])
    days_credit_between['diff'] = agg['DAYS_CREDIT'].diff()
    days_credit_between = days_credit_between.groupby(
        "SK_ID_CURR")['diff'].mean().reset_index(name='DAYS_CREDIT_BETWEEN_MEAN')
    days_credit_between.set_index("SK_ID_CURR", inplace=True)
    final_df = final_df.join(days_credit_between, on='SK_ID_CURR')
    final_df = final_df.set_index("SK_ID_CURR")
    return final_df


aggAvgBureau(bureau)


def debtCreditRatio(df):
    # get debt:credit ratio
    df['DEBT_CREDIT_RATIO'] = df['AMT_CREDIT_SUM_DEBT']/df['AMT_CREDIT_SUM']
    df_final = df.groupby('SK_ID_CURR')['DEBT_CREDIT_RATIO'].mean(
    ).reset_index(name='DEBT_CREDIT_RATIO')
    df_final = df_final.set_index("SK_ID_CURR")
    return df_final


debtCreditRatio(bureau)


def bureauFeatures(bureau, bureau_balance):
    dfs = []
    # handling features for bureau_balance
    bureau_balance_rolling_loan = bureauBalanceRollingCreditLoan(
        bureau_balance)
    bureau_df = bureau.copy()
    bureau_df = bureau_df.join(bureau_balance_rolling_loan, on="SK_ID_BUREAU")
    bureau_df["CREDIT_STATUS_EMA_AVG"] = bureau_df['CREDIT_STATUS_EMA_AVG'].fillna(
        0)
    bureau_df = bureau_df.groupby("SK_ID_CURR")["CREDIT_STATUS_EMA_AVG"].mean()
    dfs.append(bureau_df)
    dfs.append(aggCountBureau(bureau))
    dfs.append(aggAvgBureau(bureau))
    dfs.append(debtCreditRatio(bureau))
    final_df = dfs.pop()
    while dfs:
        final_df = final_df.join(dfs.pop(), on='SK_ID_CURR')
    return final_df


bureau_features = bureauFeatures(bureau, bureau_balance)
bureau_features = bureau_features.reset_index()
bureau_features['EVENT_TIMESTAMP'] = datetime.datetime(2022, 8, 3)
bureau_features['CREATED_TIMESTAMP'] = datetime.datetime.now()
bureau_features.to_parquet('../data/bureau_feature_table.parquet')

# PREVIOUS LOAN FEATURES


def aggAvgInstalments(df):
    df_ = df.copy()
    df_['INSTALMENT_MISSED'] = (df_['AMT_INSTALMENT'] > df_[
                                'AMT_PAYMENT']).astype(int)
    df_['AMT_UNPAID'] = df_['AMT_INSTALMENT'] - df_['AMT_PAYMENT']
    df_['PERC_UNPAID'] = df_['AMT_UNPAID']/df_['AMT_INSTALMENT']
    df_ = df_.fillna(0)
    agg = df_.groupby("SK_ID_CURR")
    # percentage of missed payments
    missed_instalments = agg['INSTALMENT_MISSED'].agg(lambda x: x.sum()/x.count()). \
        reset_index().set_index("SK_ID_CURR")
    # percentage of payments difference for each missed payment
    avg_percent_unpaid = agg['PERC_UNPAID'].mean(
    ).reset_index().set_index("SK_ID_CURR")
    # average payments difference for each missed payment
    avg_unpaid = agg['AMT_UNPAID'].mean().reset_index().set_index("SK_ID_CURR")
    final_df = missed_instalments
    final_df = final_df.join(avg_percent_unpaid, on='SK_ID_CURR')
    final_df = final_df.join(avg_unpaid, on="SK_ID_CURR")
    return final_df


installment_payments_features = aggAvgInstalments(installments_payments)


def avgCreditBalance(df):
    return df.groupby('SK_ID_CURR')['AMT_BALANCE'].mean()


avgCreditBalance(credit_card_balance)


def creditCardBalanceRollingBalance(df):
    df_final = df.copy()
    df_final = df_final.sort_values(by="MONTHS_BALANCE")
    df_final = df_final.groupby("SK_ID_CURR")['AMT_BALANCE'].agg(
        lambda x: x.ewm(span=x.shape[0], adjust=False).mean().mean()
    )
    df_final = df_final.reset_index(name="CREDIT_CARD_BALANCE_EMA_AVG")
    df_final = df_final.set_index('SK_ID_CURR')
    return df_final


creditCardBalanceRollingBalance(credit_card_balance)


def creditCardFeatures(credit_card_balance):
    dfs = []
    dfs.append(avgCreditBalance(credit_card_balance))
    dfs.append(creditCardBalanceRollingBalance(credit_card_balance))
    final_df = dfs.pop()
    while dfs:
        final_df = final_df.join(dfs.pop(), on='SK_ID_CURR')
    return final_df


credit_card_balance_features = creditCardFeatures(credit_card_balance)

prev_loan_features = installment_payments_features.join(
    credit_card_balance_features, on="SK_ID_CURR").reset_index()
prev_loan_features = prev_loan_features.fillna(0)
prev_loan_features['EVENT_TIMESTAMP'] = datetime.datetime(2022, 8, 3)
prev_loan_features['EVENT_TIMESTAMP'] = datetime.datetime.now()

prev_loan_features.to_parquet('../data/previous_loan_features_table.parquet')
