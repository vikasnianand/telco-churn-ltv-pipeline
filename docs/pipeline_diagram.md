```
  data/raw/*.csv          validate.py             transform.py
 (Telco export,     ──▶   ~10 rules on       ──▶   historical + projected
  untouched)               one table                LTV, tenure buckets
                                 │                          │
                                 ▼                          ▼
                         data/rejected/*.csv          model.py
                        (bad rows + reason,         logistic regression,
                         logs/quality_report.csv)   scores every customer,
                                 │                   computes value_at_risk
                                 │                          │
                                 └──────────┬───────────────┘
                                            ▼
                                       load.py
                              applies sql/schema.sql, then
                              loads customer_scored, model
                                 metrics, dq logs
                                            │
                                            ▼
                               MySQL / SQLite warehouse
                                            │
                                            ▼
                                   Tableau dashboard
                           (vw_kpi_summary, vw_top_value_at_risk,
                            vw_risk_segment_summary, vw_contract_analysis,
                            vw_data_quality, feature_importance)
```
Paste this into draw.io (or redraw it there) for the README, same as Project 1.
