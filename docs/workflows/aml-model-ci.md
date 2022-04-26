# 1. az ml environment scaffold -n risk_env1 -d env_config -w mlops-AML-WS -g mlops-rg
# 2. az ml environment register -d env_config -w mlops-AML-WS -g mlops-rg
# 3. az ml run submit-script --ct aks-mltrain -e riskexpt2 -g mlops-rg -w mlops-AML-WS --subscription-id 371e8e7f-bce0-4db0-9df5-d88805b41101 -d src/env_config/conda_dependencies.yml --path src/env_config --source-directory src train.py

# Working 3: az ml run submit-script --ct aks-mltrain -e riskexpt5 -g mlops-rg -w mlops-AML-WS --subscription-id 371e8e7f-bce0-4db0-9df5-d88805b41101 -c train --source-directory . train.py
