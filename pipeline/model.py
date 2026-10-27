"""
model.py - STEP 3: predict which customers are likely to churn, and turn
that into a dollar figure the business can act on.

Why logistic regression and nothing fancier: this project's brief is
"keep the model simple and explain why, because a simple model you can
defend beats a complex one you can't." Logistic regression gives a churn
PROBABILITY (not just yes/no) and coefficients you can read directly as
"this feature pushes risk up/down by this much" — a random forest or
gradient-boosted model might score a percent or two higher on paper, but
you can't stand in an interview and explain its 200 decision paths. This
can be explained in one sentence per feature.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from config import (
    HIGH_RISK_THRESHOLD, LOG_DIR, MEDIUM_RISK_THRESHOLD, RANDOM_SEED,
)
from transform import build_model_features


def risk_segment(prob):
    if prob >= HIGH_RISK_THRESHOLD:
        return "High"
    if prob >= MEDIUM_RISK_THRESHOLD:
        return "Medium"
    return "Low"


def train_and_score(df):
    X, y, feature_names = build_model_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )

    # Scale features so coefficients are comparable to each other (a
    # feature measured in dollars and one measured 0/1 aren't on the same
    # scale, so their raw coefficients can't be compared without this).
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_SEED)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba_test = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba_test),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "actual_churn_rate": y.mean(),
    }
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    metrics.update({"true_positive": int(tp), "false_positive": int(fp),
                     "true_negative": int(tn), "false_negative": int(fn)})

    # Score EVERY customer (not just the test set) for the dashboard —
    # the test set is for proving the model works, the full scored
    # population is what the business actually acts on.
    X_all_scaled = scaler.transform(X)
    df = df.copy()
    df["churn_probability"] = model.predict_proba(X_all_scaled)[:, 1]
    df["risk_segment"] = df["churn_probability"].apply(risk_segment)

    # The number that matters most to the business: expected revenue at
    # risk = how likely they are to leave x what they're worth if they stay.
    df["value_at_risk"] = np.where(
        df["Churn"] == "No",
        df["churn_probability"] * df["projected_ltv"],
        0.0,
    )

    # Feature importance — standardized coefficients, so magnitude tells you
    # how much pull each feature has (same scale, see StandardScaler above).
    importance = pd.DataFrame({
        "feature": feature_names,
        "coefficient": model.coef_[0],
    })
    importance["abs_coefficient"] = importance["coefficient"].abs()
    importance["direction"] = np.where(importance["coefficient"] > 0, "increases risk", "decreases risk")
    importance = importance.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics]).to_csv(LOG_DIR / "model_metrics.csv", index=False)
    importance.to_csv(LOG_DIR / "feature_importance.csv", index=False)

    return df, metrics, importance


if __name__ == "__main__":
    from transform import transform
    scored, metrics, importance = train_and_score(transform())
    print("Model metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("\nTop 5 churn drivers:")
    print(importance.head(5).to_string(index=False))
    print("\nTop 5 highest value-at-risk customers:")
    print(scored.sort_values("value_at_risk", ascending=False)
          [["customerID", "churn_probability", "risk_segment", "projected_ltv", "value_at_risk"]]
          .head(5).to_string(index=False))
