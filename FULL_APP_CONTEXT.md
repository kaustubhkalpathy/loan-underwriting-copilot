# Use Case 1: Loan Underwriting Copilot — Complete Context Document

> Paste this into any AI (ChatGPT, Claude, Kimi) to give it full knowledge of the app.
> Last updated: June 26, 2026

---

## WHAT THIS APP DOES

A loan officer fills a form with applicant details → a trained ML model predicts default probability → returns APPROVE / REVIEW / REJECT with SHAP explainability. Business rules catch edge cases the model can't handle.

---

## ARCHITECTURE

```
Loan Officer (Streamlit UI — ~20 sidebar inputs)
    │ build_features() computes all 29 model features from user inputs
    ▼
PRIMARY: AWS Lambda (predict-default-risk, container image, 1024 MB)
    │ Downloads model from S3 on cold start (~10s), then ~8ms per prediction
    ▼
S3 Bucket: loan-copilot-quadra
    - lgbm_booster.txt (1.7 MB trained LightGBM model)
    - preprocessor.pkl (sklearn ColumnTransformer)
    │
    ▼
Returns: risk_score, risk_category, recommended_action, top_risk_factors (SHAP)

FALLBACK (if Lambda fails):
    predict_local() → same model running locally from Datasets/ folder
    Same accuracy, no AWS needed

ALWAYS:
    compute_shap_factors() → local SHAP TreeExplainer
    Shows top 5 features driving this specific prediction

BUSINESS RULES (override model when needed):
    - Income=0 + loan ≤ ₹1L → force minimum REVIEW
    - Income=0 + loan > ₹1L → force REJECT
    - Income>0 + credit/income>10x + EMI>60% → force REJECT
```

---

## ML MODEL DETAILS

- **Dataset:** Home Credit Default Risk (307,511 loan applications, 122 raw columns)
- **Target:** Binary — 8% default (TARGET=1) / 92% repaid (TARGET=0)
- **Algorithm:** LightGBM (500 trees, learning_rate=0.05, num_leaves=31)
- **Performance:** ROC-AUC 0.759 (vs LogReg 0.684, Random Forest 0.733)
- **Split:** Stratified 80/20 (246,008 train / 61,503 test)
- **Preprocessing:** ColumnTransformer → median imputation (numeric) + most_frequent + OneHotEncoder(handle_unknown="ignore") (categorical) → 153 output features
- **Decision Thresholds:** <15% APPROVE, 15-50% REVIEW, >50% REJECT
- **Explainability:** SHAP TreeExplainer (per-prediction, top 5 features)

---

## THE 29 MODEL FEATURES

### 13 Numeric Features (computed from user inputs):
| Feature | How It's Computed |
|---------|-------------------|
| AGE_YEARS | Direct from age input |
| EMPLOYMENT_YEARS | Direct from employment input |
| IS_UNEMPLOYED | 1 if unemployed toggle on, else 0 |
| CREDIT_TO_INCOME_RATIO | loan_amount / annual_income (capped at 15 if income=0) |
| ANNUITY_TO_INCOME_RATIO | monthly_emi / (annual_income/12) (0.80 if income=0) |
| CREDIT_PER_FAMILY_MEMBER | loan_amount / family_size |
| INCOME_PER_FAMILY_MEMBER | annual_income / family_size |
| CHILD_DEPENDENCY_RATIO | num_children / family_size |
| EXT_SOURCE_MEAN | Direct from credit score input (0.35 if unavailable) |
| CREDIT_TERM | Direct from loan term input |
| EXT_SOURCE_1_MISSING | 0 if credit score available, 1 if not |
| OWN_CAR_AGE_MISSING | 1 if no car, 0 if owns car |
| YEARS_BUILD_MISSING | 0 if owns property, 1 if doesn't |

