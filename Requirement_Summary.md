# Requirement Summary — Loan Underwriting Copilot

## 1. Project Overview

| Field | Details |
|-------|---------|
| Project Name | Loan Underwriting Copilot |
| Client | Quadra Systems (Internal — AWS Partner) |
| Domain | Financial Services — Credit Risk Assessment |
| Objective | Automate loan underwriting decisions using ML, reducing manual review time and providing explainable risk assessments |
| Region | US East (N. Virginia) — us-east-1 |

## 2. Business Problem

Loan officers manually review applicant profiles to decide approve/review/reject — a time-consuming, inconsistent, and non-transparent process. The system needs to:
- Predict default probability for each applicant in real-time
- Provide a clear recommendation (APPROVE / REVIEW / REJECT)
- Explain the reasoning behind each decision (regulatory requirement)
- Be accessible via a simple web interface

## 3. Functional Requirements

| # | Requirement | Priority |
|---|-------------|----------|
| FR-1 | Accept 29 applicant features (13 numeric + 16 categorical) as input | High |
| FR-2 | Return default probability (0-1), risk category, and recommended action | High |
| FR-3 | Provide per-prediction SHAP explainability (top 5 contributing features) | High |
| FR-4 | Display results in a web-based UI with decision cards and risk factor breakdown | High |
| FR-5 | Support all valid category values from the training dataset | Medium |
| FR-6 | Provide input validation and contradiction warnings | Medium |
| FR-7 | Graceful fallback if Lambda is unavailable (local estimation) | Low |

## 4. Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| NFR-1 | Inference latency (warm) | < 50ms |
| NFR-2 | Inference latency (cold start) | < 15 seconds |
| NFR-3 | Availability | 99.9% (Lambda SLA) |
| NFR-4 | Scalability | Auto-scaling (Lambda handles 0 to 1000 concurrent) |
| NFR-5 | Cost at rest | $0 (serverless — pay per invocation only) |
| NFR-6 | Model accuracy | ROC-AUC >= 0.75 |
| NFR-7 | Explainability | SHAP values per prediction |

## 5. Data Requirements

| Item | Details |
|------|---------|
| Training Dataset | Home Credit Default Risk (307,511 applications, 122 columns) |
| Target Variable | TARGET (1 = default, 0 = repaid) |
| Class Distribution | 92% repaid / 8% defaulted |
| Engineered Features | 29 (13 numeric + 16 categorical) |
| Model Output Features | 153 (after one-hot encoding) |
| Train/Test Split | 80/20 stratified |

## 6. ML Model Requirements

| Item | Details |
|------|---------|
| Algorithm | LightGBM (Gradient Boosted Decision Trees) |
| Hyperparameters | 500 trees, learning_rate=0.05, num_leaves=31 |
| Evaluation Metric | ROC-AUC |
| Achieved Performance | 0.759 ROC-AUC on holdout test set |
| Explainability Method | SHAP TreeExplainer |
| Decision Thresholds | <15% = APPROVE, 15-50% = REVIEW, >50% = REJECT |

## 7. AWS Services Required

| Service | Purpose |
|---------|---------|
| Amazon S3 | Store model artifacts (lgbm_booster.txt, preprocessor.pkl) |
| Amazon ECR | Store Docker container image for Lambda |
| AWS Lambda | Serverless inference endpoint |
| IAM | Roles and permissions (Lambda → S3 read access) |
| CloudWatch | Logging and monitoring (automatic with Lambda) |

## 8. User Interface Requirements

| Item | Details |
|------|---------|
| Framework | Streamlit (Python) |
| Theme | Dark theme (professional financial UI) |
| Input | Sidebar form with 15 user-facing fields (remaining features use defaults) |
| Output | Decision card, 4 metric boxes, risk factor analysis, SHAP breakdown, applicant summary |
| Deployment | Local / EC2 (can be deployed to ECS or App Runner for production) |

## 9. Assumptions and Constraints

- Model is trained on historical data; real-time retraining is not in scope
- Bedrock Agent integration deferred due to 424 timeout (AWS account provisioning issue)
- SHAP computation runs client-side for faster UX; Lambda handles inference only
- No PII is stored or processed — all inputs are applicant features, not identifiable data
- External credit score is assumed to be pre-computed (from CIBIL/Experian equivalent)

## 10. Success Criteria

- End-to-end pipeline working: UI → Lambda → prediction → explanation
- Model ROC-AUC >= 0.75 ✓ (achieved 0.759)
- Inference < 50ms (warm) ✓ (achieved 8ms)
- SHAP explanations per prediction ✓
- All three decision types demonstrable (APPROVE, REVIEW, REJECT) ✓
