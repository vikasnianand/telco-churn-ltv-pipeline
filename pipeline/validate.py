"""
validate.py - STEP 1: check every row against business rules before
anything downstream (LTV, the model, the dashboard) ever sees it.

Same pattern as Project 1: an "error" check removes the row and logs why;
a "warning" check keeps the row but counts it. Outputs go to data/clean/,
data/rejected/, and logs/quality_report.csv.
"""
from datetime import datetime, timezone

import pandas as pd

from config import CLEAN_DIR, LOG_DIR, RAW_FILE, REJECTED_DIR

RUN_TIME = datetime.now(timezone.utc).isoformat()
ALL_CHECKS = []


def run_checks(table, df, checks):
    """Apply a list of (name, severity, description, mask) checks.
    'mask' is True for ROWS THAT FAIL. Error checks remove the row;
    warning checks keep it but log it. Returns the surviving rows."""
    rejected_reasons = pd.Series([None] * len(df), index=df.index, dtype=object)
    keep = pd.Series(True, index=df.index)

    for name, severity, description, mask in checks:
        failed = int(mask.sum())
        ALL_CHECKS.append({
            "run_time": RUN_TIME,
            "table_name": table,
            "check_name": name,
            "severity": severity,
            "description": description,
            "rows_checked": len(df),
            "rows_failed": failed,
            "pct_failed": round(100 * failed / len(df), 2) if len(df) else 0.0,
        })
        if severity == "error":
            newly_bad = mask & keep
            rejected_reasons.loc[newly_bad] = name
            keep &= ~mask

    clean = df[keep].copy()
    rejected = df[~keep].copy()
    if len(rejected):
        rejected["reject_reason"] = rejected_reasons[~keep]

    rows_in = len(df)
    rows_clean = len(clean)
    rows_rejected = len(rejected)
    print(f"{table:12s} in={rows_in:>6,}  clean={rows_clean:>6,}  rejected={rows_rejected:>5,}")

    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    if len(rejected):
        rejected.to_csv(REJECTED_DIR / f"{table}_rejected.csv", index=False)

    return clean, {"table_name": table, "rows_in": rows_in, "rows_clean": rows_clean, "rows_rejected": rows_rejected}


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    table_summaries = []

    df = pd.read_csv(RAW_FILE, dtype={"SeniorCitizen": "Int64"})

    # Normalize TotalCharges: the real dataset stores it as text, and
    # brand-new customers (tenure = 0) get a BLANK string instead of a
    # number, because they haven't been billed yet. That's not corrupt
    # data — it's a real, documented quirk of this dataset. We flag it
    # as a warning (not an error) and fix it in transform.py.
    df["TotalCharges_raw"] = df["TotalCharges"]
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    valid_contracts = {"Month-to-month", "One year", "Two year"}
    valid_internet = {"DSL", "Fiber optic", "No"}
    valid_churn = {"Yes", "No"}

    checks = [
        ("duplicate_customer_row", "error", "Exact duplicate row (same customer counted twice)",
         df.duplicated(keep="first")),
        ("missing_customer_id", "error", "customerID is blank",
         df["customerID"].isna() | (df["customerID"].astype(str).str.strip() == "")),
        ("duplicate_customer_id", "error", "Same customerID appears more than once",
         df["customerID"].duplicated(keep="first") & df["customerID"].notna()),
        ("tenure_negative", "error", "tenure (months as customer) is negative — impossible",
         df["tenure"] < 0),
        ("monthly_charges_non_positive", "error", "MonthlyCharges is zero or negative",
         df["MonthlyCharges"] <= 0),
        ("total_charges_blank_new_customer", "warning",
         "TotalCharges is blank — real quirk: brand-new (tenure=0) customers haven't been billed yet",
         df["TotalCharges"].isna() & (df["tenure"] == 0)),
        ("total_charges_blank_other", "error",
         "TotalCharges is blank/unparseable for a customer with tenure > 0 — unexplained, unsafe to keep",
         df["TotalCharges"].isna() & (df["tenure"] != 0)),
        ("contract_invalid", "error", "Contract value isn't one of the three known plan types",
         ~df["Contract"].isin(valid_contracts)),
        ("internet_service_invalid", "error", "InternetService isn't one of the known values",
         ~df["InternetService"].isin(valid_internet)),
        ("churn_invalid", "error", "Churn isn't Yes or No",
         ~df["Churn"].isin(valid_churn)),
    ]

    clean, summary = run_checks("customers", df, checks)
    table_summaries.append(summary)
    clean = clean.drop(columns=["TotalCharges_raw"])
    clean.to_csv(CLEAN_DIR / "customers.csv", index=False)

    pd.DataFrame(ALL_CHECKS).to_csv(LOG_DIR / "quality_report.csv", index=False)
    pd.DataFrame(table_summaries).to_csv(LOG_DIR / "table_summary.csv", index=False)
    print(f"\nWrote {LOG_DIR / 'quality_report.csv'} and {LOG_DIR / 'table_summary.csv'}")


if __name__ == "__main__":
    main()