### 16 Categorical Features:
| Feature | Source |
|---------|--------|
| NAME_CONTRACT_TYPE | Loan Type dropdown (Cash loans / Revolving loans) |
| CODE_GENDER | Gender dropdown → M/F |
| FLAG_OWN_CAR | Owns Car → Y/N |
| FLAG_OWN_REALTY | Owns Property → Y/N |
| NAME_TYPE_SUITE | Hardcoded "Unaccompanied" (negligible SHAP) |
| NAME_INCOME_TYPE | Income Source dropdown (Working, Pensioner, Student, etc.) |
| NAME_EDUCATION_TYPE | Education dropdown |
| NAME_FAMILY_STATUS | Family Status dropdown |
| NAME_HOUSING_TYPE | Housing Type dropdown |
| OCCUPATION_TYPE | Occupation dropdown → "Unknown" if "Not applicable / Never worked" |
| WEEKDAY_APPR_PROCESS_START | Hardcoded "MONDAY" (negligible SHAP) |
| ORGANIZATION_TYPE | Employer Type dropdown → "XNA" if "N/A — Unemployed..." |
| FONDKAPREMONT_MODE | Hardcoded "reg oper account" (negligible SHAP) |
| HOUSETYPE_MODE | Hardcoded "block of flats" (negligible SHAP) |
| WALLSMATERIAL_MODE | Hardcoded "Panel" (negligible SHAP) |
| EMERGENCYSTATE_MODE | Hardcoded "No" (negligible SHAP) |

---

## SIDEBAR INPUTS (what the user fills)

### Personal Section:
- Age (18-70, default 35)
- Gender (Male/Female)
- Number of Children (0-10, default 1)
- Total Family Size (1-15, default 3)
- Employment years (0-100, default 5)
- Currently Unemployed toggle (default off)

### Loan Details Section:
- Annual Income (₹0 - ₹50M, default 300,000)
- Loan Type (Cash loans / Revolving loans)
- Loan Amount Requested (₹0 - ₹100M, default 900,000)
- **If income > 0:**
  - Monthly EMI (₹0 - ₹5M, default 4,500)
  - Loan Term months (1-120, default 24)
  - Shows computed: Credit/Income ratio + EMI/Income ratio as caption
- **If income = 0:**
  - Loan Term months (1-120, default 24)
  - EMI hidden (irrelevant)
  - Shows warning: "No income — ratios set to maximum risk"

### Credit Profile Section:
- Credit Score Available toggle (default on)
  - If on: External Credit Score (0.0-1.0, default 0.60)
  - If off: Uses 0.35 median, shows info message
- Owns Car (No/Yes)
- Owns Property (Yes/No)
- Income Source (Working, Commercial associate, Pensioner, State servant, Student, Unemployed, Maternity leave, Businessman)
- Education (Secondary, Higher education, Incomplete higher, Lower secondary, Academic degree)
- Family Status (Married, Single, Civil marriage, Separated, Widow)
- Housing Type (House/apartment, Rented, With parents, Municipal, Office, Co-op)
- Occupation (18 job types + "Not applicable / Never worked")
- Employer Type (17 types from dataset: Business Entity 1/2/3, Self-employed, Government 1/2/3, Military, School, Medicine, Bank, Industries, Construction, Transport, "N/A — Unemployed / Student / Never worked")

---

## INPUT VALIDATION RULES (7 rules)

1. Unemployed + Income Source = "Working" → warning (contradictory)
2. Unemployed + employment > 10 years → info (lost job recently)
3. Employment years > age - 16 → warning (impossible)
4. Employment years > 45 → info (unusual, model trained up to ~45)
5. Pensioner + age < 40 → warning (unusual)
6. Student + age > 45 → warning (unusual)
7. Children > family_size - 1 → BLOCKS submission (impossible)
8. EMI too low for loan/term → info (might be wrong)
9. Credit score = 0.0 → warning (extremely rare)
10. Unemployed + income type not in [Unemployed, Student, Maternity] → warning

---

## BUSINESS RULE OVERRIDES

Applied AFTER model prediction, BEFORE displaying result:

| Condition | Override | Risk Score Set To |
|-----------|----------|-------------------|
| Income=0 + loan > ₹1,00,000 | Force REJECT | max(model_score, 0.85) |
| Income=0 + loan > 0 (any amount) | Force minimum REVIEW | max(model_score, 0.20) |
| Income>0 + credit/income>10x + EMI/income>60% | Force REJECT | max(model_score, 0.55) |

When triggered, shows yellow banner: "🏛️ Business Rule Override: [reason]"

---

## FALLBACK SYSTEM (3 layers)

```
Layer 1: Lambda (primary) → calls AWS
  ↓ fails? (no creds, timeout, Lambda deleted)
Layer 2: predict_local() → same LightGBM model running locally
  ↓ fails? (model files missing)  
Layer 3: Returns 0.5 + explicit error banner "Both models unavailable"
```

- Lambda success → Technical Details shows full JSON response
- Lambda fail + local success → "Using local LightGBM model as fallback"
- Both fail → Red error: "Both Lambda and local model are unavailable"

