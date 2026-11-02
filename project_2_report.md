# project 2: telco churn prediction

## problem → solution

**problem:** telecom company loses customers every month. they don't know who's leaving until they're already gone.

**solution:** build a machine learning model that predicts churn BEFORE it happens, so the company can act.

---

## how it works

raw customer data (messy) 
→ validate (remove garbage)
→ transform (create signals)
→ model (learn patterns)
→ load (predict & export)
→ manager sees: "1,200 at-risk customers, call them"

---

## the pipeline: what each stage does

| stage | job | output |
|-------|-----|--------|
| **validate** | remove bad data | 9,800 clean rows (from 10,000) |
| **transform** | create features (signals) | 5 features per customer that predict churn |
| **model** | learn from 4,000 old customers | trained model with 85% accuracy on test data |
| **load** | predict on 10,000 current customers | high/medium/low risk groups ready to act |

---

## what i realized building this

**realization 1: features are the difference between blind and seeing**

without features:
```
raw data: signup_date=2023-01-15, bill=$29.99, tickets=12
model: ??? can't see a pattern
```

with features:
```
months_as_customer=24, support_tickets=12, days_inactive=71
model: "i learned this pattern = churn"
```

features turn facts into insights.

**realization 2: test on new data or your model is lying**

if you test on old data the model saw during training:
- model says: "i remember customer 100, they stayed"
- not actually learning, just memorizing

if you test on new data:
- model says: "customer 4,001, i've never seen you, but you match the churn pattern i learned"
- actually learning

train/test split = the difference between memorizing and understanding.

**realization 3: simple beats complex**

could use fancy neural networks. chose logistic regression instead.

why?
- explains itself ("high support tickets matter most for churn")
- works on small data (4,000 customers enough)
- fast (seconds vs hours)
- 85% accuracy is good enough

complex model at 87% accuracy not worth explaining to a manager.

---

## numbers that matter

```
customers analyzed: 10,000
model accuracy: 85%
high-risk identified: 1,200 customers
estimated revenue at risk: $3.6M
revenue saved if 30% retain: $1.1M
cost of automated calls: $50K
net value: $1.05M
```

---

## what the model learned

customers who churn have:
- **high support tickets** (frustrated)
- **long inactive periods** (disengaged)
- **plan downgrades** (losing interest)
- **low spending** (low value = easy to drop)

customers who stay have opposite signals.

---

## if i built this in production

- confirm churn definition with business (60% threshold? 50%? 70%?)
- validate on real data (synthetic data has fake errors)
- automate the pipeline (daily predictions, not manual runs)
- track outcomes (did calling high-risk customers actually save them?)
- iterate the model (feedback improves predictions)

---

## what this shows (interview angle)

**not:** "i trained a model"

**instead:** "i identified that the company loses customers invisibly. i built a system to predict churn with 85% accuracy, identify 1,200 at-risk customers worth $3.6M, and give the company the data to save $1.1M. the model is simple enough to explain to a non-technical manager."

that's the difference between data science and business impact.
