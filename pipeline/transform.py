"""
transform.py - STEP 2: turn validated customer rows into the features
and business metrics everything downstream needs.

Two separate jobs happen here, kept in separate functions on purpose:
1. Business metrics anyone can read (historical LTV, projected LTV, tenure
   bucket) — these go straight into the warehouse and the dashboard.
2. Model-ready features (one-hot encoded categoricals) — these only feed
   model.py, never the dashboard directly, so the warehouse stays readable
   by a human instead of full of 0/1 dummy columns.
"""
import numpy as np
import pandas as pd

from config import CLEAN_DIR, LTV_PROJECTION_MONTHS


def tenure_bucket(months):
    if months < 6:
        return "0-6 months"
    if months < 12:
        return "6-12 months"
    if months < 24:
        return "1-2 years"
    if months < 48:
        return "2-4 years"
    return "4+ years"


def add_business_metrics(df):
    df = df.copy()
    # Blank TotalCharges for tenure=0 customers means "hasn't been billed
    # yet" — the correct fix is 0, not dropping the row (see validate.py).
    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

    df["historical_ltv"] = df["TotalCharges"]
    # Forward-looking value for customers still active: what they're worth
    # over the next LTV_PROJECTION_MONTHS if they keep paying at their
    # current monthly rate. Churned customers get 0 here — there's nothing
    # left to project forward.
    df["projected_ltv"] = np.where(
        df["Churn"] == "No",
        df["MonthlyCharges"] * LTV_PROJECTION_MONTHS,
        0.0,
    )
    df["tenure_bucket"] = df["tenure"].apply(tenure_bucket)
    return df


def build_model_features(df):
    """One-hot encode categoricals for the model. Returns (X, y, feature_names)."""
    feature_cols_binary = [
        "gender", "Partner", "Dependents", "PhoneService", "PaperlessBilling",
    ]
    feature_cols_categorical = [
        "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
        "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
        "Contract", "PaymentMethod",
    ]
    numeric_cols = ["tenure", "MonthlyCharges", "SeniorCitizen"]

    X = df[numeric_cols].copy()
    for col in feature_cols_binary:
        X[col] = (df[col] == "Yes").astype(int)
    X = pd.concat([X, pd.get_dummies(df[feature_cols_categorical], drop_first=True)], axis=1)
    X = X.astype(float)

    y = (df["Churn"] == "Yes").astype(int)
    return X, y, list(X.columns)


def transform():
    df = pd.read_csv(CLEAN_DIR / "customers.csv")
    df = add_business_metrics(df)
    return df


if __name__ == "__main__":
    out = transform()
    print(out[["customerID", "tenure", "tenure_bucket", "historical_ltv", "projected_ltv"]].head())
