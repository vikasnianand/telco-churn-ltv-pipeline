"""
config.py - central settings for the churn & lifetime value pipeline.

Same idea as Project 1: one place for paths, connection settings, and the
business thresholds that define "at risk" — so those decisions are visible
and easy to defend, not buried inside some function.
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
REJECTED_DIR = ROOT / "data" / "rejected"
LOG_DIR = ROOT / "logs"
SQL_DIR = ROOT / "sql"

RAW_FILE = RAW_DIR / "telco_customer_churn.csv"

# Defaults to a local SQLite file for easy testing.
# For MySQL: export DB_URL="mysql+pymysql://user:password@host:3306/dbname"
DB_URL = os.environ.get("DB_URL", f"sqlite:///{ROOT / 'telco_churn_warehouse.db'}")

# --- Business thresholds (the judgment calls) ---
# Everything below is a decision, not a fact. Each one is explained in the
# README so it can be defended, not just quoted as a number.

# A customer counts as "high risk" once their predicted churn probability
# crosses this line. Picked by looking at the precision/recall tradeoff on
# the test set, not an arbitrary round number — see model.py and README.
HIGH_RISK_THRESHOLD = 0.50
MEDIUM_RISK_THRESHOLD = 0.25

# Forward-looking LTV projection window, in months, used for customers who
# haven't churned yet (projected_ltv = MonthlyCharges * LTV_PROJECTION_MONTHS).
LTV_PROJECTION_MONTHS = 12

RANDOM_SEED = 42
