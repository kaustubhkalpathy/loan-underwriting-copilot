# Loan Underwriting Copilot — Complete App Explanation (Final Version)

> This document explains the entire app as it exists today. Use this to understand, demo, or hand off the project.

---

## What It Does (One Line)

A loan officer enters applicant details → ML model predicts default probability → returns APPROVE/REVIEW/REJECT with SHAP explanations, business rule guardrails, and scenario analysis tools.

---

## How It Works (End-to-End Flow)

```
User opens app → sees Landing Page (3 feature cards + architecture + model stats)
    │
    ▼
Fills sidebar (20+ fields OR 5 fields in Quick Mode)
    │
    ▼
Clicks ASSESS RISK
    │
    ├── Validation runs (7+ rules) → blocks if impossible (children > family)
    │
    ▼
build_features() computes all 29 model features from user inputs
    │
    ▼
invoke_lambda() calls AWS Lambda
    ├── Success → uses Lambda's risk_score
    └── Failure → predict_local() runs same model locally
                  └── Failure → returns 0.5 + error banner
    │
    ▼
Business Rules check (override model when needed)
    ├── Income=0 + Loan > ₹1L → REJECT (85%)
    ├── Income=0 + any loan → minimum REVIEW (20%)
    └── Credit/Income > 10x + EMI > 60% → REJECT (55%)
    │
    ▼
Apply thresholds (configurable via sliders, default: <15% APPROVE, 15-50% REVIEW, >50% REJECT)
    │
    ▼
Display Results:
    ├── Decision Card (green/orange/red)
    ├── Borderline Warning (if within 3% of threshold)
    ├── Business Rule Banner (if triggered)
    ├── 4 Metric Boxes (probability, category, score, debt ratio)
    ├── Risk Factor Analysis (15 checks ranked by severity)
    ├── Applicant Profile Summary Table
    ├── SHAP Bar Chart (Plotly, red=risk up, green=risk down)
    │   └── With ELI5 toggle (technical vs friendly names)
    ├── Technical Details (raw Lambda JSON)
    ├── Session History Table + Download CSV
    └── PDF Export button
    │
    ▼
Save to session state (for What-If Analyzer)
```

---

## All Features (Complete List)

### Core Prediction
- LightGBM model (0.759 AUC, 307K training samples, 29 features)
- 3-layer fallback: Lambda → local model → error state
- Business rules override model for edge cases
- Configurable thresholds (APPROVE 5-25%, REJECT 30-70%)

### Input & Validation
- 20+ sidebar inputs covering personal, loan, and credit profile
- Application Reference Number field (appears in PDF + session log)
- 7+ validation rules catching contradictions and impossible inputs
- Blocks submission for critical errors (children > family size)
- Soft warnings for unusual combinations (employment > age-16, pensioner at 25)
- Dynamic ratio computation (credit/income, EMI/income shown as live captions)
- Conditional field display (EMI hidden when income=0)

### Explainability
- SHAP TreeExplainer (local computation, per-prediction)
- Plotly horizontal bar chart (red = increases risk, green = decreases risk)
- "Explain Like I'm 5" toggle → replaces technical names with human-readable labels
- 15 risk factor checks in human language, ranked by SHAP importance
- Confidence explanation ("A 22% probability means roughly 22 out of 100 similar applicants defaulted")

### Decision Support Tools
- What-If Scenario Analyzer: tweak income/loan/score/employment → see decision change
- Quick Assessment: 5 fields only for instant triage (30 seconds)
- Borderline Warning: flags scores within 3% of threshold
- Business Rule transparency: explains WHY a rule overrode the model

### Output & Reporting
- Decision Card (colored: green APPROVE, orange REVIEW, red REJECT)
- PDF Export with: reference number, timestamp, decision, inputs, SHAP factors, disclaimer
- Session History: every assessment logged, viewable as table, downloadable as CSV
- Batch Assessment: upload CSV → predict all rows → download results with summary

### UX Polish
- Dark theme (professional financial UI)
- Custom CSS (Inter font, gradient backgrounds, styled cards)
- Market-open/closed indicator awareness in thresholds
- Tooltips on every input explaining what it means
- Section labels and dividers for clear visual hierarchy

---

## Sidebar Inputs (What the User Fills)

### Application Reference
- Reference No. (optional, defaults to "N/A")

### Personal (6 fields)
- Age (18-70)
- Gender (Male/Female)
- Number of Children (0-10)
- Total Family Size (1-15)
- Employment Years (0-100)
- Currently Unemployed (toggle)

### Loan Details (4-5 fields depending on income)
- Annual Income (₹0 - ₹50M)
- Loan Type (Cash / Revolving)
- Loan Amount (₹0 - ₹100M)
- Monthly EMI (₹0 - ₹5M) — only shown if income > 0
- Loan Term (1-120 months)
- Live captions show: Credit/Income ratio + EMI/Income ratio

