# QUADRA SYSTEMS INTERNSHIP — PROJECT CHECKPOINT

## Project

Loan Underwriting Copilot

Pipeline: Home Credit Dataset → Feature Engineering → LightGBM Model → AWS Lambda → Streamlit UI

---

## Best Model Result

Model: LightGBM
ROC-AUC: 0.759
Split: Stratified 80/20 (246,008 train / 61,503 test)
Features: 13 numeric + 16 categorical (29 total)

---

## Completed

- Dataset Loading and Understanding
- Target Variable Analysis (92% / 8% class imbalance)
- Missing Value Analysis (50+ columns with >50% missingness)
- DAYS_EMPLOYED anomaly identified and handled (365243 sentinel)
- Correlation Analysis (raw features)
- Feature Engineering — 13 numeric features + 3 missing-value flags
- Feature Validation — correlations with TARGET confirmed
- Categorical Feature Analysis — 16 columns reviewed
- Preprocessing Pipeline (median imputation + one-hot encoding)
- Train / Test Split (stratified 80/20)
- Baseline Model — Logistic Regression ROC-AUC: 0.684
- Model Comparison — Random Forest: 0.733, LightGBM: 0.759
- Feature Importance Analysis (LightGBM)
- SHAP Explainability — waterfall + summary plots working
- Prediction Tool (predict_default_risk function with recommended_action)
- Model saved as lgbm_booster.txt + preprocessor.pkl
- S3 bucket created (loan-copilot-quadra) with model artifacts + API schema
- Lambda function deployed (container image via ECR)
- Lambda tested successfully — returns risk_score, risk_category, recommended_action
- Bedrock Agent created (Nova Pro) — but 424 timeout on all accounts
- Decision: Skip Bedrock Agent, call Lambda directly from Streamlit
- Streamlit UI — complete, dark theme, calls Lambda directly
- End-to-end working: Streamlit → Lambda → LightGBM → prediction displayed
- Notebook cleaned and structured (HomeCredit_LoanUnderwriting_v1.ipynb, 67 cells)

---

## Architecture (Final)

```
Loan Officer (Streamlit UI)
    |
    v
AWS Lambda: predict-default-risk (container image, 1024 MB)
    |
    v
Loads from S3: lgbm_booster.txt + preprocessor.pkl
    |
    v
LightGBM Model → Prediction
    |
    v
Returns: risk_score, risk_category, recommended_action
```

---

## AWS Resources

- S3 Bucket: loan-copilot-quadra
  - lgbm_booster.txt (1.7 MB)
  - preprocessor.pkl (11.4 KB)
  - api-schema.json
- ECR Repository: predict-default-risk
- Lambda Function: predict-default-risk
  - Container image, 1024 MB memory, 5 min timeout
  - Inference: ~8ms (warm), ~10s (cold start)
  - Max memory used: 280 MB
- Region: us-east-1
- Account: 675628601464

---

## Known Limitations

1. sklearn version mismatch: preprocessor pickled with 1.8.0, Lambda runs 1.4.2 (functional, shows warnings)
2. Bedrock Agent: 424 timeout on both accounts — not used in final architecture
3. SHAP explanations: Working in notebook but NOT returned by Lambda (risk factors in UI are heuristic-based)
4. Some features still use defaults (ORGANIZATION_TYPE, FONDKAPREMONT_MODE, etc.) — low impact on predictions
5. Lambda cold start: ~10 seconds on first invocation after idle period

---

## Local Files

- streamlit_app.py — Main UI application
- Datasets/HomeCredit_LoanUnderwriting_v1.ipynb — ML notebook (67 cells)
- Datasets/lgbm_booster.txt — Trained LightGBM model
- Datasets/preprocessor.pkl — sklearn ColumnTransformer pipeline
- api-schema.json — OpenAPI schema (used by Bedrock, kept for documentation)
- .streamlit/config.toml — Dark theme config
- PROJECT_CHECKPOINT.md — This file

---

## Demo Script

1. Open terminal: `python -m streamlit run streamlit_app.py`
2. Fill sidebar with applicant details
3. Click ASSESS RISK
4. Show: decision card, metrics, risk factors, applicant summary
5. Expand "Technical Details" to show raw Lambda JSON response
6. Show different scenarios: low-risk (approve), medium (review), high-risk (reject)

---

*Last updated: June 18, 2026*
