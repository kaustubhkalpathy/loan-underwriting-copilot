# Deploy Lambda with SHAP — Step by Step

## Prerequisites
- AWS Console access to account 675628601464
- Region: us-east-1

---

## Step 1: Open CloudShell

1. Go to AWS Console (your account)
2. Click the terminal icon `>_` in the top-right toolbar
3. Wait for CloudShell to start (30 seconds)

---

## Step 2: Create the project files

Copy-paste each block below into CloudShell one at a time:

### Create directory:
```bash
mkdir -p ~/lambda-shap && cd ~/lambda-shap
```

### Create requirements.txt:
```bash
cat > requirements.txt << 'EOF'
boto3>=1.28.0
lightgbm>=4.0.0
scikit-learn==1.8.0
numpy>=1.24.0
pandas>=2.0.0
shap>=0.43.0
joblib>=1.3.0
EOF
```

### Create Dockerfile:
```bash
cat > Dockerfile << 'EOF'
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_function.handler"]
EOF
```

### Create lambda_function.py:
```bash
cat > lambda_function.py << 'PYEOF'
import json
import os
import pickle
import tempfile
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
import boto3

S3_BUCKET = "loan-copilot-quadra"
MODEL_KEY = "lgbm_booster.txt"
PREPROCESSOR_KEY = "preprocessor.pkl"

booster = None
preprocessor = None
explainer = None

NUMERIC_FEATURES = [
    "AGE_YEARS", "EMPLOYMENT_YEARS", "IS_UNEMPLOYED",
    "CREDIT_TO_INCOME_RATIO", "ANNUITY_TO_INCOME_RATIO",
    "CREDIT_PER_FAMILY_MEMBER", "INCOME_PER_FAMILY_MEMBER",
    "CHILD_DEPENDENCY_RATIO", "EXT_SOURCE_MEAN", "CREDIT_TERM",
    "EXT_SOURCE_1_MISSING", "OWN_CAR_AGE_MISSING", "YEARS_BUILD_MISSING"
]

CATEGORICAL_FEATURES = [
    "NAME_CONTRACT_TYPE", "CODE_GENDER", "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY", "NAME_TYPE_SUITE", "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS", "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE", "WEEKDAY_APPR_PROCESS_START", "ORGANIZATION_TYPE",
    "FONDKAPREMONT_MODE", "HOUSETYPE_MODE", "WALLSMATERIAL_MODE",
    "EMERGENCYSTATE_MODE"
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_model():
    global booster, preprocessor, explainer
    if booster is not None:
        return
    s3 = boto3.client("s3")
    tmp_dir = tempfile.gettempdir()
    model_path = os.path.join(tmp_dir, "model.txt")
    s3.download_file(S3_BUCKET, MODEL_KEY, model_path)
    booster = lgb.Booster(model_file=model_path)
    prep_path = os.path.join(tmp_dir, "preprocessor.pkl")
    s3.download_file(S3_BUCKET, PREPROCESSOR_KEY, prep_path)
    with open(prep_path, "rb") as f:
        preprocessor = pickle.load(f)
    explainer = shap.TreeExplainer(booster)
    print("Model, preprocessor, and SHAP explainer loaded.")


def parse_request(event):
    properties = event["requestBody"]["content"]["application/json"]["properties"]
    features = {}
    for prop in properties:
        name = prop["name"]
        value = prop["value"]
        if name in NUMERIC_FEATURES:
            try:
                features[name] = float(value)
            except (ValueError, TypeError):
                features[name] = 0.0
        else:
            features[name] = value
    return features


def predict_with_shap(features):
    row = {}
    for f in NUMERIC_FEATURES:
        row[f] = features.get(f, 0.0)
    for f in CATEGORICAL_FEATURES:
        row[f] = features.get(f, "Unknown")

    df = pd.DataFrame([row])
    X_processed = preprocessor.transform(df)
    risk_score = float(booster.predict(X_processed)[0])

    if risk_score < 0.15:
        risk_category = "Low Risk"
        recommended_action = "APPROVE"
    elif risk_score < 0.50:
        risk_category = "Medium Risk"
        recommended_action = "REVIEW"
    else:
        risk_category = "High Risk"
        recommended_action = "REJECT"

    shap_values = explainer.shap_values(X_processed)
    if isinstance(shap_values, list):
        sv = shap_values[1][0]
    elif len(shap_values.shape) == 3:
        sv = shap_values[0, :, 1]
    else:
        sv = shap_values[0]

    try:
        feature_names = preprocessor.get_feature_names_out().tolist()
    except AttributeError:
        feature_names = [f"feature_{i}" for i in range(len(sv))]

    top_indices = np.argsort(np.abs(sv))[-5:][::-1]
    top_factors = []
    for idx in top_indices:
        fname = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
        clean_name = fname.replace("num__", "").replace("cat__", "")
        impact_val = float(sv[idx])
        direction = "increases risk" if impact_val > 0 else "decreases risk"
        top_factors.append({
            "feature": clean_name,
            "shap_value": round(impact_val, 4),
            "direction": direction
        })

    return {
        "risk_score": round(risk_score, 4),
        "risk_category": risk_category,
        "recommended_action": recommended_action,
        "top_risk_factors": top_factors
    }


def handler(event, context):
    try:
        load_model()
        features = parse_request(event)
        result = predict_with_shap(features)
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup", "predict-risk"),
                "apiPath": event.get("apiPath", "/predict"),
                "httpMethod": event.get("httpMethod", "POST"),
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(result)
                    }
                }
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get("actionGroup", "predict-risk"),
                "apiPath": event.get("apiPath", "/predict"),
                "httpMethod": event.get("httpMethod", "POST"),
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({"error": str(e)})
                    }
                }
            }
        }
PYEOF
```

