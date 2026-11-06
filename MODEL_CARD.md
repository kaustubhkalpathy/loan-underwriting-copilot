# Model Card — Loan Underwriting Copilot

## Model Details

| Field | Value |
|-------|-------|
| Model Type | LightGBM (Gradient Boosted Decision Trees) |
| Version | 1.0 |
| Framework | LightGBM 4.0+ via Python |
| Task | Binary classification (default vs. repaid) |
| Output | Probability of default (0 to 1) |
| Training Date | June 2026 |
| Last Retrained | Never (initial training only) |

## Training Data

| Field | Value |
|-------|-------|
| Dataset | Home Credit Default Risk (Kaggle) |
| Total Samples | 307,511 loan applications |
| Target Distribution | 92% repaid (0) / 8% default (1) |
| Train/Test Split | 80/20 stratified (246,008 / 61,503) |
| Features Used | 29 (13 numeric + 16 categorical) |
| Features After Encoding | 153 (one-hot encoded) |
| Data Source Period | Historical (pre-2018) |
| Geographic Origin | Eastern European market |

## Performance Metrics

| Metric | Value |
|--------|-------|
| ROC-AUC (test set) | 0.759 |
| Baseline (Logistic Regression) | 0.684 |
| Random Forest comparison | 0.733 |
| Decision Thresholds | <15% APPROVE, 15-50% REVIEW, >50% REJECT |

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| Number of Trees | 500 |
| Learning Rate | 0.05 |
| Max Leaves | 31 |
| Training Objective | binary (cross-entropy) |
| Evaluation Metric | AUC |

## Feature Importance (SHAP Order)

1. EXT_SOURCE_MEAN (external credit bureau score) — strongest predictor
2. CREDIT_TO_INCOME_RATIO
3. EMPLOYMENT_YEARS
4. AGE_YEARS
5. ANNUITY_TO_INCOME_RATIO
6. CODE_GENDER
7. OCCUPATION_TYPE
8. INCOME_PER_FAMILY_MEMBER
9. CREDIT_PER_FAMILY_MEMBER
10. CREDIT_TERM

## Known Limitations

1. **Training data is historical** — economic conditions may have shifted since training. No retraining pipeline exists.
2. **Class imbalance** — only 8% positive examples. Model may underestimate risk for unusual profiles not well-represented in training.
3. **Zero-income applicants** — model was trained on data where nearly all applicants had income. Business rules compensate for this gap.
4. **Academic degree bias** — model learned that academic degree holders rarely default, which strongly protects them even with otherwise bad profiles.
5. **sklearn version** — preprocessor was fitted with sklearn 1.8.0. Lambda environment should match.
6. **Geographic bias** — trained on Eastern European market data. May not generalize perfectly to Indian or US applicants.

## Fairness Considerations

| Group | Default Rate (Training Data) | Note |
|-------|------------------------------|------|
| Male | ~10% | Higher default rate |
| Female | ~7% | Lower default rate |
| Young (<25) | ~10% | Higher than average |
| Middle-aged (35-55) | ~7% | Lower than average |
| Laborers | ~11% | Above average |
| Accountants/Managers | ~5% | Below average |

**Note:** The model uses gender as a feature because it was statistically significant in the training data. In some jurisdictions, using gender for credit decisions is prohibited. Deploying in production would require fairness review per local regulations.

## Intended Use

- **Primary users:** Loan officers at banks/NBFCs
- **Use case:** First-pass risk screening before human review
- **NOT intended for:** Fully automated lending decisions without human oversight

## Decision Flow

```
Model Output (risk_score)
    │
    ├── Business Rules (override when model can't handle edge cases)
    │   ├── Income=0 + Loan > ₹1L → REJECT
    │   ├── Income=0 + any loan → minimum REVIEW
    │   └── Credit/Income > 10x + EMI > 60% → REJECT
    │
    └── Thresholds (configurable)
        ├── < 15% → APPROVE
        ├── 15-50% → REVIEW (human decision required)
        └── > 50% → REJECT
```

## Monitoring & Drift

**Current state:** No automated monitoring. Model performance on new data is unknown.

**Recommended for production:**
- Monthly feature distribution comparison (detect drift)
- Quarterly AUC re-evaluation on recent outcomes
- Alert if any feature drifts > 2 standard deviations from training distribution
- Retrain trigger if AUC drops below 0.70

## Contact

- Built by: Kaustubh Kalpathy
- Organization: Quadra Systems (AWS Partner)
- Internship: June 2026
