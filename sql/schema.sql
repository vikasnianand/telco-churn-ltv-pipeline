-- schema.sql : the warehouse and the views Tableau reads from.
-- Runs on MySQL AND SQLite, same dual-support pattern as Project 1.

DROP VIEW IF EXISTS vw_kpi_summary;
DROP VIEW IF EXISTS vw_risk_segment_summary;
DROP VIEW IF EXISTS vw_contract_analysis;
DROP VIEW IF EXISTS vw_top_value_at_risk;
DROP VIEW IF EXISTS vw_data_quality;

DROP TABLE IF EXISTS dq_check_log;
DROP TABLE IF EXISTS dq_table_summary;
DROP TABLE IF EXISTS model_metrics;
DROP TABLE IF EXISTS feature_importance;
DROP TABLE IF EXISTS customer_scored;

-- One row per customer: their profile, their LTV, and the model's output.
-- Deliberately flat and human-readable — this is what a non-technical
-- stakeholder would open directly, unlike the one-hot encoded features
-- the model trains on (those never leave Python).
CREATE TABLE customer_scored (
    customer_id          VARCHAR(20) PRIMARY KEY,
    gender                VARCHAR(10),
    senior_citizen        INTEGER,
    partner                VARCHAR(5),
    dependents             VARCHAR(5),
    tenure                 INTEGER,
    tenure_bucket          VARCHAR(20),
    contract               VARCHAR(20),
    internet_service       VARCHAR(20),
    payment_method         VARCHAR(40),
    monthly_charges        DECIMAL(10,2),
    historical_ltv         DECIMAL(12,2),
    projected_ltv          DECIMAL(12,2),
    churned                VARCHAR(5),
    churn_probability      DECIMAL(6,4),
    risk_segment            VARCHAR(10),
    value_at_risk           DECIMAL(12,2)
);

CREATE TABLE model_metrics (
    accuracy            DECIMAL(6,4),
    precision_score      DECIMAL(6,4),
    recall_score         DECIMAL(6,4),
    roc_auc              DECIMAL(6,4),
    n_train               INTEGER,
    n_test                INTEGER,
    actual_churn_rate     DECIMAL(6,4),
    true_positive         INTEGER,
    false_positive        INTEGER,
    true_negative          INTEGER,
    false_negative         INTEGER
);

CREATE TABLE feature_importance (
    feature          VARCHAR(60),
    coefficient       DECIMAL(10,4),
    abs_coefficient    DECIMAL(10,4),
    direction           VARCHAR(20)
);

CREATE TABLE dq_check_log (
    run_time      VARCHAR(25),
    table_name    VARCHAR(50),
    check_name    VARCHAR(60),
    severity      VARCHAR(10),
    description   VARCHAR(200),
    rows_checked  INTEGER,
    rows_failed   INTEGER,
    pct_failed    DECIMAL(6,2)
);

CREATE TABLE dq_table_summary (
    run_time       VARCHAR(25),
    table_name     VARCHAR(50),
    rows_in        INTEGER,
    rows_clean     INTEGER,
    rows_rejected  INTEGER
);

-- ---------- views: ready-made tables for Tableau ----------

-- The single most important view: who to call first. Active customers
-- only (already-churned customers have nothing left to act on), ranked
-- by expected revenue at stake.
CREATE VIEW vw_top_value_at_risk AS
SELECT customer_id, tenure, tenure_bucket, contract, internet_service,
       monthly_charges, projected_ltv, churn_probability, risk_segment, value_at_risk
FROM customer_scored
WHERE churned = 'No'
ORDER BY value_at_risk DESC;

CREATE VIEW vw_risk_segment_summary AS
SELECT risk_segment,
       COUNT(*)                   AS customers,
       AVG(churn_probability)      AS avg_churn_probability,
       SUM(projected_ltv)          AS total_projected_ltv,
       SUM(value_at_risk)          AS total_value_at_risk
FROM customer_scored
WHERE churned = 'No'
GROUP BY risk_segment;

CREATE VIEW vw_contract_analysis AS
SELECT contract,
       COUNT(*)                                                  AS customers,
       SUM(CASE WHEN churned = 'Yes' THEN 1 ELSE 0 END)          AS churned_customers,
       AVG(CASE WHEN churned = 'Yes' THEN 1.0 ELSE 0.0 END)      AS churn_rate,
       AVG(monthly_charges)                                      AS avg_monthly_charges,
       SUM(value_at_risk)                                        AS total_value_at_risk
FROM customer_scored
GROUP BY contract;

CREATE VIEW vw_kpi_summary AS
SELECT
    COUNT(*)                                                  AS total_customers,
    SUM(CASE WHEN churned = 'Yes' THEN 1 ELSE 0 END)          AS churned_customers,
    AVG(CASE WHEN churned = 'Yes' THEN 1.0 ELSE 0.0 END)      AS churn_rate,
    SUM(CASE WHEN risk_segment = 'High' AND churned = 'No' THEN 1 ELSE 0 END) AS high_risk_customers,
    SUM(value_at_risk)                                        AS total_value_at_risk,
    AVG(historical_ltv)                                       AS avg_historical_ltv
FROM customer_scored;

CREATE VIEW vw_data_quality AS
SELECT run_time, table_name, check_name, severity, description, rows_checked, rows_failed, pct_failed
FROM dq_check_log;