---

## Step 3: Build the Docker image

```bash
docker build -t predict-default-risk .
```

This takes 3-5 minutes (downloads Python packages).

---

## Step 4: Tag and push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 675628601464.dkr.ecr.us-east-1.amazonaws.com

# Tag the image
docker tag predict-default-risk:latest 675628601464.dkr.ecr.us-east-1.amazonaws.com/predict-default-risk:latest

# Push to ECR
docker push 675628601464.dkr.ecr.us-east-1.amazonaws.com/predict-default-risk:latest
```

---

## Step 5: Update the Lambda to use new image

1. Go to Lambda console → predict-default-risk
2. Click "Image" tab (or "Deploy new image")
3. Click "Deploy new image" → select the latest image from ECR
4. Or it might auto-update if using `:latest` tag

---

## Step 6: Update Lambda configuration

1. Go to Configuration → General configuration → Edit
2. Set Memory to **2048 MB** (SHAP needs more memory)
3. Set Timeout to **5 minutes**
4. Save

---

## Step 7: Test

Use the same test event as before. The response should now include `top_risk_factors`:

```json
{
  "risk_score": 0.0957,
  "risk_category": "Low Risk",
  "recommended_action": "APPROVE",
  "top_risk_factors": [
    {"feature": "EXT_SOURCE_MEAN", "shap_value": -0.4521, "direction": "decreases risk"},
    {"feature": "EMPLOYMENT_YEARS", "shap_value": -0.1234, "direction": "decreases risk"},
    ...
  ]
}
```

---

## Troubleshooting

- **Build fails with memory error in CloudShell:** CloudShell has limited resources. Try `docker build --no-cache -t predict-default-risk .`
- **Push fails with "no basic auth credentials":** Re-run the `aws ecr get-login-password` command
- **Lambda timeout on test:** Increase timeout to 5 min. First invocation loads model + builds SHAP explainer.
- **SHAP import error:** Make sure `shap>=0.43.0` is in requirements.txt
