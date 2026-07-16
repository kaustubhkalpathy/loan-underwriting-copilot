"""One-time script to fit and save the preprocessor from the training data."""
import pandas as pd
import pickle
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

# Load data
print("Loading dataset...")
df = pd.read_csv(r"Datasets\application_train.csv")
print(f"Loaded: {df.shape}")

# Feature engineering (same as notebook)
df["AGE_YEARS"] = (-df["DAYS_BIRTH"] / 365.25).round(1)
df["EMPLOYMENT_YEARS"] = (-df["DAYS_EMPLOYED"] / 365.25).round(1)
df.loc[df["DAYS_EMPLOYED"] == 365243, "EMPLOYMENT_YEARS"] = 0
df["IS_UNEMPLOYED"] = (df["DAYS_EMPLOYED"] == 365243).astype(int)
df["CREDIT_TO_INCOME_RATIO"] = (df["AMT_CREDIT"] / df["AMT_INCOME_TOTAL"]).round(2)
df["ANNUITY_TO_INCOME_RATIO"] = (df["AMT_ANNUITY"] / df["AMT_INCOME_TOTAL"]).round(4)
df["CREDIT_PER_FAMILY_MEMBER"] = (df["AMT_CREDIT"] / df["CNT_FAM_MEMBERS"]).round(0)
df["INCOME_PER_FAMILY_MEMBER"] = (df["AMT_INCOME_TOTAL"] / df["CNT_FAM_MEMBERS"]).round(0)
df["CHILD_DEPENDENCY_RATIO"] = (df["CNT_CHILDREN"] / df["CNT_FAM_MEMBERS"]).round(4)
df["EXT_SOURCE_MEAN"] = df[["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]].mean(axis=1).round(4)
df["CREDIT_TERM"] = (df["AMT_CREDIT"] / df["AMT_ANNUITY"]).round(1)
df["EXT_SOURCE_1_MISSING"] = df["EXT_SOURCE_1"].isna().astype(int)
df["OWN_CAR_AGE_MISSING"] = df["OWN_CAR_AGE"].isna().astype(int)
df["YEARS_BUILD_MISSING"] = df["YEARS_BUILD_AVG"].isna().astype(int)

numeric_features = [
    "AGE_YEARS", "EMPLOYMENT_YEARS", "IS_UNEMPLOYED",
    "CREDIT_TO_INCOME_RATIO", "ANNUITY_TO_INCOME_RATIO",
    "CREDIT_PER_FAMILY_MEMBER", "INCOME_PER_FAMILY_MEMBER",
    "CHILD_DEPENDENCY_RATIO", "EXT_SOURCE_MEAN", "CREDIT_TERM",
    "EXT_SOURCE_1_MISSING", "OWN_CAR_AGE_MISSING", "YEARS_BUILD_MISSING"
]

categorical_features = [
    "NAME_CONTRACT_TYPE", "CODE_GENDER", "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY", "NAME_TYPE_SUITE", "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS", "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE", "WEEKDAY_APPR_PROCESS_START", "ORGANIZATION_TYPE",
    "FONDKAPREMONT_MODE", "HOUSETYPE_MODE", "WALLSMATERIAL_MODE",
    "EMERGENCYSTATE_MODE"
]

X = df[numeric_features + categorical_features]
print(f"Features: {X.shape}")

# Build preprocessor (same as notebook)
numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median"))
])
categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])
preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features)
])

# Fit on full training data
print("Fitting preprocessor...")
preprocessor.fit(X)
print(f"Fitted! Output features: {preprocessor.get_feature_names_out().shape[0]}")

# Save
output_path = r"Datasets\preprocessor.pkl"
with open(output_path, "wb") as f:
    pickle.dump(preprocessor, f)

print(f"Saved: {output_path}")
import os
print(f"Size: {os.path.getsize(output_path)} bytes")
print("Done! Upload this to S3 bucket 'loan-copilot-quadra' as preprocessor.pkl")
