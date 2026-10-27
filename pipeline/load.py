"""
load.py - STEP 4: build the warehouse and load everything into it.

Runs validate -> transform -> model, then applies schema.sql and loads
every table, same orchestration pattern as Project 1's load.py.
"""
import re

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL, LOG_DIR, SQL_DIR
from model import train_and_score
from transform import transform
from validate import main as run_validation


def split_statements(sql_text):
    no_comments = re.sub(r"--.*", "", sql_text)
    return [s.strip() for s in no_comments.split(";") if s.strip()]


def apply_schema(engine):
    sql_text = (SQL_DIR / "schema.sql").read_text()
    with engine.begin() as conn:
        for stmt in split_statements(sql_text):
            conn.execute(text(stmt))
    print("Schema applied: tables and views created.")


def main():
    print(f"Connecting to: {DB_URL}\n")
    engine = create_engine(DB_URL)

    print("--- Re-running validation so the logs match this load ---")
    run_validation()

    print("\n--- Transforming ---")
    df = transform()

    print("\n--- Training model and scoring every customer ---")
    scored, metrics, importance = train_and_score(df)

    print("\n--- Applying schema ---")
    apply_schema(engine)

    print("\n--- Loading customer_scored ---")
    out = pd.DataFrame({
        "customer_id": scored["customerID"],
        "gender": scored["gender"],
        "senior_citizen": scored["SeniorCitizen"],
        "partner": scored["Partner"],
        "dependents": scored["Dependents"],
        "tenure": scored["tenure"],
        "tenure_bucket": scored["tenure_bucket"],
        "contract": scored["Contract"],
        "internet_service": scored["InternetService"],
        "payment_method": scored["PaymentMethod"],
        "monthly_charges": scored["MonthlyCharges"],
        "historical_ltv": scored["historical_ltv"],
        "projected_ltv": scored["projected_ltv"],
        "churned": scored["Churn"],
        "churn_probability": scored["churn_probability"],
        "risk_segment": scored["risk_segment"],
        "value_at_risk": scored["value_at_risk"],
    })
    with engine.begin() as conn:
        out.to_sql("customer_scored", conn, if_exists="append", index=False)
    print(f"loaded customer_scored    {len(out):>6,} rows")

    with engine.begin() as conn:
        pd.DataFrame([metrics]).rename(columns={"precision": "precision_score", "recall": "recall_score"}) \
            .to_sql("model_metrics", conn, if_exists="append", index=False)
        importance.to_sql("feature_importance", conn, if_exists="append", index=False)
    print("loaded model_metrics and feature_importance")

    print("\n--- Loading data-quality logs ---")
    check_df = pd.read_csv(LOG_DIR / "quality_report.csv")
    summary_df = pd.read_csv(LOG_DIR / "table_summary.csv")
    with engine.begin() as conn:
        check_df.to_sql("dq_check_log", conn, if_exists="append", index=False)
        summary_df.to_sql("dq_table_summary", conn, if_exists="append", index=False)
    print(f"loaded dq_check_log       {len(check_df):>6,} rows")
    print(f"loaded dq_table_summary   {len(summary_df):>6,} rows")

    print("\nDone. Warehouse ready for Tableau.")
    print(f"\nModel accuracy: {metrics['accuracy']:.1%}  |  ROC-AUC: {metrics['roc_auc']:.3f}  |  "
          f"Recall: {metrics['recall']:.1%} (of customers who actually churned, this % were caught)")


if __name__ == "__main__":
    main()
