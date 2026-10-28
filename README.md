# Customer Churn & Lifetime Value — Telco

![Python](https://img.shields.io/badge/Python-FFB6C1?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-B5EAD7?style=for-the-badge&logo=pandas&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-C7CEEA?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-FFDAC1?style=for-the-badge&logo=jupyter&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-E2F0CB?style=for-the-badge&logo=sqlite&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-FF9AA2?style=for-the-badge&logo=tableau&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-D4A5A5?style=for-the-badge&logo=github&logoColor=white)

## Dashboard

![Telco Churn Dashboard](docs/dashboard_screenshot.png)


A pipeline that validates raw subscriber data, predicts which customers are
likely to leave, and turns that prediction into a dollar figure: **how much
revenue is actually at risk, and exactly which customers to call first.**

## The business problem

A subscription business (here: a telecom provider) loses customers every
month. Knowing the overall churn rate is nearly useless on its own — what a
retention team actually needs is: *which specific customers, worth how much
money, are about to leave, and why.* Calling every customer is wasted effort;
calling nobody means losing revenue you could have saved.

- **User:** a customer retention / CRM manager deciding where to spend
  limited outreach effort this month.
- **Decision it supports:** which customers to contact first, ranked by
  expected revenue saved, not just by churn probability alone.
- **Success measure:** revenue retained per outreach dollar spent, and how
  many of the highest-value at-risk customers were actually contacted.

## What it found (on the sample data used to build and test this)

On the synthetic test dataset: **model accuracy 81.7%, ROC-AUC 0.919**, catching
**81% of customers who actually churned** (recall). The strongest churn
drivers were **month-to-month contracts, fiber optic internet, and short
tenure** — all of which hold up as real, well-known patterns in this
dataset, not artifacts of the test data. **127 customers landed in the
"High risk" segment, representing ~$77K of projected revenue at stake.**
(Re-run on the real dataset and these numbers will change — see "Running it.")

## How it works

See `docs/pipeline_diagram.md` for the full flow. In short:

1. **Raw** (`data/raw/`) — the untouched Telco export, exactly as downloaded.
2. **Validate** (`validate.py`) — ~10 rules (duplicate rows, missing IDs,
   impossible tenure, invalid categories). One check is worth calling out:
   this dataset has a real, documented quirk where brand-new customers
   (tenure = 0) have a **blank** `TotalCharges` field, because they haven't
   been billed yet. That's flagged as a *warning*, not an error — it's not
   corrupt data, it's an accurate reflection of a customer with no billing
   history. It's fixed to 0 in `transform.py`, not dropped.
3. **Transform** (`transform.py`) — computes `historical_ltv` (what they've
   paid so far) and `projected_ltv` (what an active customer is worth over
   the next 12 months at their current rate), plus a readable tenure bucket.
4. **Explore & compare** (`notebooks/eda_and_model_comparison.ipynb`) —
   before committing to a model, this notebook looks at the actual churn
   patterns (by contract, tenure, charges) and cross-validates logistic
   regression against a decision tree to justify the choice with evidence,
   not just an assertion. See "Design decisions" below for the result.
5. **Model** (`model.py`) — a logistic regression predicts each customer's
   churn probability, scores every customer (not just a test sample), and
   computes `value_at_risk = churn_probability × projected_ltv` — the number
   that actually matters to the business.
6. **Load** (`load.py`) — applies `sql/schema.sql` and loads the scored
   customer table, model metrics, and data-quality logs into the warehouse.
7. **Dashboard** — Tableau connects to the warehouse's views and needs no
   further transformation.

## Data

Built for the [Telco Customer Churn
dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
(IBM sample data, hosted on Kaggle — not included here; download it and
save the CSV as `data/raw/telco_customer_churn.csv`).

To test the pipeline right now without downloading anything, generate a
small fake dataset in the same shape, with the same real-world quirks
planted on purpose:

```bash
pip install -r requirements.txt
python pipeline/generate_sample_data.py
```

## Running it

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get data into data/raw/telco_customer_churn.csv
#    (real Kaggle download, or the sample generator above)

# 3. Set where the warehouse lives (optional — defaults to a local SQLite file)
#    export DB_URL="mysql+pymysql://root:yourpassword@localhost:3306/telco_dw"

# 4. Run the pipeline (validates, trains the model, loads everything)
python pipeline/load.py

# 5. Export a single Excel file for Tableau
python pipeline/export_for_dashboard.py
```

Then point Tableau at `data/telco_churn_dashboard_data.xlsx` and build
visuals straight from its sheets.

## Design decisions (so I can defend them)

- **Why logistic regression, not a more "powerful" model — with evidence,
  not just an assertion:** `notebooks/eda_and_model_comparison.ipynb`
  cross-validates logistic regression against a decision tree on identical
  folds. The tree edges it out on accuracy and ROC-AUC by about a point,
  but logistic regression has meaningfully higher **recall** (86.3% vs
  76.7%) — catches more of the customers who actually churn — while the
  tree has higher precision (92.6% vs 82.5%). For this business problem,
  missing an actual churner (losing that revenue entirely) is a worse
  mistake than one unnecessary retention call, so the higher-recall model
  is the economically correct choice, not just the easier one to explain.
  It also happens to give a coefficient per feature you can read directly
  as "this pushes risk up/down by this much" — a model I can fully defend
  on two independent grounds beats one that scores a point higher on one
  metric.
- **What "churned" actually means here:** the dataset already labels who
  left historically — that part isn't my judgment call. The real judgment
  calls are forward-looking: *(1)* what probability counts as "risky enough
  to act on" (`HIGH_RISK_THRESHOLD = 0.50`, `MEDIUM_RISK_THRESHOLD = 0.25`
  in `config.py`) and *(2)* what time horizon to project value over
  (12 months — long enough to be meaningful, short enough that the
  projection stays credible). Both are visible, named constants, not
  buried magic numbers — a different business could reasonably set these
  differently, and that's a legitimate conversation to have with them.
- **Why value_at_risk, not just churn probability:** a 90%-likely-to-leave
  customer paying $20/month matters less than a 40%-likely-to-leave
  customer paying $150/month. Ranking by probability alone would send a
  retention team after the wrong people.
- **Two LTV numbers, not one:** `historical_ltv` (money already earned) and
  `projected_ltv` (money at stake going forward) answer different
  questions — total value delivered so far, versus what's actually
  recoverable through retention effort today.

## Limits and what I'd test next

- **This is trained on ~1,500-7,000 customers from one point in time** — it
  tells you who looks like past churners *right now*, not how churn risk
  changes over a customer's lifecycle, and it can't see anything outside
  this dataset: a competitor's price cut, a bad support call, a changed
  family budget. Those drive real churn and aren't in these columns.
- **The 0.50 / 0.25 risk thresholds are a starting point, not a tuned
  business answer.** With real outreach-cost and win-back-rate numbers from
  the business, I'd tune these against actual ROI instead of a round number.
- **class_weight="balanced" trades some precision for recall** — it's tuned
  to catch more actual churners at the cost of some false alarms. Whether
  that's the right tradeoff depends on how expensive an outreach call is
  versus how expensive a missed churner is — worth confirming with the
  business, not assuming.
- With the company's real data, I'd add a time dimension (retrain monthly,
  track whether value_at_risk predictions actually prevented churn when
  acted on) instead of treating this as a one-off snapshot.

## Repo structure

```
pipeline/     config.py, validate.py, transform.py, model.py, load.py,
              export_for_dashboard.py, generate_sample_data.py
notebooks/    eda_and_model_comparison.ipynb — exploration + the evidence
              behind the model choice (reuses validate.py/transform.py,
              never duplicates their logic)
sql/          schema.sql — the warehouse tables and Tableau views
data/         raw/ clean/ rejected/ (gitignored — see .gitignore)
logs/         quality_report.csv, table_summary.csv, model_metrics.csv,
              feature_importance.csv, model_comparison.csv (written on each run)
docs/         pipeline_diagram.md
```