---

## RESULTS DISPLAY (after clicking ASSESS RISK)

1. **Decision Card** — big colored banner (green APPROVE / orange REVIEW / red REJECT)
2. **Business Rule Banner** — yellow warning if a rule overrode the model
3. **4 Metric Boxes** — Default Probability, Risk Category, Credit Score, Debt-to-Income
4. **Risk Factor Analysis** (left column) — 15 human-readable checks ranked by severity
5. **Applicant Profile** (right column) — summary table of all inputs
6. **SHAP Explainability** (expandable) — top 5 features from TreeExplainer with direction
7. **Technical Details** (expandable) — raw Lambda JSON or error message
8. **Footer** — model info

---

## RISK FACTOR ANALYSIS (15 checks)

Ranked by SHAP importance from the training notebook:
1. External credit score (thresholds: <0.25 high, <0.35 high, <0.5 med, else low)
2. Credit-to-income ratio (>8 high, >5 high, >3.5 med, else low)
3. Employment stability (unemployed=high, <1yr=high, <2yr=med, else low)
4. Age (< 25 med, > 60 med)
5. Monthly payment ratio (>50% high, >35% med, >25% med)
6. Gender pattern (Male = med, dataset shows 10% vs 7% default)
7. Occupation (high-risk list: Laborers, Low-skill, Drivers, Security, Cooking, Cleaning, Waiters)
8. Loan type (Revolving = med)
9. Collateral (no car + no property = med)
10. Housing (Rented or With parents = med)
11. Education (Lower secondary or Incomplete higher = med)
12. Income per family member (<50K high, <80K med)
13. Child dependency (>50% = med)
14. Organization type (Self-employed or N/A = med)
15. Credit score unavailable (= med)

---

## SHAP EXPLAINABILITY

- Uses `shap.TreeExplainer(booster)` on the local model
- Computes SHAP values for all 153 features (after one-hot encoding)
- Shows top 5 by absolute value
- Displays: feature name, SHAP value (+ or -), direction (increases/decreases risk)
- Color coded: red = increases risk, green = decreases risk

---

## AWS RESOURCES

| Resource | Details |
|----------|---------|
| Lambda | predict-default-risk, container image, 1024 MB, 5 min timeout |
| S3 | loan-copilot-quadra (lgbm_booster.txt + preprocessor.pkl) |
| ECR | predict-default-risk (Docker image) |
| Region | us-east-1 |
| Account | 675628601464 |

---

## LOCAL FILES

```
Use_Case_1_Loan_Underwriting/
├── streamlit_app.py              # Main UI (~1000 lines, all logic)
├── lambda/
│   ├── lambda_function.py        # Lambda handler with SHAP
│   ├── Dockerfile                # Python 3.11 Lambda container
│   ├── requirements.txt          # lightgbm, shap, sklearn, pandas, boto3
│   └── DEPLOY_INSTRUCTIONS.md    # CloudShell deployment steps
├── Datasets/
│   ├── application_train.csv     # 307K rows training data
│   ├── HomeCredit_LoanUnderwriting_v1.ipynb  # ML notebook (67 cells)
│   ├── lgbm_booster.txt          # Trained model (1.7 MB)
│   ├── preprocessor.pkl          # Original preprocessor (Lambda, sklearn 1.4.2)
│   └── preprocessor_fitted.pkl   # Re-fitted preprocessor (local, sklearn 1.8.0)
├── fit_preprocessor.py           # One-time script to re-fit preprocessor
├── test_lambda.py                # 6 integration test profiles
├── api-schema.json               # OpenAPI 3.0 spec
├── .streamlit/config.toml        # Dark theme (blue accent #4fc3f7)
├── Requirement_Summary.md        # Formal requirements doc
├── Cost_Estimation.md            # AWS pricing breakdown
├── Architecture_Diagram_Instructions.md
└── PROJECT_CHECKPOINT.md         # Status tracker
```

---

## ALL BUGS FOUND AND FIXED (chronological)