### Credit Profile (8 fields)
- Credit Score Available (toggle)
- External Credit Score (0.0 - 1.0) — hidden if toggle off
- Owns Car (No/Yes)
- Owns Property (Yes/No)
- Income Source (8 options)
- Education (5 options)
- Family Status (5 options)
- Housing Type (6 options)
- Occupation (18 types + "Not applicable / Never worked")
- Employer Type (17 exact dataset values + "N/A — Unemployed / Student / Never worked")

### Settings
- Decision Thresholds (APPROVE slider 5-25%, REJECT slider 30-70%)
- Simplified Explanations toggle (ELI5 mode)

---

## The 29 Model Features

### 13 Numeric (computed from inputs):
| Feature | Computation |
|---------|-------------|
| AGE_YEARS | Direct input |
| EMPLOYMENT_YEARS | Direct input |
| IS_UNEMPLOYED | 1 if toggle on, else 0 |
| CREDIT_TO_INCOME_RATIO | loan_amount / annual_income (cap 15 if income=0) |
| ANNUITY_TO_INCOME_RATIO | monthly_emi / (annual_income/12) (0.80 if income=0) |
| CREDIT_PER_FAMILY_MEMBER | loan_amount / family_size |
| INCOME_PER_FAMILY_MEMBER | annual_income / family_size |
| CHILD_DEPENDENCY_RATIO | num_children / family_size |
| EXT_SOURCE_MEAN | Direct input (0.35 if unavailable) |
| CREDIT_TERM | Direct input |
| EXT_SOURCE_1_MISSING | 0 if score available, 1 if not |
| OWN_CAR_AGE_MISSING | 1 if no car, 0 if owns |
| YEARS_BUILD_MISSING | 0 if owns property, 1 if not |

### 16 Categorical (from dropdowns + hardcoded):
- NAME_CONTRACT_TYPE, CODE_GENDER, FLAG_OWN_CAR, FLAG_OWN_REALTY
- NAME_TYPE_SUITE (hardcoded "Unaccompanied")
- NAME_INCOME_TYPE, NAME_EDUCATION_TYPE, NAME_FAMILY_STATUS, NAME_HOUSING_TYPE
- OCCUPATION_TYPE (→ "Unknown" if "Not applicable")
- WEEKDAY_APPR_PROCESS_START (hardcoded "MONDAY")
- ORGANIZATION_TYPE (→ "XNA" if "N/A — Unemployed...")
- FONDKAPREMONT_MODE, HOUSETYPE_MODE, WALLSMATERIAL_MODE, EMERGENCYSTATE_MODE (all hardcoded, negligible SHAP)

---

## Business Rules

| Condition | Override | Risk Score |
|-----------|----------|------------|
| Income=0 + Loan > ₹1,00,000 | Force REJECT | max(model, 0.85) |
| Income=0 + Loan > 0 | Force REVIEW minimum | max(model, 0.20) |
| Income>0 + Credit/Income>10x + EMI>60% | Force REJECT | max(model, 0.55) |

When triggered: yellow banner "🏛️ Business Rule Override: [reason]"

---

## Fallback System

```
Layer 1: Lambda → AWS us-east-1, container image, 1024 MB
  ↓ fails?
Layer 2: predict_local() → same LightGBM model from Datasets/ folder
  ↓ fails?
Layer 3: Returns 0.5 + red error banner "Both models unavailable"
```

---

## Quick Assessment Mode

- 5 fields only: Age, Income, Loan Amount, Credit Score, Employment Years
- All other 24 fields use sensible defaults
- Shows prominent warning: "Treat as indicative only"
- Shows expandable list of all defaults used
- Result appears as colored decision bar
- Suggests "Switch to Full Assessment for detailed review"

---

## What-If Scenario Analyzer

- Requires a Full Assessment first (saves baseline in session state)
- Shows 4 tweakable inputs: Income, Loan Amount, Credit Score, Employment
- Click "Compare Scenario" → runs local model on modified inputs
- Displays side-by-side: Baseline score vs Scenario score with delta
- Highlights if decision flipped (e.g., REJECT → APPROVE)

---

## Batch Assessment

- Accepts CSV upload with applicant data
- Runs predict_local() for each row
- Applies business rules per row
- Shows results table (Row, Risk Score, Category, Decision, key inputs)
- Summary metrics: count of APPROVE/REVIEW/REJECT
- Download Results CSV button
- Progress bar during processing

---

## PDF Export

Generates downloadable PDF with:
- Header: "Loan Risk Assessment Report" + timestamp + reference number
- Decision: action + category + probability
- Business rule (if triggered)
- Applicant summary (5 lines: demographics, financials, assets, employment, employer)
- Top 5 SHAP factors with values and directions
- Footer disclaimer
- Unicode-safe text rendering

---

## Session History

- Every Full Assessment appends a row: ref_no, timestamp, risk_score, category, decision, business_rule, age, income, loan, score
- Displays as interactive dataframe (when >1 assessment)
- Download as CSV button
- Persists within browser session (resets on page refresh)

---

## SHAP Explainability

