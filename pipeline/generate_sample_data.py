"""
generate_sample_data.py - builds a small fake Telco-shaped dataset for
testing the pipeline before you download the real one.

Shaped exactly like the real IBM/Kaggle "Telco Customer Churn" dataset,
including its single most famous real-world quirk on purpose: brand new
customers (tenure = 0) have a BLANK TotalCharges field in the real data,
because they haven't been billed yet. This script plants that same issue
plus a handful of others, so you can watch validate.py catch them before
you ever touch the real file.
"""
import random

import numpy as np
import pandas as pd

from config import RAW_DIR, RANDOM_SEED

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

N = 1500

GENDERS = ["Male", "Female"]
YES_NO = ["Yes", "No"]
INTERNET = ["DSL", "Fiber optic", "No"]
CONTRACT = ["Month-to-month", "One year", "Two year"]
PAYMENT = ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
LINES = ["Yes", "No", "No phone service"]
ADDON = ["Yes", "No", "No internet service"]


def make_customer_id(i):
    return f"{np.random.randint(1000, 9999)}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}-{i}"


rows = []
for i in range(N):
    tenure = int(np.clip(np.random.exponential(20), 0, 72))
    monthly = round(np.random.uniform(18.0, 120.0), 2)
    internet = random.choices(INTERNET, weights=[0.35, 0.45, 0.20])[0]
    has_internet = internet != "No"
    contract = random.choices(CONTRACT, weights=[0.55, 0.22, 0.23])[0]

    # Churn more likely for month-to-month, short tenure, fiber optic, no tech support —
    # mirrors the real dataset's known patterns so the model has something real to learn.
    churn_score = (
        0.35 * (contract == "Month-to-month")
        + 0.20 * (internet == "Fiber optic")
        + 0.25 * (tenure < 12)
        - 0.20 * (contract == "Two year")
        + np.random.normal(0, 0.15)
    )
    churn = "Yes" if churn_score > 0.35 else "No"

    total_charges = round(monthly * tenure, 2)

    rows.append({
        "customerID": make_customer_id(i),
        "gender": random.choice(GENDERS),
        "SeniorCitizen": np.random.choice([0, 1], p=[0.84, 0.16]),
        "Partner": random.choice(YES_NO),
        "Dependents": random.choice(YES_NO),
        "tenure": tenure,
        "PhoneService": "Yes" if random.random() > 0.1 else "No",
        "MultipleLines": random.choice(LINES),
        "InternetService": internet,
        "OnlineSecurity": random.choice(ADDON) if has_internet else "No internet service",
        "OnlineBackup": random.choice(ADDON) if has_internet else "No internet service",
        "DeviceProtection": random.choice(ADDON) if has_internet else "No internet service",
        "TechSupport": random.choice(ADDON) if has_internet else "No internet service",
        "StreamingTV": random.choice(ADDON) if has_internet else "No internet service",
        "StreamingMovies": random.choice(ADDON) if has_internet else "No internet service",
        "Contract": contract,
        "PaperlessBilling": random.choice(YES_NO),
        "PaymentMethod": random.choice(PAYMENT),
        "MonthlyCharges": monthly,
        "TotalCharges": total_charges,
        "Churn": churn,
    })

df = pd.DataFrame(rows)

# --- plant realistic problems on purpose, same spirit as Project 1 ---

# 1. The REAL quirk: tenure = 0 customers get a blank TotalCharges (not billed yet).
# Cast to object dtype first since we're mixing in a string — matches how
# the real CSV stores this column (as text, not a number) for this exact reason.
df["TotalCharges"] = df["TotalCharges"].astype(object)
zero_tenure_idx = df[df["tenure"] == 0].index
df.loc[zero_tenure_idx, "TotalCharges"] = " "
if len(zero_tenure_idx) == 0:
    # guarantee at least a few, so the check has something to catch
    some_idx = df.sample(8, random_state=RANDOM_SEED).index
    df.loc[some_idx, "tenure"] = 0
    df.loc[some_idx, "TotalCharges"] = " "

# 2. A handful of exact duplicate customer rows.
dupes = df.sample(5, random_state=RANDOM_SEED)
df = pd.concat([df, dupes], ignore_index=True)

# 3. A few missing customer IDs.
missing_id_idx = df.sample(3, random_state=RANDOM_SEED + 1).index
df.loc[missing_id_idx, "customerID"] = ""

# 4. A few impossible negative tenures (data entry mistake).
neg_tenure_idx = df.sample(4, random_state=RANDOM_SEED + 2).index
df.loc[neg_tenure_idx, "tenure"] = -3

# 5. A few non-positive monthly charges.
bad_charge_idx = df.sample(3, random_state=RANDOM_SEED + 3).index
df.loc[bad_charge_idx, "MonthlyCharges"] = 0

# 6. A few invalid Churn values (typos / bad exports happen).
bad_churn_idx = df.sample(3, random_state=RANDOM_SEED + 4).index
df.loc[bad_churn_idx, "Churn"] = "Unknown"

RAW_DIR.mkdir(parents=True, exist_ok=True)
out_path = RAW_DIR / "telco_customer_churn.csv"
df.to_csv(out_path, index=False)
print(f"Wrote {len(df):,} rows (with planted issues) to {out_path}")