### Round 1 (Code Audit — 15 bugs):
1. Hardcoded INCOME_PER_FAMILY_MEMBER=75000 → computed from real income/family_size
2. Heuristic fallback formula shown as real prediction → replaced with actual local model
3. Stale threshold comment → corrected
4. EXT_SOURCE_1_MISSING always 0 → credit score availability toggle
5. No contradiction validation → 7+ validation rules added
6. ORGANIZATION_TYPE hardcoded → dropdown with exact dataset values
7. YEARS_BUILD_MISSING always 1 → derived from owns_realty
8. Two preprocessor versions (sklearn mismatch) → documented limitation
9. Redundant preprocessing → noted as performance issue
10. Org dropdown values didn't match training → fixed to exact dataset values
11. Division guard redundant → confirmed UI prevents 0
12. Loan ratio mathematical inconsistency → info warning
13. Validation didn't block submission → st.stop() on impossible inputs
14. Risk factors missed new fields → added income/member, child dep, org, credit
15. Silent 0.5 fallback → error banner when both models fail

### Round 2 (UX from manual testing):
16. Min income was 10000 → changed to 0 (allow zero income)
17. No loan amount input → added Loan Amount field, compute ratios internally
18. Credit/Income Ratio as manual input → auto-computed from income + loan amount
19. Monthly Payment / Income ratio → replaced with Monthly EMI input
20. EMI field meaningless when income=0 → hidden, ratios auto-set to max risk
21. Loan term min was 6 → changed to 1 (allow any term)
22. Employment max was 40 → changed to 100 with soft warnings
23. No "Not applicable" in Occupation → added "Not applicable / Never worked"
24. "XNA" in Employer Type unclear → renamed to "N/A — Unemployed / Student / Never worked"
25. Credit score 0.0 allowed silently → added warning
26. Model underestimates risk for zero-income + large loans → business rules added
27. CREDIT_PER_FAMILY_MEMBER was computed from 0 income (always 0) → now uses actual loan_amount input

---

## BUSINESS DECISIONS MADE

1. **Bedrock Agent skipped** — 424 timeout on both AWS accounts. Decision: call Lambda directly.
2. **Two preprocessor files** — Lambda has sklearn 1.4.2, local has 1.8.0. Both produce nearly identical predictions. Full fix requires Lambda rebuild.
3. **Decision thresholds (15%/50%)** — calibrated from dataset distribution. Not arbitrary.
4. **Business rules** — added because model was trained on data where zero-income applicants barely existed. Rules catch what the model can't.
5. **Hardcoded fields** (FONDKAPREMONT, WALLSMATERIAL, etc.) — confirmed negligible SHAP impact. Not worth asking the user about building materials.
6. **SHAP computed locally** — faster than Lambda's SHAP and works even when Lambda fails.

---

## HOW TO RUN

```bash
cd "Use_Case_1_Loan_Underwriting"
pip install streamlit boto3 lightgbm scikit-learn shap numpy pandas
python -m streamlit run streamlit_app.py
```

**Requires:**
- For Lambda: AWS CLI configured with Lambda invoke permission
- For local fallback: `Datasets/lgbm_booster.txt` + `Datasets/preprocessor_fitted.pkl`
- App works without AWS (uses local model automatically)

---

## COST

| Usage | Monthly Cost |
|-------|-------------|
| Dev (100 invocations) | $0.50 (mostly free tier) |
| Branch (30K invocations) | $1.20 |
| At rest | $0 (serverless) |

---

## TEST CASES THAT PASS

| Scenario | Expected | Actual |
|----------|----------|--------|
| Income=0, loan=₹500 | REVIEW + business rule | ✅ REVIEW 20% |
| Income=0, loan=₹2L | REJECT + business rule | ✅ REJECT 85% |
| Perfect applicant (age 45, income 6L, score 0.85, owns everything) | APPROVE | ✅ APPROVE 1.4% |
| Bad applicant (age 22, income 1L, loan 15L, score 0.15, nothing owned) | REJECT | ✅ REJECT 55% |
| Extreme debt (12x income, 95% EMI) | REJECT + business rule | ✅ REJECT 55% |
| Children > family size | Block submission | ✅ Blocked |

---

## KNOWN LIMITATIONS

1. sklearn version mismatch between Lambda (1.4.2) and local (1.8.0) — predictions are very close but not byte-identical
2. Model AUC is 0.759 (not perfect) — it will occasionally give medium-risk scores to clearly bad applicants if they have a good credit bureau score
3. Some hardcoded fields (FONDKAPREMONT, WALLSMATERIAL) have near-zero impact but aren't user-configurable
4. Lambda cold start ~10 seconds on first invocation after idle
5. The "Academic degree" education type strongly protects applicants even with otherwise bad profiles (model learned this pattern from data)