- Uses local LightGBM model + sklearn preprocessor
- SHAP TreeExplainer computes per-feature contributions
- Top 5 features by |SHAP value| displayed
- Plotly horizontal bar chart: red bars (right) = increases risk, green bars (left) = decreases
- ELI5 toggle maps technical names to friendly labels:
  - EXT_SOURCE_MEAN → "Credit Bureau Score"
  - CREDIT_TO_INCOME_RATIO → "Loan Size vs. Your Income"
  - EMPLOYMENT_YEARS → "Years at Current Job"
  - etc.
- Fallback: text display if Plotly fails

---

## Risk Factor Analysis (15 Checks)

Displayed as colored cards ranked by SHAP importance:

1. External credit score (🔴 <0.25, 🔴 <0.35, 🟡 <0.5, 🟢 ≥0.5)
2. Credit-to-income ratio (🔴 >8, 🔴 >5, 🟡 >3.5, 🟢 ≤3.5)
3. Employment stability (🔴 unemployed, 🔴 <1yr, 🟡 <2yr, 🟢 ≥2yr)
4. Age (🟡 <25, 🟡 >60)
5. Monthly payment ratio (🔴 >50%, 🟡 >35%, 🟡 >25%)
6. Gender pattern (🟡 male — 10% vs 7% default rate)
7. Occupation (🟡 high-risk jobs: Laborers, Drivers, Security, etc.)
8. Loan type (🟡 revolving)
9. Collateral (🟡 no car + no property)
10. Housing (🟡 rented or with parents)
11. Education (🟡 lower secondary or incomplete)
12. Income per family member (🔴 <50K, 🟡 <80K)
13. Child dependency (🟡 >50%)
14. Organization type (🟡 self-employed or N/A)
15. Credit score unavailable (🟡)

---

## Files

```
Use_Case_1_Loan_Underwriting/
├── streamlit_app.py              # Main UI (~1300 lines)
├── lambda/
│   ├── lambda_function.py        # AWS Lambda handler
│   ├── Dockerfile                # Container image
│   ├── requirements.txt          # sklearn==1.8.0
│   └── DEPLOY_INSTRUCTIONS.md    # CloudShell steps
├── Datasets/
│   ├── application_train.csv     # Training data (307K rows)
│   ├── HomeCredit_LoanUnderwriting_v1.ipynb  # ML notebook
│   ├── lgbm_booster.txt          # Trained model
│   ├── preprocessor.pkl          # sklearn ColumnTransformer
│   └── preprocessor_fitted.pkl   # Legacy (keep for backup)
├── fit_preprocessor.py           # Re-fit preprocessor script
├── test_lambda.py                # Integration tests
├── api-schema.json               # OpenAPI spec
├── MODEL_CARD.md                 # Fairness, limitations, governance
├── FULL_APP_CONTEXT.md           # Full context for AI handoff
├── .streamlit/config.toml        # Dark theme
├── Requirement_Summary.md
├── Cost_Estimation.md
├── Architecture_Diagram_Instructions.md
└── PROJECT_CHECKPOINT.md
```

---

## AWS Resources

| Resource | Details |
|----------|---------|
| Lambda | predict-default-risk, container, 1024 MB, 5 min timeout |
| S3 | loan-copilot-quadra (model + preprocessor) |
| ECR | predict-default-risk (Docker image) |
| Region | us-east-1 |
| Account | 675628601464 |

---

## Cost

| Scenario | Monthly |
|----------|---------|
| Development (100 calls) | ~$0.50 |
| Branch office (30K calls) | ~$1.20 |
| At rest | $0 |

---

## How to Run

```bash
cd Use_Case_1_Loan_Underwriting
pip install streamlit boto3 lightgbm scikit-learn shap numpy pandas plotly fpdf2
python -m streamlit run streamlit_app.py
```

Works without AWS (local model fallback). Opens at http://localhost:8501.

---

## Known Limitations

1. Model trained on historical Eastern European data — may not perfectly generalize to Indian/US markets
2. sklearn version should match between Lambda (1.4.2) and local (1.8.0) — fix pending Lambda redeploy
3. Academic degree strongly protects applicants (model bias from training data)
4. Zero-income applicants handled by business rules, not model (insufficient training examples)
5. Lambda cold start ~10 seconds on first invocation after idle

---

## Demo Script (2 minutes)

1. "This is a loan underwriting copilot I built" → show landing page
2. Quick Assessment → age 35, income ₹3L, loan ₹9L, score 0.6, 5 years employed → "REVIEW 34% in 30 seconds"
3. Full Assessment → add details: owns car, State servant, Higher education → "still REVIEW, let's see why"
4. SHAP chart → "Model is worried about credit-to-income ratio" → flip ELI5 toggle → "Now readable by non-technical officers"
5. What-If → "What if income was ₹5L?" → Compare → "Flips to APPROVE 12%. That's scenario analysis."
6. PDF Export → "Officer downloads this, attaches to loan file. Auditable."
7. Batch mode → "Upload 100 applications, get decisions in seconds."
