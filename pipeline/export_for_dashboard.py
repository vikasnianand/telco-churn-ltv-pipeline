"""
export_for_dashboard.py - turns the warehouse into ONE Excel file for
Tableau, same bridge pattern as Project 1 (Tableau Public reads Excel
cleanly; it doesn't need a live database connection).

Usage: python pipeline/export_for_dashboard.py
Needs load.py to have been run first (the warehouse must already exist).
"""
import pandas as pd
from sqlalchemy import create_engine

from config import DB_URL, ROOT

VIEWS = {
    "KPI Summary": "vw_kpi_summary",
    "Top Value at Risk": "vw_top_value_at_risk",
    "Risk Segment Summary": "vw_risk_segment_summary",
    "Contract Analysis": "vw_contract_analysis",
    "Data Quality": "vw_data_quality",
    "Feature Importance": "feature_importance",
}

OUTPUT_FILE = ROOT / "data" / "telco_churn_dashboard_data.xlsx"


def main():
    print(f"Connecting to: {DB_URL}")
    engine = create_engine(DB_URL)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name, source in VIEWS.items():
            df = pd.read_sql(f"SELECT * FROM {source}", engine)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  {sheet_name:22s} {len(df):>7,} rows  <- {source}")

    print(f"\nDone. Upload this file to Tableau: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
