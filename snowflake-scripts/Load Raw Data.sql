create or replace file format my_csv_format
  type = csv
  field_delimiter = ','
  skip_header = 1
  null_if = ('NULL', 'null')
  empty_field_as_null = true
  FIELD_OPTIONALLY_ENCLOSED_BY = '0x22';

create stage azure_stage_creditdata
  url='azure://STORAGEACCOUNT.blob.core.windows.net/CONTAINER/FOLDER/'
  credentials=(azure_sas_token='<SAS TOKEN>')
  file_format = my_csv_format;

copy into application_test
    from @AZURE_STAGE_CREDITDATA
    pattern='application_test.csv'
    file_format = my_csv_format;

copy into application_train
    from @AZURE_STAGE_CREDITDATA
    pattern='application_train.csv'
    file_format = my_csv_format;

copy into bureau
    from @AZURE_STAGE_CREDITDATA
    pattern='bureau.csv'
    file_format = my_csv_format;
    
copy into bureau_balance
    from @AZURE_STAGE_CREDITDATA
    pattern='bureau_balance.csv'
    file_format = my_csv_format;

copy into credit_card_balance
    from @AZURE_STAGE_CREDITDATA
    pattern='credit_card_balance.csv'
    file_format = my_csv_format;

copy into installments_payments
    from @AZURE_STAGE_CREDITDATA
    pattern='installments_payments.csv'
    file_format = my_csv_format;
    
copy into "POS_CASH_balance"
    from @AZURE_STAGE_CREDITDATA
    pattern='POS_CASH_balance.csv'
    file_format = my_csv_format;

copy into previous_application
    from @AZURE_STAGE_CREDITDATA
    pattern='previous_application.csv'
    file_format = my_csv_format;