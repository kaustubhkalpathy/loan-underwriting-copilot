"""
Lambda handler for Loan Underwriting Copilot.
Loads LightGBM model + preprocessor from S3, predicts default risk,
and returns SHAP-based explanations.
"""

import json
import os
import pickle
import tempfile
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
import boto3

# ============================================================
# CONFIGURATION
# ============================================================
S3_BUCKET = "loan-underwriting-copilot"
MODEL_KEY = "lgbm_booster.txt"
PREPROCESSOR_KEY = "preprocessor.pkl"

# ============================================================
# GLOBAL MODEL CACHE (loaded once per cold start)
# ============================================================
booster = None
preprocessor = None
explainer = None


# Feature definitions (must match training)
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
    """Download and load model artifacts from S3."""
    global booster, preprocessor, explainer

    if booster is not None:
        return  # Already loaded

    s3 = boto3.client("s3")
    tmp_dir = tempfile.gettempdir()

    # Download model
    model_path = os.path.join(tmp_dir, "model.txt")
    s3.download_file(S3_BUCKET, MODEL_KEY, model_path)
    booster = lgb.Booster(model_file=model_path)

    # Download preprocessor
    prep_path = os.path.join(tmp_dir, "preprocessor.pkl")
    s3.download_file(S3_BUCKET, PREPROCESSOR_KEY, prep_path)
    with open(prep_path, "rb") as f:
        preprocessor = pickle.load(f)

    # Create SHAP explainer (TreeExplainer is fast for LightGBM)
    explainer = shap.TreeExplainer(booster)
    print("Model, preprocessor, and SHAP explainer loaded successfully.")


def parse_request(event):
    """Parse the Bedrock agent format request into a feature dictionary."""
    properties = event["requestBody"]["content"]["application/json"]["properties"]
    features = {}
    for prop in properties:
        name = prop["name"]
        value = prop["value"]
        # Convert numeric features to float
        if name in NUMERIC_FEATURES:
            try:
                features[name] = float(value)
            except (ValueError, TypeError):
                features[name] = 0.0
        else:
            features[name] = value
    return features


def predict_with_shap(features):
    """Run prediction and compute SHAP explanations."""
    # Build DataFrame with all features (fill missing with defaults)
    row = {}
    for f in NUMERIC_FEATURES:
        row[f] = features.get(f, 0.0)
    for f in CATEGORICAL_FEATURES:
        row[f] = features.get(f, "Unknown")

    df = pd.DataFrame([row])

    # Preprocess
    X_processed = preprocessor.transform(df)

    # Predict
    risk_score = float(booster.predict(X_processed)[0])

    # Determine category
    if risk_score < 0.15:
        risk_category = "Low Risk"
        recommended_action = "APPROVE"
    elif risk_score < 0.50:
        risk_category = "Medium Risk"
        recommended_action = "REVIEW"
    else:
        risk_category = "High Risk"
        recommended_action = "REJECT"

    # Compute SHAP values
    shap_values = explainer.shap_values(X_processed)

    # Handle binary classification (shap_values might be a list of [class0, class1])
    if isinstance(shap_values, list):
        sv = shap_values[1][0]  # class 1 (default) explanations, first sample
    elif len(shap_values.shape) == 3:
        sv = shap_values[0, :, 1]  # (samples, features, classes)
    else:
        sv = shap_values[0]  # single output

    # Get feature names from preprocessor
    try:
        feature_names = preprocessor.get_feature_names_out().tolist()
    except AttributeError:
        feature_names = [f"feature_{i}" for i in range(len(sv))]

    # Get top 5 most impactful features
    top_indices = np.argsort(np.abs(sv))[-5:][::-1]
    top_factors = []
    for idx in top_indices:
        fname = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
        # Clean up feature name (remove prefix like "num__" or "cat__")
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


def lambda_handler(event, context):
    """AWS Lambda handler — Bedrock Agent action group format."""
    try:
        # Load model on first invocation (cold start)
        load_model()

        # Parse features from request
        features = parse_request(event)

        # Predict with SHAP explanations
        result = predict_with_shap(features)

        # Return in Bedrock agent response format
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
        print(f"Error: {str(e)}")
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
