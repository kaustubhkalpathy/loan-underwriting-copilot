import streamlit as st
import json
import boto3
import os
import numpy as np
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
LAMBDA_FUNCTION_NAME = "predict-default-risk"
AWS_REGION = "us-east-1"
AWS_PROFILE = None  # Uses default AWS CLI credentials
# ============================================================

st.set_page_config(
    page_title="Loan Underwriting Copilot",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Hide default Streamlit header/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Hide anchor links on headings */
.stMarkdown a.header-anchor, 
h1 a, h2 a, h3 a, h4 a,
[data-testid="StyledLinkIconContainer"] {
    display: none !important;
}

/* Page background */
.stApp {
    background: linear-gradient(180deg, #0a0e1a 0%, #111827 100%);
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Hero section */
.hero-container {
    text-align: center;
    padding: 20px 0 10px 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(79, 195, 247, 0.1);
    border: 1px solid rgba(79, 195, 247, 0.3);
    border-radius: 20px;
    padding: 8px 20px;
    font-size: 0.85rem;
    color: #4fc3f7;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 3.8rem !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #4fc3f7 0%, #7c4dff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 !important;
    letter-spacing: -1px;
    line-height: 1.15;
}
.hero-sub {
    font-size: 1.3rem !important;
    color: #8892a4 !important;
    margin-top: 12px;
    margin-bottom: 0;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Feature cards */
.feature-card {
    background: linear-gradient(145deg, #151b2e 0%, #1a2238 100%);
    border: 1px solid #2a3450;
    border-radius: 16px;
    padding: 30px 24px;
    text-align: center;
    min-height: 200px;
    transition: transform 0.2s, box-shadow 0.2s;
}
.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(79, 195, 247, 0.1);
}
.feature-card .icon {
    font-size: 2.8rem;
    margin-bottom: 14px;
}
.feature-card h3 {
    color: #e8eaf6;
    font-size: 1.4rem;
    font-weight: 700;
    margin: 10px 0;
}
.feature-card p {
    color: #7e8aa0;
    font-size: 1rem;
    line-height: 1.7;
    margin: 0;
}

/* Decision cards */
.decision-card {
    border-radius: 20px;
    padding: 36px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.decision-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    opacity: 0.15;
    border-radius: 20px;
}
.decision-approve {
    background: linear-gradient(135deg, #0d3320 0%, #1a5c38 100%);
    border: 1px solid #2e7d32;
    box-shadow: 0 8px 40px rgba(76, 175, 80, 0.2);
}
.decision-review {
    background: linear-gradient(135deg, #3d2000 0%, #5c3500 100%);
    border: 1px solid #f57c00;
    box-shadow: 0 8px 40px rgba(255, 152, 0, 0.2);
}
.decision-reject {
    background: linear-gradient(135deg, #3d0000 0%, #5c1010 100%);
    border: 1px solid #d32f2f;
    box-shadow: 0 8px 40px rgba(244, 67, 54, 0.2);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.decision-icon {
    font-size: 3.5rem;
    margin-bottom: 8px;
}
.decision-text {
    color: white;
    font-size: 2.4rem;
    font-weight: 900;
    margin: 0;
    letter-spacing: 2px;
}
.decision-sub {
    color: rgba(255,255,255,0.75);
    font-size: 1.15rem;
    margin-top: 10px;
    font-weight: 400;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(145deg, #151b2e 0%, #1a2238 100%);
    border: 1px solid #2a3450;
    border-radius: 14px;
    padding: 24px 16px;
    text-align: center;
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 800;
    color: #4fc3f7;
    margin: 6px 0;
}
.metric-card .label {
    color: #6b7a94;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}

/* Risk factors */
.risk-item {
    background: linear-gradient(145deg, #151b2e 0%, #1a2238 100%);
    border-left: 4px solid;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    font-size: 1rem;
    color: #c5cdd8;
    line-height: 1.6;
}
.risk-item.high { border-color: #ef5350; }
.risk-item.med { border-color: #ffa726; }
.risk-item.low { border-color: #66bb6a; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Sidebar styling */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #0a0e1a 0%, #0d1221 100%);
}
.sidebar-header {
    color: #4fc3f7;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 2px;
}
.sidebar-sub {
    color: #5a6577;
    font-size: 0.9rem;
    margin-bottom: 16px;
}
.section-label {
    color: #8892a4;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 8px;
    margin-bottom: 4px;
}

/* Button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1565c0 0%, #4fc3f7 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 1.05rem;
    font-weight: 700;
    padding: 16px;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(79, 195, 247, 0.25);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4fc3f7 0%, #1565c0 100%);
    box-shadow: 0 6px 30px rgba(79, 195, 247, 0.4);
    transform: translateY(-1px);
}

/* Architecture */
.arch-container {
    background: linear-gradient(145deg, #151b2e 0%, #1a2238 100%);
    border: 1px solid #2a3450;
    border-radius: 16px;
    padding: 28px;
    text-align: center;
}
.arch-step {
    display: inline-block;
    background: rgba(79, 195, 247, 0.08);
    border: 1px solid rgba(79, 195, 247, 0.2);
    border-radius: 10px;
    padding: 12px 24px;
    margin: 6px 0;
    color: #b8c5d6;
    font-size: 1rem;
    font-weight: 500;
    width: 80%;
}
.arch-arrow {
    color: #4fc3f7;
    font-size: 1.4rem;
    margin: 4px 0;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid #1e2a3f;
    margin: 32px 0;
}

/* Footer */
.footer-text {
    text-align: center;
    color: #4a5568;
    font-size: 0.8rem;
    padding: 20px 0;
    letter-spacing: 0.5px;
}

/* Summary table */
.summary-table {
    width: 100%;
    border-collapse: collapse;
}
.summary-table tr {
    border-bottom: 1px solid #1e2a3f;
}
.summary-table td {
    padding: 10px 12px;
    color: #b8c5d6;
    font-size: 0.9rem;
}
.summary-table td:first-child {
    color: #6b7a94;
    font-weight: 600;
    width: 40%;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">Quadra Systems • AWS Partner</div>
    <div class="hero-title">🏦 Loan Underwriting Copilot</div>
    <div class="hero-sub">AI-powered credit risk assessment — LightGBM model served via AWS Lambda</div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<p class="sidebar-header">📋 Applicant Details</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-sub">Enter loan application information</p>', unsafe_allow_html=True)

    # Claude Enhancement 1: Application Reference Number
    applicant_ref = st.text_input("Application Reference No.", placeholder="e.g. APP-2024-001",
                                  help="Optional reference number for tracking. Appears in PDF reports and session log.")
    if not applicant_ref.strip():
        applicant_ref = "N/A"

    st.markdown('<p class="section-label">👤 Personal</p>', unsafe_allow_html=True)
    age = st.number_input("Age", min_value=18, max_value=70, value=35,
                          help="Applicant's current age in years. Younger applicants (<25) tend to have slightly higher risk.")
    gender = st.selectbox("Gender", ["Male", "Female"],
                          help="Applicant's gender. Used as a categorical feature by the model.")
    num_children = st.number_input("Number of Children", min_value=0, max_value=10, value=1,
                                   help="How many dependent children does the applicant have? More children = higher financial obligations.")
    family_size = st.number_input("Total Family Size", min_value=1, max_value=15, value=3,
                                  help="Total household members (including applicant). Used to calculate per-capita income and credit burden.")
    employment_years = st.number_input("Employment (years)", min_value=0.0, max_value=100.0, value=5.0, step=0.5,
                                 help="How many years at their most recent job. Even if currently unemployed, enter how long they worked at their last position. Longer = more stable.")
    is_unemployed = st.toggle("Currently Unemployed", value=False,
                              help="Is the applicant jobless RIGHT NOW? This is separate from employment years — someone can have 10 years experience but be currently out of work.")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">💰 Loan Details</p>', unsafe_allow_html=True)
    annual_income = st.number_input("Annual Income (₹ / $)", min_value=0, max_value=50000000, value=300000, step=10000,
                                    help="Applicant's total annual income. Used to calculate per-family-member income and credit burden ratios. Enter 0 if unemployed with no income.")
    contract_type = st.selectbox("Loan Type", ["Cash loans", "Revolving loans"],
                                 help="Cash loan = fixed lump sum with scheduled repayments. Revolving loan = credit line (like a credit card) that can be reused.")
    loan_amount = st.number_input("Loan Amount Requested (₹ / $)", min_value=0, max_value=100000000, value=900000, step=50000,
                                  help="How much money is the applicant asking for? This is the total loan principal.")
    
    if annual_income > 0:
        monthly_emi = st.number_input("Monthly EMI / Payment (₹ / $)", min_value=0, max_value=5000000, value=4500, step=500,
                                      help="The actual monthly repayment amount (EMI). This is on the loan application — includes principal + interest.")
        credit_term = st.number_input("Loan Term (months)", min_value=1, max_value=120, value=24, step=6,
                                help="How many months to repay the loan. Shorter term = higher EMI but less total interest. Longer term = lower EMI but more risk.")
        
        # Compute ratios from real inputs
        monthly_income = annual_income / 12
        annuity_to_income = round(monthly_emi / monthly_income, 4) if monthly_income > 0 else 0.80
        annuity_to_income = min(max(annuity_to_income, 0.01), 0.95)
        credit_to_income = round(loan_amount / annual_income, 2)
        credit_to_income = min(credit_to_income, 20.0)  # Cap at training data range
        
        st.caption(f"📐 Credit/Income: **{credit_to_income:.1f}x** {'⚠️ High' if credit_to_income > 6 else '✓'} · EMI/Income: **{annuity_to_income:.0%}** {'⚠️ Stretched' if annuity_to_income > 0.40 else '✓'}")
    else:
        # Income is 0 — ratios are meaningless, auto-set to maximum risk
        credit_term = st.number_input("Loan Term (months)", min_value=1, max_value=120, value=24, step=6,
                                help="How many months to repay the loan.")
        monthly_emi = 0
        annuity_to_income = 0.80  # Max risk
        credit_to_income = 15.0   # Max risk (training data cap)
        st.warning("⚠️ No income — credit and payment ratios automatically set to maximum risk.")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">📊 Credit Profile</p>', unsafe_allow_html=True)
    credit_score_available = st.toggle("External Credit Score Available", value=True,
                                       help="Is the external credit bureau score (CIBIL/Experian) available for this applicant? ~50% of applicants in the dataset had missing scores.")
    if credit_score_available:
        ext_source_mean = st.number_input("External Credit Score", min_value=0.0, max_value=1.0, value=0.60, step=0.05,
                                    help="Average score from external credit bureaus (like CIBIL/Experian), normalized to 0-1. This is the STRONGEST predictor in the model. 0 = worst, 1 = best. Below 0.35 is high risk.")
        if ext_source_mean == 0.0:
            st.warning("⚠️ Credit score of exactly 0.0 is extremely rare — verify this is correct. The model will assess maximum credit risk.")
    else:
        ext_source_mean = 0.35  # Dataset median for applicants with missing scores
        st.info("ℹ️ No external score — using dataset median (0.35). This increases risk assessment uncertainty.")
    owns_car = st.selectbox("Owns Car", ["No", "Yes"],
                            help="Does the applicant own a car? Indicates asset ownership and financial stability.")
    owns_realty = st.selectbox("Owns Property", ["Yes", "No"],
                              help="Does the applicant own a house/apartment? Property = collateral = lower risk.")
    income_type = st.selectbox("Income Source", ["Working", "Commercial associate", "Pensioner",
                                                "State servant", "Student", "Unemployed",
                                                "Maternity leave", "Businessman"],
                               help="Primary source of income. 'Working' = salaried employee. 'Commercial associate' = business owner. 'Pensioner' = retired. 'State servant' = government job. 'Student' = still in education. 'Businessman' = self-employed business owner.")
    education = st.selectbox("Education", ["Secondary / secondary special", "Higher education",
                                           "Incomplete higher", "Lower secondary", "Academic degree"],
                             help="Highest education level completed. Higher education generally correlates with lower default risk.")
    family_status = st.selectbox("Family Status", ["Married", "Single / not married",
                                                   "Civil marriage", "Separated", "Widow"],
                                 help="Current marital/relationship status. Married applicants tend to have slightly lower risk (shared financial responsibility).")
    housing_type = st.selectbox("Housing Type", ["House / apartment", "Rented apartment",
                                                 "With parents", "Municipal apartment",
                                                 "Office apartment", "Co-op apartment"],
                                help="Where does the applicant live? Owning = more stable. Renting or living with parents = less collateral.")
    occupation_type = st.selectbox("Occupation", ["Laborers", "Core staff", "Sales staff",
                                                  "Managers", "Drivers", "High skill tech staff",
                                                  "Accountants", "Medicine staff", "Cooking staff",
                                                  "Security staff", "Cleaning staff", "Private service staff",
                                                  "Low-skill Laborers", "Secretaries", "Waiters/barmen staff",
                                                  "Realty agents", "HR staff", "IT staff",
                                                  "Not applicable / Never worked"],
                                   help="Applicant's job type. Select 'Not applicable / Never worked' for students or people with no work history.")
    organization_type = st.selectbox("Employer Type",
                                     ["Business Entity Type 3", "Business Entity Type 2",
                                      "Business Entity Type 1", "Self-employed", 
                                      "Government type 3", "Government type 2", "Government type 1",
                                      "Military", "School", "Medicine", "Bank",
                                      "Industry: type 3", "Industry: type 1", "Trade: type 7",
                                      "Construction", "Transport: type 4",
                                      "N/A — Unemployed / Student / Never worked"],
                                     help="Type of organization the applicant works for. Government/military tend to have lower default rates. Self-employed is higher risk. Select 'N/A' if unemployed, student, or never worked.")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # --- Enhancement 9: Threshold Customization ---
    with st.expander("⚙️ Decision Thresholds", expanded=False):
        st.caption("Adjust the thresholds for APPROVE/REVIEW/REJECT decisions")
        approve_threshold = st.slider("APPROVE below (%)", min_value=5, max_value=25, value=15, step=1,
                                      help="Applications with risk below this % get APPROVE") / 100.0
        reject_threshold = st.slider("REJECT above (%)", min_value=30, max_value=70, value=50, step=1,
                                     help="Applications with risk above this % get REJECT") / 100.0
    
    # Kimi Enhancement 2: Simplified explanations toggle
    simplified_mode = st.toggle("Simplified explanations", value=False,
                                help="Replace technical feature names with human-readable labels in SHAP and risk factors.")
    
    assess = st.button("🔍 ASSESS RISK", type="primary", use_container_width=True)

    # Input validation warnings
    if is_unemployed and income_type == "Working":
        st.warning("⚠️ You marked 'Unemployed' but income source is 'Working' — this is contradictory. Model may produce unreliable results.")
    if is_unemployed and employment_years > 10:
        st.info("ℹ️ 'Unemployed' with high employment years means they had long experience but lost their job recently.")
    if employment_years > age - 16:
        st.warning("⚠️ Employment ({e:.0f} yrs) exceeds what's possible for age {a} (max ~{m} yrs). Please verify.".format(e=employment_years, a=age, m=age-16))
    elif employment_years > 45:
        st.info("ℹ️ {e:.0f} years of employment is unusually high — model was trained on values up to ~45 years.".format(e=employment_years))
    if income_type == "Pensioner" and age < 40:
        st.warning("⚠️ Income source 'Pensioner' with age under 40 is unusual — model may not generalize well to this case.")
    if income_type == "Student" and age > 45:
        st.warning("⚠️ Income source 'Student' at age {age} is uncommon in training data — prediction reliability is lower.".format(age=age))
    if num_children > family_size - 1:
        st.error("❌ Children ({c}) cannot exceed family size minus 1 ({f}). Fix before assessing.".format(c=num_children, f=family_size - 1))
    if is_unemployed and income_type not in ["Unemployed", "Student", "Maternity leave"]:
        st.warning("⚠️ Marked as unemployed but income source is '{t}' — consider changing income source to match.".format(t=income_type))
    # Mathematical consistency check — EMI vs loan amount over term
    if annual_income > 0 and credit_term > 0 and monthly_emi > 0:
        expected_monthly = loan_amount / credit_term
        if monthly_emi < expected_monthly * 0.5:
            st.info("ℹ️ EMI (₹{emi:,.0f}) seems low for a ₹{loan:,.0f} loan over {t} months. Minimum principal-only payment would be ₹{exp:,.0f}/month.".format(
                emi=monthly_emi, loan=loan_amount, t=credit_term, exp=expected_monthly))


# ============================================================
# LAMBDA INVOCATION
# ============================================================
def invoke_lambda(features: dict):
    """Call the Lambda function directly and return the risk prediction."""
    try:
        session_kwargs = {"region_name": AWS_REGION}
        if AWS_PROFILE:
            session_kwargs["profile_name"] = AWS_PROFILE
        session = boto3.Session(**session_kwargs)
        client = session.client("lambda")

        properties = [{"name": k, "value": str(v)} for k, v in features.items()]
        payload = {
            "actionGroup": "predict-risk",
            "apiPath": "/predict",
            "httpMethod": "POST",
            "requestBody": {
                "content": {
                    "application/json": {
                        "properties": properties
                    }
                }
            }
        }

        response = client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        response_payload = json.loads(response["Payload"].read())

        if "response" in response_payload:
            body = response_payload["response"]["responseBody"]["application/json"]["body"]
            return json.loads(body)
        elif "body" in response_payload:
            body = response_payload["body"]
            return json.loads(body) if isinstance(body, str) else body
        else:
            return {"error": f"Unexpected response: {response_payload}"}
    except Exception as e:
        return {"error": str(e)}


def build_features(age, gender, employment_years, is_unemployed, contract_type,
                   credit_to_income, annuity_to_income, credit_term,
                   ext_source_mean, owns_car, owns_realty, income_type,
                   education, family_status, housing_type, occupation_type,
                   annual_income, num_children, family_size, organization_type,
                   credit_score_available, loan_amount):
    """Build feature dictionary for Lambda with properly computed derived features."""
    # Compute derived features from actual inputs
    credit_per_family = loan_amount / max(family_size, 1)
    income_per_family = annual_income / max(family_size, 1)
    child_dependency = num_children / max(family_size, 1)

    # EXT_SOURCE_1_MISSING: flag if credit score is not available (Bug #4 fix)
    ext_source_1_missing = 0 if credit_score_available else 1

    # YEARS_BUILD_MISSING: if they own property, building info is likely known (Bug #7 fix)
    years_build_missing = 0 if owns_realty == "Yes" else 1

    return {
        "AGE_YEARS": age,
        "EMPLOYMENT_YEARS": employment_years,
        "IS_UNEMPLOYED": 1 if is_unemployed else 0,
        "CREDIT_TO_INCOME_RATIO": credit_to_income,
        "ANNUITY_TO_INCOME_RATIO": annuity_to_income,
        "CREDIT_PER_FAMILY_MEMBER": int(credit_per_family),
        "INCOME_PER_FAMILY_MEMBER": int(income_per_family),
        "CHILD_DEPENDENCY_RATIO": round(child_dependency, 4),
        "EXT_SOURCE_MEAN": ext_source_mean,
        "CREDIT_TERM": credit_term,
        "EXT_SOURCE_1_MISSING": ext_source_1_missing,
        "OWN_CAR_AGE_MISSING": 1 if owns_car == "No" else 0,
        "YEARS_BUILD_MISSING": years_build_missing,
        "NAME_CONTRACT_TYPE": contract_type,
        "CODE_GENDER": "M" if gender == "Male" else "F",
        "FLAG_OWN_CAR": "Y" if owns_car == "Yes" else "N",
        "FLAG_OWN_REALTY": "Y" if owns_realty == "Yes" else "N",
        "NAME_TYPE_SUITE": "Unaccompanied",
        "NAME_INCOME_TYPE": income_type,
        "NAME_EDUCATION_TYPE": education,
        "NAME_FAMILY_STATUS": family_status,
        "NAME_HOUSING_TYPE": housing_type,
        "OCCUPATION_TYPE": "Unknown" if occupation_type == "Not applicable / Never worked" else occupation_type,
        "WEEKDAY_APPR_PROCESS_START": "MONDAY",
        "ORGANIZATION_TYPE": "XNA" if organization_type == "N/A — Unemployed / Student / Never worked" else organization_type,
        "FONDKAPREMONT_MODE": "reg oper account",
        "HOUSETYPE_MODE": "block of flats",
        "WALLSMATERIAL_MODE": "Panel",
        "EMERGENCYSTATE_MODE": "No",
    }


# ============================================================
# LOCAL MODEL PREDICTION (fallback when Lambda is unavailable)
# ============================================================
def predict_local(features: dict) -> float:
    """Run prediction locally using the LightGBM model — used as fallback when Lambda fails."""
    try:
        booster, preprocessor = load_local_model()

        NUMERIC = ["AGE_YEARS", "EMPLOYMENT_YEARS", "IS_UNEMPLOYED",
                   "CREDIT_TO_INCOME_RATIO", "ANNUITY_TO_INCOME_RATIO",
                   "CREDIT_PER_FAMILY_MEMBER", "INCOME_PER_FAMILY_MEMBER",
                   "CHILD_DEPENDENCY_RATIO", "EXT_SOURCE_MEAN", "CREDIT_TERM",
                   "EXT_SOURCE_1_MISSING", "OWN_CAR_AGE_MISSING", "YEARS_BUILD_MISSING"]
        CATEGORICAL = ["NAME_CONTRACT_TYPE", "CODE_GENDER", "FLAG_OWN_CAR",
                       "FLAG_OWN_REALTY", "NAME_TYPE_SUITE", "NAME_INCOME_TYPE",
                       "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS", "NAME_HOUSING_TYPE",
                       "OCCUPATION_TYPE", "WEEKDAY_APPR_PROCESS_START", "ORGANIZATION_TYPE",
                       "FONDKAPREMONT_MODE", "HOUSETYPE_MODE", "WALLSMATERIAL_MODE",
                       "EMERGENCYSTATE_MODE"]

        row = {}
        for f in NUMERIC:
            row[f] = float(features.get(f, 0))
        for f in CATEGORICAL:
            row[f] = features.get(f, "Unknown")

        df = pd.DataFrame([row])
        X_processed = preprocessor.transform(df)
        return float(booster.predict(X_processed)[0])
    except Exception:
        # Last resort: return 0.5 (unknown risk) rather than a misleading heuristic
        return 0.5


@st.cache_resource
def load_local_model():
    """Load the LightGBM booster and fitted preprocessor for SHAP."""
    import lightgbm as lgb
    import pickle

    base_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(base_dir, "Datasets")

    model_path = os.path.join(datasets_dir, "lgbm_booster.txt")
    prep_path = os.path.join(datasets_dir, "preprocessor.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at: {model_path}")
    if not os.path.exists(prep_path):
        raise FileNotFoundError(f"Preprocessor not found at: {prep_path}")

    booster = lgb.Booster(model_file=model_path)

    with open(prep_path, "rb") as f:
        preprocessor = pickle.load(f)

    return booster, preprocessor


def compute_shap_factors(features: dict):
    """Compute real per-prediction SHAP values using TreeExplainer."""
    try:
        import shap

        booster, preprocessor = load_local_model()

        NUMERIC = ["AGE_YEARS", "EMPLOYMENT_YEARS", "IS_UNEMPLOYED",
                   "CREDIT_TO_INCOME_RATIO", "ANNUITY_TO_INCOME_RATIO",
                   "CREDIT_PER_FAMILY_MEMBER", "INCOME_PER_FAMILY_MEMBER",
                   "CHILD_DEPENDENCY_RATIO", "EXT_SOURCE_MEAN", "CREDIT_TERM",
                   "EXT_SOURCE_1_MISSING", "OWN_CAR_AGE_MISSING", "YEARS_BUILD_MISSING"]
        CATEGORICAL = ["NAME_CONTRACT_TYPE", "CODE_GENDER", "FLAG_OWN_CAR",
                       "FLAG_OWN_REALTY", "NAME_TYPE_SUITE", "NAME_INCOME_TYPE",
                       "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS", "NAME_HOUSING_TYPE",
                       "OCCUPATION_TYPE", "WEEKDAY_APPR_PROCESS_START", "ORGANIZATION_TYPE",
                       "FONDKAPREMONT_MODE", "HOUSETYPE_MODE", "WALLSMATERIAL_MODE",
                       "EMERGENCYSTATE_MODE"]

        row = {}
        for f in NUMERIC:
            row[f] = float(features.get(f, 0))
        for f in CATEGORICAL:
            row[f] = features.get(f, "Unknown")

        df = pd.DataFrame([row])
        X_processed = preprocessor.transform(df)

        explainer = shap.TreeExplainer(booster)
        shap_values = explainer.shap_values(X_processed)

        # Handle output shape
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        elif len(shap_values.shape) == 3:
            sv = shap_values[0, :, 1]
        else:
            sv = shap_values[0]

        # Get feature names
        feature_names = preprocessor.get_feature_names_out().tolist()

        # Top 5 most impactful
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

        return top_factors
    except Exception as e:
        return [{"feature": f"Error: {str(e)}", "shap_value": 0, "direction": "error"}]


# ============================================================
# AI UNDERWRITER ANALYSIS (Bedrock Nova Pro)
# ============================================================
def get_bedrock_analysis(age, annual_income, loan_amount, employment_years, income_type,
                         occupation_type, organization_type, ext_source_mean, owns_realty,
                         owns_car, family_size, num_children, education, housing_type,
                         risk_score, category, action, shap_factors, business_rule_triggered):
    """Call Bedrock Nova Pro for AI underwriter narrative."""
    try:
        shap_text = ""
        if shap_factors and shap_factors[0]["direction"] != "error":
            for f in shap_factors[:5]:
                shap_text += f"  - {f['feature']}: {f['shap_value']:+.4f} ({f['direction']})\n"
        
        prompt = f"""You are a senior loan underwriter at an Indian bank. A machine learning model has assessed a loan application and returned the following:

Risk Score: {risk_score:.1%}
Risk Category: {category}
Model Decision: {action}
Business Rule Override: {business_rule_triggered if business_rule_triggered else 'None'}

Top risk drivers (SHAP):
{shap_text}
Applicant Profile:
- Age: {age} years
- Annual Income: ₹{annual_income:,}
- Loan Amount Requested: ₹{loan_amount:,}
- Employment: {employment_years} years ({income_type})
- Occupation: {occupation_type}
- Employer Type: {organization_type}
- Credit Score: {ext_source_mean}
- Owns Property: {owns_realty}, Owns Car: {owns_car}
- Family: {family_size} members, {num_children} children
- Education: {education}
- Housing: {housing_type}

Provide a concise underwriter narrative (4-6 sentences) covering:
1. Whether you agree with the model's decision and why
2. Any mitigating factors the model may have missed
3. Key risks specific to this applicant's profile
4. Your final recommendation (Approve / Review with conditions / Reject)

Be specific to Indian banking context. Do not repeat the numbers mechanically — reason about what they mean."""

        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        response = client.converse(
            modelId="amazon.nova-pro-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 400, "temperature": 0.3}
        )
        return response["output"]["message"]["content"][0]["text"]
    except Exception:
        return None


# ============================================================
# FEATURE NAME MAPPING (Kimi Enhancement 2: simplified labels)
# ============================================================
FRIENDLY_FEATURE_NAMES = {
    "EXT_SOURCE_MEAN": "Credit Bureau Score",
    "CREDIT_TO_INCOME_RATIO": "Loan-to-Income Ratio",
    "ANNUITY_TO_INCOME_RATIO": "Monthly Payment Burden",
    "EMPLOYMENT_YEARS": "Years at Current Job",
    "IS_UNEMPLOYED": "Currently Unemployed",
    "CREDIT_PER_FAMILY_MEMBER": "Loan Per Family Member",
    "INCOME_PER_FAMILY_MEMBER": "Income Per Family Member",
    "CHILD_DEPENDENCY_RATIO": "Dependents Ratio",
    "OWN_CAR_AGE_MISSING": "No Car Owned",
    "YEARS_BUILD_MISSING": "No Property Records",
    "EXT_SOURCE_1_MISSING": "Credit Score Unavailable",
    "AGE_YEARS": "Applicant Age",
    "CREDIT_TERM": "Loan Duration (months)",
    "CODE_GENDER_M": "Gender: Male",
    "CODE_GENDER_F": "Gender: Female",
    "FLAG_OWN_CAR_Y": "Owns a Car",
    "FLAG_OWN_CAR_N": "No Car",
    "FLAG_OWN_REALTY_Y": "Owns Property",
    "FLAG_OWN_REALTY_N": "No Property",
    "NAME_EDUCATION_TYPE_Higher education": "Education: Degree Holder",
    "NAME_EDUCATION_TYPE_Secondary": "Education: Secondary School",
    "NAME_EDUCATION_TYPE_Lower secondary": "Education: Below Secondary",
    "NAME_EDUCATION_TYPE_Academic degree": "Education: Advanced Degree",
    "NAME_EDUCATION_TYPE_Incomplete higher": "Education: Incomplete College",
    "NAME_INCOME_TYPE_Working": "Income: Salaried Employee",
    "NAME_INCOME_TYPE_Pensioner": "Income: Pensioner",
    "NAME_INCOME_TYPE_State servant": "Income: Government Employee",
    "NAME_INCOME_TYPE_Student": "Income: Student",
    "NAME_INCOME_TYPE_Unemployed": "Income: Unemployed",
    "NAME_INCOME_TYPE_Commercial associate": "Income: Business Owner",
    "NAME_FAMILY_STATUS_Married": "Married",
    "NAME_FAMILY_STATUS_Single": "Single",
    "NAME_HOUSING_TYPE_House": "Housing: Own Home",
    "NAME_HOUSING_TYPE_Rented": "Housing: Rented",
    "NAME_HOUSING_TYPE_With parents": "Housing: Living with Parents",
    "OCCUPATION_TYPE_Laborers": "Occupation: Manual Labor",
    "OCCUPATION_TYPE_Low-skill": "Occupation: Low-Skill Work",
    "ORGANIZATION_TYPE_Self-employed": "Employer: Self-Employed",
    "ORGANIZATION_TYPE_Government": "Employer: Government",
    "ORGANIZATION_TYPE_XNA": "Employer: Unknown/None",
    "NAME_CONTRACT_TYPE_Cash loans": "Loan Type: Cash Loan",
    "NAME_CONTRACT_TYPE_Revolving loans": "Loan Type: Revolving Credit",
    "WEEKDAY_APPR_PROCESS_START_MONDAY": "Application Day: Monday",
}

def get_display_name(feature_name: str, simplified: bool) -> str:
    """Return friendly name if simplified mode is on, otherwise original."""
    if not simplified:
        return feature_name
    # Handle one-hot encoded names like "NAME_EDUCATION_TYPE_Higher education"
    for key, friendly in FRIENDLY_FEATURE_NAMES.items():
        if key in feature_name:
            return friendly
    # Clean up remaining one-hot names
    clean = feature_name.replace("num__", "").replace("cat__", "")
    clean = clean.replace("NAME_", "").replace("_TYPE", "").replace("_", " ").title()
    return clean


# ============================================================
# MAIN CONTENT
# ============================================================
if assess:
    # Block submission if validation fails critically
    if num_children > family_size - 1:
        st.error("⛔ Cannot assess: Number of children exceeds family size. Please fix the values in the sidebar.")
        st.stop()

    with st.spinner("⏳ Connecting to prediction service... (first request may take ~10s)"):
        features = build_features(
            age, gender, employment_years, is_unemployed, contract_type,
            credit_to_income, annuity_to_income, credit_term,
            ext_source_mean, owns_car, owns_realty, income_type,
            education, family_status, housing_type, occupation_type,
            annual_income, num_children, family_size, organization_type,
            credit_score_available, loan_amount
        )
        result = invoke_lambda(features)

    # Parse result (Bug #2 fix: use local model as fallback, not a heuristic formula)
    if "error" in result:
        risk_score = predict_local(features)
        lambda_error = result["error"]
        if risk_score == 0.5:
            local_model_failed = True
        else:
            local_model_failed = False
    else:
        risk_score = result.get("risk_score", 0.5)
        lambda_error = None
        local_model_failed = False
    
    # Save everything to session state so results persist across reruns (ELI5 toggle fix)
    st.session_state["last_risk_score"] = risk_score
    st.session_state["last_features"] = features
    st.session_state["last_result"] = result
    st.session_state["last_local_model_failed"] = local_model_failed
    st.session_state["assessment_done"] = True

# Show results if an assessment has been done (persists across toggle/slider changes)
if st.session_state.get("assessment_done", False):
    risk_score = st.session_state["last_risk_score"]
    features = st.session_state["last_features"]
    result = st.session_state["last_result"]
    local_model_failed = st.session_state["last_local_model_failed"]

    # Determine action and category from risk_score
    # Both Lambda and Streamlit use the same thresholds: <15% APPROVE, 15-50% REVIEW, >50% REJECT
    if local_model_failed:
        st.error("⚠️ **Both Lambda and local model are unavailable.** The score shown below is NOT a real prediction. Please check AWS credentials or ensure model files exist in Datasets/ folder.")

    # --- Business Rule Overrides ---
    # These catch scenarios the model can't handle well due to training data limitations.
    business_rule_triggered = None
    
    if annual_income == 0 and loan_amount > 0:
        if loan_amount > 100000:
            # Above 1 lakh with no income — auto-reject
            business_rule_triggered = "No income with loan above ₹1,00,000 — cannot service this loan without income source"
            risk_score = max(risk_score, 0.85)
        else:
            # Any loan with no income — minimum REVIEW (never approve)
            business_rule_triggered = "No income — any loan requires manual review regardless of model score"
            risk_score = max(risk_score, 0.20)  # Force above APPROVE threshold (0.15)
    elif annual_income > 0 and credit_to_income > 10 and annuity_to_income > 0.60:
        business_rule_triggered = "Extreme debt burden (>10x income) with very high EMI ratio (>60%) — elevated to reject"
        risk_score = max(risk_score, 0.55)

    if risk_score < approve_threshold:
        action, category = "APPROVE", "Low Risk"
    elif risk_score < reject_threshold:
        action, category = "REVIEW", "Medium Risk"
    else:
        action, category = "REJECT", "High Risk"

    card_class = "decision-approve" if action == "APPROVE" else "decision-review" if action == "REVIEW" else "decision-reject"
    icon = "✅" if action == "APPROVE" else "⚠️" if action == "REVIEW" else "❌"

    # --- Decision Card ---
    st.markdown(f"""
    <div class="decision-card {card_class}">
        <div class="decision-icon">{icon}</div>
        <p class="decision-text">{action}</p>
        <p class="decision-sub">{category} — Default Probability: {risk_score:.1%}</p>
    </div>
    """, unsafe_allow_html=True)

    # Show business rule override notice
    if business_rule_triggered:
        st.warning(f"🏛️ **Business Rule Override:** {business_rule_triggered}")

    # Enhancement 4: Borderline warning
    if abs(risk_score - approve_threshold) < 0.03 or abs(risk_score - reject_threshold) < 0.03:
        st.warning("⚠️ **Borderline Decision:** Score is very close to the threshold. Manual review strongly recommended.")

    st.markdown("")
    st.markdown("")

    # --- Metrics Row ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        color = "#66bb6a" if risk_score < 0.3 else "#ffa726" if risk_score < 0.6 else "#ef5350"
        st.markdown(f'''<div class="metric-card">
            <p class="label">Default Probability</p>
            <p class="value" style="color:{color}">{risk_score:.1%}</p>
        </div>''', unsafe_allow_html=True)
    with c2:
        cat_color = "#66bb6a" if action == "APPROVE" else "#ffa726" if action == "REVIEW" else "#ef5350"
        st.markdown(f'''<div class="metric-card">
            <p class="label">Risk Category</p>
            <p class="value" style="color:{cat_color}">{category}</p>
        </div>''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''<div class="metric-card">
            <p class="label">Credit Score</p>
            <p class="value">{ext_source_mean:.2f}</p>
        </div>''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''<div class="metric-card">
            <p class="label">Debt-to-Income</p>
            <p class="value">{credit_to_income:.1f}x</p>
        </div>''', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Compute SHAP factors early (needed by AI Underwriter + SHAP chart + session log)
    shap_factors = compute_shap_factors(features)

    # --- 🤖 AI Underwriter Analysis ---
    st.markdown("#### 🤖 AI Underwriter Analysis")
    # Only call Bedrock on new assessment (not on toggle/slider reruns)
    if assess:
        with st.spinner("Consulting AI Underwriter..."):
            ai_analysis = get_bedrock_analysis(
                age, annual_income, loan_amount, employment_years, income_type,
                occupation_type, organization_type, ext_source_mean, owns_realty,
                owns_car, family_size, num_children, education, housing_type,
                risk_score, category, action, shap_factors, business_rule_triggered
            )
        st.session_state["last_ai_analysis"] = ai_analysis
    
    ai_analysis = st.session_state.get("last_ai_analysis")
    if ai_analysis:
        st.info(ai_analysis)
    else:
        st.warning("AI Underwriter unavailable — assess using risk factors below.")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # --- Risk Factors & Profile ---
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### 🔍 Risk Factor Analysis")
        st.markdown('<p style="color:#6b7a94; font-size:0.8rem; margin-bottom:16px;">Factors ranked by model importance (based on SHAP analysis of 307K training samples)</p>', unsafe_allow_html=True)

        # Build risk factors list with severity and SHAP-based importance rank
        # SHAP importance order from notebook: EXT_SOURCE_MEAN > CREDIT_TO_INCOME > EMPLOYMENT > AGE > ANNUITY_TO_INCOME > GENDER > OCCUPATION
        risk_factors = []

        # 1. External credit score (SHAP rank #1 — strongest predictor)
        if ext_source_mean < 0.25:
            risk_factors.append(("high", f"🔴 External credit score very low ({ext_source_mean:.2f}) — strongest default predictor in model", 1))
        elif ext_source_mean < 0.35:
            risk_factors.append(("high", f"🔴 External credit score significantly below average ({ext_source_mean:.2f})", 1))
        elif ext_source_mean < 0.5:
            risk_factors.append(("med", f"🟡 External credit score below average ({ext_source_mean:.2f}) — moderate concern", 1))
        else:
            risk_factors.append(("low", f"🟢 External credit score healthy ({ext_source_mean:.2f})", 1))

        # 2. Credit-to-income ratio (SHAP rank #2)
        if credit_to_income > 8:
            risk_factors.append(("high", f"🔴 Extreme debt burden — loan is {credit_to_income:.1f}x annual income", 2))
        elif credit_to_income > 5:
            risk_factors.append(("high", f"🔴 High debt burden — loan is {credit_to_income:.1f}x annual income", 2))
        elif credit_to_income > 3.5:
            risk_factors.append(("med", f"🟡 Elevated debt — loan is {credit_to_income:.1f}x annual income", 2))
        else:
            risk_factors.append(("low", f"🟢 Manageable debt — loan is {credit_to_income:.1f}x annual income", 2))

        # 3. Employment (SHAP rank #3)
        if is_unemployed:
            risk_factors.append(("high", "🔴 Currently unemployed — significant repayment risk", 3))
        elif employment_years < 1:
            risk_factors.append(("high", "🔴 Less than 1 year employment — very limited stability", 3))
        elif employment_years < 2:
            risk_factors.append(("med", f"🟡 Employment under 2 years ({employment_years:.1f}yr) — limited stability", 3))
        else:
            risk_factors.append(("low", f"🟢 Stable employment — {employment_years:.0f} years at current job", 3))

        # 4. Age (SHAP rank #4)
        if age < 25:
            risk_factors.append(("med", f"🟡 Young applicant ({age}) — limited credit history", 4))
        elif age > 60:
            risk_factors.append(("med", f"🟡 Older applicant ({age}) — shorter repayment horizon", 4))

        # 5. Monthly payment ratio (SHAP rank #5)
        if annuity_to_income > 0.5:
            risk_factors.append(("high", f"🔴 Monthly payment consumes {annuity_to_income:.0%} of income — unsustainable", 5))
        elif annuity_to_income > 0.35:
            risk_factors.append(("med", f"🟡 Monthly payment is {annuity_to_income:.0%} of income — heavily stretched", 5))
        elif annuity_to_income > 0.25:
            risk_factors.append(("med", f"🟡 Monthly payment is {annuity_to_income:.0%} of income — moderate strain", 5))

        # 6. Gender (SHAP rank #6 — statistical pattern in dataset)
        if gender == "Male":
            risk_factors.append(("med", "🟡 Male applicants have ~10% default rate vs ~7% for female (dataset pattern)", 6))

        # 7. Occupation (SHAP rank #7)
        high_risk_jobs = ["Laborers", "Low-skill Laborers", "Drivers", "Security staff", "Cooking staff", "Cleaning staff", "Waiters/barmen staff"]
        if occupation_type in high_risk_jobs:
            risk_factors.append(("med", f"🟡 Occupation \"{occupation_type}\" has above-average default rate", 7))

        # 8. Loan type
        if contract_type == "Revolving loans":
            risk_factors.append(("med", "🟡 Revolving loan — higher default rate than fixed cash loans", 8))

        # 9. Collateral
        if owns_realty == "No" and owns_car == "No":
            risk_factors.append(("med", "🟡 No collateral assets (no car, no property)", 9))

        # 10. Housing
        if housing_type in ["Rented apartment", "With parents"]:
            risk_factors.append(("med", f"🟡 Housing: {housing_type} — less financial stability", 10))

        # 11. Education
        if education in ["Lower secondary", "Incomplete higher"]:
            risk_factors.append(("med", f"🟡 Education \"{education}\" correlates with slightly higher risk", 11))

        # 12. Income per family member
        income_per_fam = annual_income / max(family_size, 1)
        if income_per_fam < 50000:
            risk_factors.append(("high", f"🔴 Very low per-capita income ({income_per_fam:,.0f}/member) — limited repayment capacity", 12))
        elif income_per_fam < 80000:
            risk_factors.append(("med", f"🟡 Below-average per-capita income ({income_per_fam:,.0f}/member)", 12))

        # 13. Child dependency
        child_dep = num_children / max(family_size, 1)
        if child_dep > 0.5:
            risk_factors.append(("med", f"🟡 High child dependency ratio ({child_dep:.0%}) — more financial strain", 13))

        # 14. Organization type
        high_risk_orgs = ["Self-employed", "N/A — Unemployed / Student / Never worked"]
        if organization_type in high_risk_orgs:
            risk_factors.append(("med", f"🟡 Employer type \"{organization_type}\" has above-average default rate", 14))

        # 15. Credit score unavailable
        if not credit_score_available:
            risk_factors.append(("med", "🟡 No external credit bureau score available — higher prediction uncertainty", 15))

        # Display sorted by severity (high first, then med, then low)
        severity_order = {"high": 0, "med": 1, "low": 2}
        risk_factors.sort(key=lambda x: (severity_order[x[0]], x[2]))

        for severity, text, _ in risk_factors:
            st.markdown(f'<div class="risk-item {severity}">{text}</div>', unsafe_allow_html=True)

        # Confidence explanation
        st.markdown(f'''<div style="background: rgba(79,195,247,0.05); border: 1px solid rgba(79,195,247,0.15); 
            border-radius: 10px; padding: 14px; margin-top: 16px; font-size: 0.82rem; color: #7e8aa0;">
            <strong style="color:#4fc3f7;">ℹ️ How to interpret:</strong> A {risk_score:.1%} default probability means that among 
            similar applicants in our 307K training dataset, roughly {int(risk_score*100)} out of 100 went on to default. 
            The model (LightGBM, AUC 0.759) captures complex interactions between all 29 features simultaneously.
        </div>''', unsafe_allow_html=True)

    with right:
        st.markdown("#### 👤 Applicant Profile")
        st.markdown("")
        st.markdown(f"""
<table class="summary-table">
<tr><td>Age</td><td>{age} years</td></tr>
<tr><td>Gender</td><td>{gender}</td></tr>
<tr><td>Children</td><td>{num_children}</td></tr>
<tr><td>Family Size</td><td>{family_size}</td></tr>
<tr><td>Employment</td><td>{employment_years:.1f} years</td></tr>
<tr><td>Unemployed</td><td>{"Yes ⚠️" if is_unemployed else "No"}</td></tr>
<tr><td>Annual Income</td><td>{annual_income:,.0f}</td></tr>
<tr><td>Loan Type</td><td>{contract_type}</td></tr>
<tr><td>Loan Term</td><td>{credit_term} months</td></tr>
<tr><td>Income Source</td><td>{income_type}</td></tr>
<tr><td>Occupation</td><td>{occupation_type}</td></tr>
<tr><td>Employer Type</td><td>{organization_type}</td></tr>
<tr><td>Education</td><td>{education}</td></tr>
<tr><td>Family Status</td><td>{family_status}</td></tr>
<tr><td>Housing</td><td>{housing_type}</td></tr>
<tr><td>Owns Car</td><td>{owns_car}</td></tr>
<tr><td>Owns Property</td><td>{owns_realty}</td></tr>
<tr><td>Credit Score</td><td>{ext_source_mean:.2f}{" (unavailable)" if not credit_score_available else ""}</td></tr>
</table>
        """, unsafe_allow_html=True)

    # --- Lambda Details Expander ---
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # SHAP explanation section
    with st.expander("🧠 SHAP Explainability — Model's Actual Reasoning", expanded=True):
        # shap_factors already computed above (before AI Underwriter)
        # Save top SHAP features for What-If Analyzer
        if shap_factors and shap_factors[0]["direction"] != "error":
            st.session_state["top_shap_features"] = [f["feature"] for f in shap_factors]
            st.markdown("**Top 5 features driving this prediction** (computed via SHAP TreeExplainer):")
            st.markdown("")
            
            # Enhancement 5: SHAP horizontal bar chart
            try:
                import plotly.graph_objects as go
                
                shap_names = [get_display_name(f["feature"], simplified_mode) for f in shap_factors]
                shap_values = [f["shap_value"] for f in shap_factors]
                shap_colors = ["#ef5350" if v > 0 else "#66bb6a" for v in shap_values]
                
                fig = go.Figure(go.Bar(
                    x=shap_values,
                    y=shap_names,
                    orientation='h',
                    marker_color=shap_colors,
                    text=[f"{v:+.4f}" for v in shap_values],
                    textposition="outside",
                    textfont=dict(color="#FAFAFA"),
                ))
                fig.add_vline(x=0, line_color="#444", line_dash="dash", opacity=0.5)
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0E1117",
                    plot_bgcolor="#0E1117",
                    font=dict(color="#FAFAFA"),
                    height=250,
                    margin=dict(l=10, r=80, t=10, b=10),
                    xaxis_title="SHAP Value (→ increases risk, ← decreases risk)",
                    showlegend=False,
                )
                fig.update_xaxes(gridcolor="#1A1F2E")
                fig.update_yaxes(gridcolor="#1A1F2E")
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                # Fallback to text display if plotly fails
                for factor in shap_factors:
                    if factor["direction"] == "increases risk":
                        ficon = "📈"
                        color = "#ef5350"
                    else:
                        ficon = "📉"
                        color = "#66bb6a"
                    st.markdown(
                        f'<div style="background:#151b2e; border-left:4px solid {color}; border-radius:8px; '
                        f'padding:10px 14px; margin-bottom:8px; color:#c5cdd8; font-size:0.9rem;">'
                        f'{ficon} <strong>{factor["feature"]}</strong> — SHAP: {factor["shap_value"]:+.4f} '
                        f'<span style="color:{color}">({factor["direction"]})</span></div>',
                        unsafe_allow_html=True
                    )
            
            st.markdown('<p style="color:#6b7a94; font-size:0.75rem; margin-top:12px;">'
                        'SHAP (SHapley Additive exPlanations) quantifies each feature\'s contribution to the prediction. '
                        'Positive values push toward default, negative values push toward repayment.</p>',
                        unsafe_allow_html=True)
        else:
            error_msg = shap_factors[0]["feature"] if shap_factors else "Unknown error"
            st.error(f"SHAP error: {error_msg}")

    # --- PDF Export (moved here — below SHAP, above Technical Details) ---
    if st.button("📄 Download Report as PDF", use_container_width=True, key="pdf_main_btn"):
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(0, 100, 180)
            def _safe(text):
                return str(text).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 12, "Loan Risk Assessment Report", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Reference: {applicant_ref}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 8, f"Decision: {action} ({category})", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 6, f"Default Probability: {risk_score:.1%}", new_x="LMARGIN", new_y="NEXT")
            if business_rule_triggered:
                pdf.cell(0, 6, f"Business Rule: {business_rule_triggered}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Applicant Summary", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for line in [f"Age: {age} | Gender: {gender} | Family Size: {family_size}", f"Income: {annual_income:,.0f} | Loan: {loan_amount:,.0f} | Term: {credit_term} months", f"Employment: {employment_years:.1f} years | Unemployed: {'Yes' if is_unemployed else 'No'}", f"Credit Score: {ext_source_mean:.2f} | Owns Property: {owns_realty} | Owns Car: {owns_car}", f"Occupation: {_safe(occupation_type)} | Employer: {_safe(organization_type)}"]:
                pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            if shap_factors and shap_factors[0]["direction"] != "error":
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Top Risk Factors (SHAP)", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                for f in shap_factors:
                    pdf.cell(0, 5, f"  {f['feature']}: {f['shap_value']:+.4f} ({f['direction']})", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(8)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 4, "Internal use only. Model: LightGBM (AUC 0.759). Quadra Systems 2026.")
            st.download_button("⬇️ Download PDF", data=bytes(pdf.output()),
                             file_name=f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                             mime="application/pdf", key="pdf_download")
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
    st.caption("Downloads report for the current applicant above.")

    with st.expander("⚙️ Technical Details — Lambda Response"):
        if "error" in result:
            st.error(f"Lambda error: {result['error']}")
            st.info("Using local LightGBM model as fallback (same model, no SHAP from Lambda). Check AWS credentials for full Lambda response.")
        else:
            st.json(result)
            if "top_risk_factors" in result and result["top_risk_factors"]:
                st.markdown("**SHAP-based Top Risk Factors (from model):**")
                for factor in result["top_risk_factors"]:
                    direction_icon = "📈" if factor["direction"] == "increases risk" else "📉"
                    st.markdown(f"- {direction_icon} **{factor['feature']}** — SHAP value: {factor['shap_value']:.4f} ({factor['direction']})")

    st.markdown("""
    <p class="footer-text">
        Model: LightGBM (ROC-AUC 0.759) &nbsp;•&nbsp; 29 Features &nbsp;•&nbsp; AWS Lambda &nbsp;•&nbsp; Quadra Systems Internship 2026
    </p>
    """, unsafe_allow_html=True)

    # --- Enhancement 3: Session Log ---
    if "history" not in st.session_state:
        st.session_state["history"] = []
    
    # Only log when a NEW assessment was just triggered (not on toggle/slider reruns)
    if assess:
        st.session_state["history"].append({
            "ref_no": applicant_ref,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk_score": round(risk_score, 4),
            "risk_category": category,
            "decision": action,
            "business_rule": business_rule_triggered or "None",
            "age": age,
            "income": annual_income,
            "loan_amount": loan_amount,
            "credit_score": ext_source_mean,
            "shap_factors": shap_factors if (shap_factors and shap_factors[0]["direction"] != "error") else [],
        })
    
    if len(st.session_state["history"]) >= 1:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown("#### 📋 Session History")
        import pandas as pd_hist
        hist_df = pd_hist.DataFrame(st.session_state["history"])
        display_df = hist_df.drop(columns=["shap_factors"], errors="ignore")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        csv_data = display_df.to_csv(index=False)
        st.download_button("📥 Download History as CSV", data=csv_data, 
                          file_name=f"loan_assessments_{datetime.now().strftime('%Y%m%d')}.csv",
                          mime="text/csv")
        
        # Export for Batch Assessment (mapped to batch column names)
        batch_export = []
        for row in st.session_state["history"]:
            batch_export.append({
                "AGE_YEARS": row.get("age", 35),
                "EMPLOYMENT_YEARS": 5,
                "IS_UNEMPLOYED": 0,
                "ANNUAL_INCOME": row.get("income", 300000),
                "LOAN_AMOUNT": row.get("loan_amount", 900000),
                "CREDIT_TERM": 24,
                "EXT_SOURCE_MEAN": row.get("credit_score", 0.5),
                "NUM_CHILDREN": 1,
                "FAMILY_SIZE": 3,
                "NAME_CONTRACT_TYPE": "Cash loans",
                "CODE_GENDER": "M",
                "FLAG_OWN_CAR": "N",
                "FLAG_OWN_REALTY": "Y",
                "NAME_INCOME_TYPE": "Working",
                "NAME_EDUCATION_TYPE": "Secondary / secondary special",
                "NAME_FAMILY_STATUS": "Married",
                "NAME_HOUSING_TYPE": "House / apartment",
                "OCCUPATION_TYPE": "Laborers",
                "ORGANIZATION_TYPE": "Business Entity Type 3",
            })
        batch_csv = pd.DataFrame(batch_export).to_csv(index=False)
        st.download_button("📤 Export for Batch Assessment", data=batch_csv,
                          file_name=f"batch_input_{datetime.now().strftime('%Y%m%d')}.csv",
                          mime="text/csv", key="batch_export_btn")
        st.caption("Re-upload this file in Batch Assessment to generate a summary report of all assessed applicants.")

        # --- Report Downloads Section ---
        st.divider()
        st.markdown("##### 📁 Report Downloads")

        # --- ADDITION 1: Individual PDF from session log ---
        st.markdown("")
        st.markdown("**📄 Download Individual Report**")
        history_options = ["Select an applicant..."] + [
            f"{r['ref_no']} — {r['decision']} — {r['timestamp']}" for r in st.session_state["history"]
        ]
        selected_individual = st.selectbox("Choose applicant", history_options, key="individual_pdf_select")
        
        if selected_individual != "Select an applicant...":
            sel_idx = history_options.index(selected_individual) - 1
            sel_row = st.session_state["history"][sel_idx]
            if st.button("📄 Download PDF", key="individual_pdf_btn"):
                try:
                    from fpdf import FPDF as FPDF_IND
                    pdf = FPDF_IND()
                    pdf.add_page()
                    def _s(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
                    pdf.set_font("Helvetica", "B", 18)
                    pdf.set_text_color(0, 100, 180)
                    pdf.cell(0, 12, "Loan Risk Assessment Report", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 6, f"Reference: {sel_row['ref_no']} | Generated: {sel_row['timestamp']}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(6)
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_text_color(40, 40, 40)
                    pdf.cell(0, 8, f"Decision: {sel_row['decision']} ({sel_row['risk_category']})", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", "", 11)
                    pdf.cell(0, 6, f"Default Probability: {sel_row['risk_score']:.1%}", new_x="LMARGIN", new_y="NEXT")
                    if sel_row.get('business_rule') and sel_row['business_rule'] != "None":
                        pdf.cell(0, 6, f"Business Rule: {_s(sel_row['business_rule'])}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.cell(0, 8, "Applicant Summary", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 5, f"Age: {sel_row.get('age','')} | Income: {sel_row.get('income',0):,.0f} | Loan: {sel_row.get('loan_amount',0):,.0f} | Credit Score: {sel_row.get('credit_score','')}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(4)
                    sel_shap = sel_row.get("shap_factors", [])
                    if sel_shap:
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(0, 8, "Top Risk Factors (SHAP)", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", "", 10)
                        for f in sel_shap[:5]:
                            pdf.cell(0, 5, f"  {_s(f['feature'])}: {f['shap_value']:+.4f} ({f['direction']})", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(6)
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(120, 120, 120)
                    pdf.cell(0, 4, "Internal use only. Model: LightGBM (AUC 0.759). Quadra Systems 2026.")
                    st.download_button("⬇️ Download", data=bytes(pdf.output()),
                                      file_name=f"Report_{sel_row['ref_no']}_{sel_row['timestamp'][:10]}.pdf",
                                      mime="application/pdf", key="ind_pdf_dl")
                except Exception as e:
                    st.error(f"PDF error: {e}")

        # --- ADDITION 2: Combined PDF for multiple applicants ---
        st.markdown("")
        st.markdown("**📄 Combined Report**")
        multi_options = [f"{r['ref_no']} — {r['decision']} — {r['timestamp']}" for r in st.session_state["history"]]
        selected_multi = st.multiselect("Select applicants for combined report", multi_options, key="combined_pdf_multi")
        
        if selected_multi and st.button("📄 Download Combined PDF", key="combined_pdf_btn"):
            try:
                from fpdf import FPDF as FPDF_COMB
                pdf = FPDF_COMB()
                def _s(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
                
                # Page 1: Summary
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(0, 100, 180)
                pdf.cell(0, 12, "Combined Loan Assessment Report", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')} | Applicants: {len(selected_multi)}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(8)
                
                # Summary table header
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(40, 40, 40)
                pdf.cell(25, 6, "Ref", border=1)
                pdf.cell(15, 6, "Age", border=1)
                pdf.cell(30, 6, "Income", border=1)
                pdf.cell(30, 6, "Loan", border=1)
                pdf.cell(25, 6, "Decision", border=1)
                pdf.cell(20, 6, "Score", border=1)
                pdf.cell(30, 6, "Rule?", border=1, new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("Helvetica", "", 9)
                selected_rows = []
                for sel in selected_multi:
                    idx = multi_options.index(sel)
                    row = st.session_state["history"][idx]
                    selected_rows.append(row)
                    pdf.cell(25, 5, str(row['ref_no'])[:8], border=1)
                    pdf.cell(15, 5, str(row.get('age', '')), border=1)
                    pdf.cell(30, 5, f"{row.get('income',0):,.0f}", border=1)
                    pdf.cell(30, 5, f"{row.get('loan_amount',0):,.0f}", border=1)
                    pdf.cell(25, 5, row['decision'], border=1)
                    pdf.cell(20, 5, f"{row['risk_score']:.1%}", border=1)
                    pdf.cell(30, 5, "Yes" if row.get('business_rule', 'None') != 'None' else "No", border=1, new_x="LMARGIN", new_y="NEXT")
                
                # Individual pages
                for row in selected_rows:
                    pdf.add_page()
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_text_color(0, 100, 180)
                    pdf.cell(0, 10, f"Applicant: {row['ref_no']}", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", "", 11)
                    pdf.set_text_color(40, 40, 40)
                    pdf.cell(0, 6, f"Decision: {row['decision']} ({row['risk_category']}) | Risk: {row['risk_score']:.1%}", new_x="LMARGIN", new_y="NEXT")
                    if row.get('business_rule') and row['business_rule'] != 'None':
                        pdf.cell(0, 6, f"Business Rule: {_s(row['business_rule'])}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.cell(0, 5, f"Age: {row.get('age','')} | Income: {row.get('income',0):,.0f} | Loan: {row.get('loan_amount',0):,.0f} | Score: {row.get('credit_score','')}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(4)
                    row_shap = row.get("shap_factors", [])
                    if row_shap:
                        pdf.set_font("Helvetica", "B", 11)
                        pdf.cell(0, 7, "Top Risk Factors (SHAP)", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", "", 10)
                        for f in row_shap[:5]:
                            pdf.cell(0, 5, f"  {_s(f['feature'])}: {f['shap_value']:+.4f} ({f['direction']})", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(6)
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(120, 120, 120)
                    pdf.cell(0, 4, "Internal use only. Quadra Systems 2026.")
                    pdf.set_text_color(40, 40, 40)
                
                st.download_button("⬇️ Download Combined PDF", data=bytes(pdf.output()),
                                  file_name=f"Combined_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                  mime="application/pdf", key="combined_pdf_dl")
            except Exception as e:
                st.error(f"Combined PDF error: {e}")


if not st.session_state.get("assessment_done", False):
    # ============================================================
    # LANDING PAGE
    # ============================================================
    st.markdown("")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🧠</div>
            <h3>ML-Powered</h3>
            <p>LightGBM trained on 307K+ loan applications with ROC-AUC of 0.759 on holdout data.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🔬</div>
            <h3>Explainable AI</h3>
            <p>SHAP-based explanations break down every prediction into human-readable risk factors.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">⚡</div>
            <h3>Real-Time</h3>
            <p>Sub-second predictions via AWS Lambda. Instant APPROVE, REVIEW, or REJECT decisions.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # How it works + Architecture side by side
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🚀 How It Works")
        st.markdown("""
1. Fill in applicant details in the sidebar
2. Click **ASSESS RISK**
3. Get instant ML prediction + recommendation
4. Review risk factors before final decision
        """)

    with col_right:
        st.markdown("#### 🏗️ Architecture")
        st.markdown("""
<div class="arch-container">
    <div class="arch-step">👤 Loan Officer (Streamlit UI)</div><br>
    <span class="arch-arrow">↓</span><br>
    <div class="arch-step">⚡ AWS Lambda (predict-default-risk)</div><br>
    <span class="arch-arrow">↓</span><br>
    <div class="arch-step">🧠 LightGBM + Preprocessor (from S3)</div><br>
    <span class="arch-arrow">↓</span><br>
    <div class="arch-step">📊 Risk Score + Category + Action</div>
</div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Model stats
    st.markdown("#### 📈 Model Performance")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown('''<div class="metric-card"><p class="label">ROC-AUC</p><p class="value">0.759</p></div>''', unsafe_allow_html=True)
    with m2:
        st.markdown('''<div class="metric-card"><p class="label">Training Samples</p><p class="value">307K</p></div>''', unsafe_allow_html=True)
    with m3:
        st.markdown('''<div class="metric-card"><p class="label">Features</p><p class="value">29</p></div>''', unsafe_allow_html=True)
    with m4:
        st.markdown('''<div class="metric-card"><p class="label">Inference</p><p class="value">&lt;10ms</p></div>''', unsafe_allow_html=True)

    st.markdown("""
    <p class="footer-text">
        Quadra Systems &nbsp;•&nbsp; AWS Partner &nbsp;•&nbsp; Internship Project 2026
    </p>
    """, unsafe_allow_html=True)


# ============================================================
# BATCH ASSESSMENT MODE (Enhancement 6)
# ============================================================
st.markdown('<hr class="divider">', unsafe_allow_html=True)
with st.expander("📊 Batch Assessment — Upload CSV for Multiple Applicants", expanded=False):
    st.caption("Upload a CSV file with applicant data to assess multiple applications at once.")
    st.markdown("""
    **Required CSV columns:** AGE_YEARS, EMPLOYMENT_YEARS, IS_UNEMPLOYED, ANNUAL_INCOME, LOAN_AMOUNT, 
    CREDIT_TERM, EXT_SOURCE_MEAN, NUM_CHILDREN, FAMILY_SIZE, NAME_CONTRACT_TYPE, CODE_GENDER, 
    FLAG_OWN_CAR, FLAG_OWN_REALTY, NAME_INCOME_TYPE, NAME_EDUCATION_TYPE, NAME_FAMILY_STATUS, 
    NAME_HOUSING_TYPE, OCCUPATION_TYPE, ORGANIZATION_TYPE
    """)
    
    # CSV Template download
    template_row = {
        "AGE_YEARS": 35, "EMPLOYMENT_YEARS": 5, "IS_UNEMPLOYED": 0,
        "ANNUAL_INCOME": 300000, "LOAN_AMOUNT": 900000, "CREDIT_TERM": 24,
        "EXT_SOURCE_MEAN": 0.60, "NUM_CHILDREN": 1, "FAMILY_SIZE": 3,
        "NAME_CONTRACT_TYPE": "Cash loans", "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "N", "FLAG_OWN_REALTY": "Y",
        "NAME_INCOME_TYPE": "Working", "NAME_EDUCATION_TYPE": "Secondary / secondary special",
        "NAME_FAMILY_STATUS": "Married", "NAME_HOUSING_TYPE": "House / apartment",
        "OCCUPATION_TYPE": "Laborers", "ORGANIZATION_TYPE": "Business Entity Type 3",
    }
    template_csv = pd.DataFrame([template_row]).to_csv(index=False)
    st.download_button("📥 Download CSV Template", data=template_csv,
                      file_name="batch_template.csv", mime="text/csv", key="batch_template_btn")
    st.caption("Fill this template in Excel and upload below. Or use 'Export for Batch Assessment' from the Session Log above.")
    
    st.markdown("")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="batch_csv")
    
    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.success(f"Loaded {len(batch_df)} applications")
            
            if st.button("🚀 Run Batch Assessment", use_container_width=True):
                results = []
                progress_bar = st.progress(0)
                
                for idx, row in batch_df.iterrows():
                    # Build features from CSV row
                    annual_inc = float(row.get("ANNUAL_INCOME", 0))
                    loan_amt = float(row.get("LOAN_AMOUNT", 0))
                    fam_size = int(row.get("FAMILY_SIZE", 1))
                    n_children = int(row.get("NUM_CHILDREN", 0))
                    cr_term = float(row.get("CREDIT_TERM", 24))
                    ext_score = float(row.get("EXT_SOURCE_MEAN", 0.5))
                    
                    credit_ratio = round(loan_amt / annual_inc, 2) if annual_inc > 0 else 15.0
                    annuity_ratio = 0.80 if annual_inc == 0 else 0.18  # Simplified for batch
                    
                    features = {
                        "AGE_YEARS": float(row.get("AGE_YEARS", 35)),
                        "EMPLOYMENT_YEARS": float(row.get("EMPLOYMENT_YEARS", 5)),
                        "IS_UNEMPLOYED": int(row.get("IS_UNEMPLOYED", 0)),
                        "CREDIT_TO_INCOME_RATIO": credit_ratio,
                        "ANNUITY_TO_INCOME_RATIO": annuity_ratio,
                        "CREDIT_PER_FAMILY_MEMBER": int(loan_amt / max(fam_size, 1)),
                        "INCOME_PER_FAMILY_MEMBER": int(annual_inc / max(fam_size, 1)),
                        "CHILD_DEPENDENCY_RATIO": round(n_children / max(fam_size, 1), 4),
                        "EXT_SOURCE_MEAN": ext_score,
                        "CREDIT_TERM": cr_term,
                        "EXT_SOURCE_1_MISSING": 0 if ext_score > 0 else 1,
                        "OWN_CAR_AGE_MISSING": 1 if row.get("FLAG_OWN_CAR", "N") == "N" else 0,
                        "YEARS_BUILD_MISSING": 0 if row.get("FLAG_OWN_REALTY", "N") == "Y" else 1,
                        "NAME_CONTRACT_TYPE": row.get("NAME_CONTRACT_TYPE", "Cash loans"),
                        "CODE_GENDER": row.get("CODE_GENDER", "M"),
                        "FLAG_OWN_CAR": row.get("FLAG_OWN_CAR", "N"),
                        "FLAG_OWN_REALTY": row.get("FLAG_OWN_REALTY", "Y"),
                        "NAME_TYPE_SUITE": "Unaccompanied",
                        "NAME_INCOME_TYPE": row.get("NAME_INCOME_TYPE", "Working"),
                        "NAME_EDUCATION_TYPE": row.get("NAME_EDUCATION_TYPE", "Secondary / secondary special"),
                        "NAME_FAMILY_STATUS": row.get("NAME_FAMILY_STATUS", "Married"),
                        "NAME_HOUSING_TYPE": row.get("NAME_HOUSING_TYPE", "House / apartment"),
                        "OCCUPATION_TYPE": row.get("OCCUPATION_TYPE", "Laborers"),
                        "WEEKDAY_APPR_PROCESS_START": "MONDAY",
                        "ORGANIZATION_TYPE": row.get("ORGANIZATION_TYPE", "Business Entity Type 3"),
                        "FONDKAPREMONT_MODE": "reg oper account",
                        "HOUSETYPE_MODE": "block of flats",
                        "WALLSMATERIAL_MODE": "Panel",
                        "EMERGENCYSTATE_MODE": "No",
                    }
                    
                    score = predict_local(features)
                    
                    # Apply business rules and track which fired
                    batch_rule = "None"
                    if annual_inc == 0 and loan_amt > 100000:
                        score = max(score, 0.85)
                        batch_rule = "Zero Income + Large Loan"
                    elif annual_inc == 0 and loan_amt > 0:
                        score = max(score, 0.20)
                        batch_rule = "Zero Income"
                    elif annual_inc > 0 and credit_ratio > 10 and 0.60 < 1:
                        # Check extreme debt (simplified — annuity ratio not computed in batch)
                        pass
                    
                    if score < 0.15:
                        decision = "APPROVE"
                        cat = "Low Risk"
                    elif score < 0.50:
                        decision = "REVIEW"
                        cat = "Medium Risk"
                    else:
                        decision = "REJECT"
                        cat = "High Risk"
                    
                    # Borderline check
                    borderline = "Yes" if (abs(score - 0.15) < 0.03 or abs(score - 0.50) < 0.03) else "No"
                    
                    # Top SHAP factor (simplified — use compute_shap_factors for first row only to avoid slowness)
                    top_factor = "N/A"
                    if idx == 0 or len(results) < 5:  # Only compute SHAP for first few rows (expensive)
                        try:
                            shap_result = compute_shap_factors(features)
                            if shap_result and shap_result[0]["direction"] != "error":
                                top_factor = get_display_name(shap_result[0]["feature"], True)
                        except Exception:
                            pass
                    
                    # Credit/Income ratio
                    ci_ratio = round(loan_amt / annual_inc, 2) if annual_inc > 0 else "N/A"
                    
                    results.append({
                        "Reference": f"APP-{idx+1:03d}",
                        "Risk Score": round(score, 4),
                        "Category": cat,
                        "Decision": decision,
                        "Business Rule": batch_rule,
                        "Borderline": borderline,
                        "Age": row.get("AGE_YEARS", ""),
                        "Income": annual_inc,
                        "Loan": loan_amt,
                        "Credit Score": ext_score,
                        "Top Risk Factor": top_factor,
                        "Credit/Income": ci_ratio,
                    })
                    
                    progress_bar.progress((idx + 1) / len(batch_df))
                
                results_df = pd.DataFrame(results)
                st.dataframe(results_df, use_container_width=True, hide_index=True)
                
                # Summary
                approve_count = len(results_df[results_df["Decision"] == "APPROVE"])
                review_count = len(results_df[results_df["Decision"] == "REVIEW"])
                reject_count = len(results_df[results_df["Decision"] == "REJECT"])
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("✅ APPROVE", approve_count)
                with sc2:
                    st.metric("⚠️ REVIEW", review_count)
                with sc3:
                    st.metric("❌ REJECT", reject_count)
                
                # Download
                csv_results = results_df.to_csv(index=False)
                st.download_button("📥 Download Results CSV", data=csv_results,
                                  file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                  mime="text/csv")
        except Exception as e:
            st.error(f"Error processing CSV: {e}")


# ============================================================
# QUICK ASSESSMENT MODE (Enhancement 11)
# ============================================================
st.markdown('<hr class="divider">', unsafe_allow_html=True)
with st.expander("⚡ Quick Assessment — 5 Fields Only", expanded=False):
    st.warning("⚠️ This prediction assumes default values for 24 fields. Treat as indicative only — do not use for final loan decisions.")
    st.caption("Instant triage with just 5 essential inputs. Uses defaults for everything else.")
    
    qc1, qc2 = st.columns(2)
    with qc1:
        q_age = st.number_input("Age", min_value=18, max_value=70, value=35, key="q_age")
        q_income = st.number_input("Annual Income", min_value=0, max_value=50000000, value=300000, step=10000, key="q_income")
        q_loan = st.number_input("Loan Amount", min_value=0, max_value=100000000, value=900000, step=50000, key="q_loan")
    with qc2:
        q_score = st.number_input("Credit Score (0-1)", min_value=0.0, max_value=1.0, value=0.60, step=0.05, key="q_score")
        q_employment = st.number_input("Employment (years)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, key="q_emp")
    
    if st.button("⚡ Quick Assess", use_container_width=True, key="quick_assess_btn"):
        # Build features with defaults
        q_credit_ratio = round(q_loan / q_income, 2) if q_income > 0 else 15.0
        q_features = {
            "AGE_YEARS": q_age, "EMPLOYMENT_YEARS": q_employment, "IS_UNEMPLOYED": 0,
            "CREDIT_TO_INCOME_RATIO": q_credit_ratio, "ANNUITY_TO_INCOME_RATIO": 0.18 if q_income > 0 else 0.80,
            "CREDIT_PER_FAMILY_MEMBER": int(q_loan / 3), "INCOME_PER_FAMILY_MEMBER": int(q_income / 3),
            "CHILD_DEPENDENCY_RATIO": 0.33, "EXT_SOURCE_MEAN": q_score, "CREDIT_TERM": 24,
            "EXT_SOURCE_1_MISSING": 0, "OWN_CAR_AGE_MISSING": 1, "YEARS_BUILD_MISSING": 1,
            "NAME_CONTRACT_TYPE": "Cash loans", "CODE_GENDER": "M", "FLAG_OWN_CAR": "N",
            "FLAG_OWN_REALTY": "Y", "NAME_TYPE_SUITE": "Unaccompanied", "NAME_INCOME_TYPE": "Working",
            "NAME_EDUCATION_TYPE": "Secondary / secondary special", "NAME_FAMILY_STATUS": "Married",
            "NAME_HOUSING_TYPE": "House / apartment", "OCCUPATION_TYPE": "Laborers",
            "WEEKDAY_APPR_PROCESS_START": "MONDAY", "ORGANIZATION_TYPE": "Business Entity Type 3",
            "FONDKAPREMONT_MODE": "reg oper account", "HOUSETYPE_MODE": "block of flats",
            "WALLSMATERIAL_MODE": "Panel", "EMERGENCYSTATE_MODE": "No",
        }
        q_score_result = predict_local(q_features)
        
        # Apply business rules
        if q_income == 0 and q_loan > 100000:
            q_score_result = max(q_score_result, 0.85)
        elif q_income == 0 and q_loan > 0:
            q_score_result = max(q_score_result, 0.20)
        
        if q_score_result < 0.15:
            q_decision, q_cat = "APPROVE", "Low Risk"
            q_color = "#66bb6a"
        elif q_score_result < 0.50:
            q_decision, q_cat = "REVIEW", "Medium Risk"
            q_color = "#ffa726"
        else:
            q_decision, q_cat = "REJECT", "High Risk"
            q_color = "#ef5350"
        
        st.markdown(f'<div style="background:#151b2e; border-left:6px solid {q_color}; border-radius:10px; padding:16px 20px; margin-top:12px;">'
                    f'<span style="font-size:1.3rem; font-weight:800; color:{q_color};">{q_decision}</span>'
                    f' — <span style="color:#AAA;">{q_cat} • Risk: {q_score_result:.1%}</span></div>', unsafe_allow_html=True)
        st.caption("⚡ Quick triage complete. Use Full Assessment (sidebar) for detailed review with SHAP explanations.")
        
        # Kimi Enhancement 3: Show defaults used
        with st.expander("ℹ️ Defaults used for this triage", expanded=False):
            st.markdown("""
- **Family Size:** 3 · **Children:** 1 · **Gender:** Male
- **Owns Car:** No · **Owns Property:** Yes
- **Income Source:** Working · **Education:** Secondary
- **Housing:** House / apartment · **Loan Term:** 24 months
- **Occupation:** Laborers · **Employer:** Business Entity Type 3
- **Loan Type:** Cash loans · **Unemployed:** No

*Switch to Full Assessment to customize all fields.*
            """)


# ============================================================
# WHAT-IF SCENARIO ANALYZER (Enhancement 2 — Dynamic SHAP-driven)
# ============================================================
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Mapping: SHAP feature name → slider config
WHATIF_CONTROLLABLE = {
    "EXT_SOURCE_MEAN": {"label": "Credit Score", "min": 0.0, "max": 1.0, "step": 0.01, "key": "wi_ext_source", "feature": "EXT_SOURCE_MEAN"},
    "EXT_SOURCE_1_MISSING": {"label": "Credit Score Available (0=yes, 1=no)", "min": 0.0, "max": 1.0, "step": 1.0, "key": "wi_ext_missing", "feature": "EXT_SOURCE_1_MISSING"},
    "CREDIT_TO_INCOME_RATIO": {"label": "Annual Income (₹)", "min": 0, "max": 5000000, "step": 10000, "key": "wi_income", "feature": "INCOME_PER_FAMILY_MEMBER", "transform": "income"},
    "INCOME_PER_FAMILY_MEMBER": {"label": "Annual Income (₹)", "min": 0, "max": 5000000, "step": 10000, "key": "wi_income2", "feature": "INCOME_PER_FAMILY_MEMBER", "transform": "income"},
    "CREDIT_PER_FAMILY_MEMBER": {"label": "Loan Amount (₹)", "min": 0, "max": 10000000, "step": 10000, "key": "wi_loan", "feature": "CREDIT_PER_FAMILY_MEMBER", "transform": "loan"},
    "ANNUITY_TO_INCOME_RATIO": {"label": "Monthly EMI (₹)", "min": 0, "max": 500000, "step": 1000, "key": "wi_emi", "feature": "ANNUITY_TO_INCOME_RATIO", "transform": "emi"},
    "EMPLOYMENT_YEARS": {"label": "Employment Years", "min": 0.0, "max": 50.0, "step": 1.0, "key": "wi_emp", "feature": "EMPLOYMENT_YEARS"},
    "IS_UNEMPLOYED": {"label": "Currently Unemployed", "type": "toggle", "key": "wi_unemployed", "feature": "IS_UNEMPLOYED"},
    "CREDIT_TERM": {"label": "Loan Term (months)", "min": 1, "max": 120, "step": 1, "key": "wi_term", "feature": "CREDIT_TERM"},
    "AGE_YEARS": {"label": "Age (years)", "min": 18.0, "max": 70.0, "step": 1.0, "key": "wi_age", "feature": "AGE_YEARS"},
    "CHILD_DEPENDENCY": {"label": "Number of Children", "min": 0, "max": 10, "step": 1, "key": "wi_children", "feature": "CHILD_DEPENDENCY_RATIO", "transform": "children"},
}

with st.expander("🔄 What-If Scenario Analyzer", expanded=False):
    st.caption("See how changing one input would change the decision — without re-filling the form.")
    
    if "last_features" not in st.session_state or "last_risk_score" not in st.session_state:
        st.info("Run a Full Assessment first (sidebar), then come here to explore scenarios.")
    else:
        baseline_score = st.session_state.get("last_risk_score", 0.5)
        baseline_features = st.session_state.get("last_features", {})
        top_shap = st.session_state.get("top_shap_features", [])
        
        st.markdown(f"**Baseline:** Risk = {baseline_score:.1%}")
        
        # Determine which sliders to show based on top SHAP features
        controllable = []
        seen_keys = set()
        for feat in top_shap:
            # Match feature name (handle one-hot encoded names like "NAME_EDUCATION_TYPE_Higher education")
            for shap_key, config in WHATIF_CONTROLLABLE.items():
                if shap_key in feat and config["key"] not in seen_keys:
                    controllable.append(config)
                    seen_keys.add(config["key"])
                    break
        
        # Fallback: if fewer than 2 controllable features, show defaults
        if len(controllable) < 2:
            controllable = [
                WHATIF_CONTROLLABLE["EXT_SOURCE_MEAN"],
                WHATIF_CONTROLLABLE["CREDIT_PER_FAMILY_MEMBER"],
                WHATIF_CONTROLLABLE["EMPLOYMENT_YEARS"],
                WHATIF_CONTROLLABLE["CREDIT_TERM"],
            ]
        
        st.caption("🎯 These fields are the top numeric drivers of risk that you can adjust. (Categorical factors like Gender/Education cannot be changed in What-If.)")
        
        # Render dynamic sliders
        scenario_overrides = {}
        wi_cols = st.columns(min(len(controllable), 3))
        for i, config in enumerate(controllable[:4]):
            with wi_cols[i % len(wi_cols)]:
                feat_key = config["feature"]
                if config.get("type") == "toggle":
                    val = st.toggle(config["label"], value=bool(baseline_features.get(feat_key, 0)), key=config["key"])
                    scenario_overrides[feat_key] = int(val)
                elif isinstance(config["min"], float):
                    val = st.number_input(config["label"], min_value=config["min"], max_value=config["max"],
                                         value=float(baseline_features.get(feat_key, config["min"])),
                                         step=config["step"], key=config["key"])
                    scenario_overrides[feat_key] = val
                else:
                    # Integer sliders — need to derive sensible default from features
                    default_val = baseline_features.get(feat_key, 0)
                    if config.get("transform") == "income":
                        default_val = int(default_val * 3)  # income_per_family * 3 ≈ total income
                    elif config.get("transform") == "loan":
                        default_val = int(default_val * 3)  # credit_per_family * 3 ≈ total loan
                    elif config.get("transform") == "emi":
                        default_val = int(default_val * baseline_features.get("INCOME_PER_FAMILY_MEMBER", 100000) * 3 / 12)
                    default_val = max(config["min"], min(config["max"], int(default_val)))
                    val = st.number_input(config["label"], min_value=config["min"], max_value=config["max"],
                                         value=default_val, step=config["step"], key=config["key"])
                    scenario_overrides[config["key"]] = val
                    # Store raw value for feature computation
                    if config.get("transform") == "income":
                        scenario_overrides["INCOME_PER_FAMILY_MEMBER"] = int(val / 3)
                        scenario_overrides["CREDIT_TO_INCOME_RATIO"] = round(baseline_features.get("CREDIT_PER_FAMILY_MEMBER", 300000) * 3 / max(val, 1), 2)
                    elif config.get("transform") == "loan":
                        scenario_overrides["CREDIT_PER_FAMILY_MEMBER"] = int(val / 3)
                        income_est = baseline_features.get("INCOME_PER_FAMILY_MEMBER", 100000) * 3
                        scenario_overrides["CREDIT_TO_INCOME_RATIO"] = round(val / max(income_est, 1), 2)
                    elif config.get("transform") == "emi":
                        income_est = baseline_features.get("INCOME_PER_FAMILY_MEMBER", 100000) * 3
                        scenario_overrides["ANNUITY_TO_INCOME_RATIO"] = round(val / max(income_est / 12, 1), 4)
        
        if st.button("🔄 Compare Scenario", use_container_width=True, key="whatif_btn"):
            # Build scenario features
            scenario_features = baseline_features.copy()
            for k, v in scenario_overrides.items():
                if k in scenario_features:
                    scenario_features[k] = v
            
            scenario_score = predict_local(scenario_features)
            
            # Compare
            diff = scenario_score - baseline_score
            if scenario_score < 0.15:
                s_decision = "APPROVE"
            elif scenario_score < 0.50:
                s_decision = "REVIEW"
            else:
                s_decision = "REJECT"
            
            b_decision = "APPROVE" if baseline_score < 0.15 else "REVIEW" if baseline_score < 0.50 else "REJECT"
            
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            with comp_col1:
                st.metric("Baseline", f"{baseline_score:.1%}", delta=None)
                st.caption(b_decision)
            with comp_col2:
                st.metric("Scenario", f"{scenario_score:.1%}", delta=f"{diff:+.1%}")
                st.caption(s_decision)
            with comp_col3:
                if b_decision != s_decision:
                    st.success(f"Decision flipped: {b_decision} → {s_decision}")
                else:
                    st.info(f"Decision unchanged: {s_decision}")
