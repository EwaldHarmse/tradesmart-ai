# TradeSmart AI: models

Training and evaluation for the valuation models and the condition-text
classifier. The web app only needs the outputs of this folder, which
`src/copy_to_app.py` copies into `tradesmart-flask`.

## Files

```
data/
  autotrader-south-africa-usedcars (cleaned data).csv   as published, 16,456 rows
  autotrader-south-africa-usedcars (corrected).csv      after fix_dataset.py, 16,453 rows
src/
  fix_dataset.py          fixes errors in the published dataset (run first)
  features.py             feature engineering, shared by every model
  train_models.py         depreciation baseline, Linear Regression, Random Forest, XGBoost
  train_deep_learning.py  MLP neural network (Keras)
  tune_xgboost.py         randomized hyperparameter search for XGBoost
  split_experiments.py    accuracy across split ratios, random seeds and training sizes
  time_series_analysis.py depreciation by vehicle age, with figures
  nlp_parser.py           condition-text classifier + rule-based extraction
  copy_to_app.py          copies the model, classifier and data into the web app
models/   saved models
outputs/  metrics (JSON), predictions and figures
```

`models/random_forest.joblib` is about 100MB, which is over GitHub's
file-size limit, so it isn't in the repo. `train_models.py` recreates it.

## Setup and running

Python 3.12 on Windows:

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Then from `src/`, in this order:

```bash
python fix_dataset.py
python train_models.py           # ~5-10 min, Random Forest is the slow part
python train_deep_learning.py    # ~1 min
python nlp_parser.py
python time_series_analysis.py
python split_experiments.py      # a few minutes
python tune_xgboost.py           # optional, ~10 min
python copy_to_app.py
```

If the dataset changes, also rebuild the database seed rows with
`python ..\..\database\build_vehicle_sql.py`.

## Dataset fixes

The data comes from Victor Adewoyin's used-car-price-prediction project
(2023, MIT licence). Its cleaning notebook introduced three errors:

1. **Two-word brands split in half.** "Land Rover Defender" became brand
   "Land", model "Rover Defender". The same happened to Alfa Romeo and
   Aston Martin.
2. **Fuel consumption lost its leading 1.** `str.strip('/100km')` strips
   *characters*, so 11.5 L/100km became 0.5. These are restored where
   tank size ÷ range confirms the real figure, and set to missing where
   it can't be confirmed.
3. **Impossible mileages,** e.g. 990,000 km on a 2018 car. Rows over
   500,000 km are dropped.

## Results

All five models use the same 80/20 split (3,291 test cars). The
cross-validation column is 10-fold, on the training set only.

| Model | MAE (R) | RMSE (R) | R² | 10-fold CV MAE (R) |
|---|---|---|---|---|
| Depreciation baseline | 59,981 | 163,204 | 0.902 | – |
| Linear Regression | 92,169 | 181,580 | 0.879 | 91,281 ± 5,925 |
| Random Forest | 43,196 | 107,392 | 0.958 | 45,683 ± 5,796 |
| **XGBoost (tuned)** | **39,116** | **85,415** | **0.973** | **42,404 ± 4,916** |
| MLP (Keras) | 51,529 | 148,098 | 0.919 | – |

XGBoost is best on every measure, and its model file is ~4MB against
~100MB for Random Forest, so the app uses it. Linear Regression is worse
than the simple depreciation baseline. A straight line can't fit how
differently a R150k hatchback and a R2.5m SUV lose value. The MLP beats
the baseline but not the tree models, which is normal for tabular data
of this size.

**Tuning.** `tune_xgboost.py` ran a randomized search over 40 settings
with 5-fold CV on the training data, then checked the best settings once
on the test set. MAE dropped from R45,607 to R38,967 (−14.6%). Those
settings are now in `train_models.py`. They are rounded there, which is
why the table shows R39,116.

**How much does the split matter?** The 0.973 above comes from one split.
Over 5 random 80/20 splits, R² ranges from 0.86 to 0.95 (average 0.91),
because a few very expensive cars dominate R². The average error is
steadier: R40k–R43k at every split ratio, with about 88% of estimates
within 15% of the real price. The app reports the average (R² 0.91,
MAE R41,905) rather than the best split. The learning curve goes from
R² 0.81 with 1,000 training cars to 0.97 with all 13,162.

**Depreciation.** `time_series_analysis.py` compares the same model
across model years. Cars keep about 92% of their value after one year
and 62% after five, which is roughly 9.5% a year. Bakkies lose value
more slowly (6–9%) and sedans faster (~11%). It fits an exponential
curve rather than a seasonal forecast like Prophet or ARIMA, since the
data is a single snapshot in time.

**Feature importance.** Both tree models rank engine power and torque
highest, ahead of mileage and age (`outputs/model_comparison.json`).

## Condition classifier

TF-IDF + logistic regression over 102 example answers across 8
categories (dents, windscreen, respray, mods, accident, service history,
no issues, unclear). There are no real customer transcripts yet, so the
examples were written by hand. About a fifth of them are short fragments
like "aftermarket rims", because that's how people actually fill in the
chat's text boxes.

Held-out accuracy is 96%, but the test split is only 26 examples, so
treat that as a rough figure. Around the classifier, rules extract dent
size, modification type and install quality, and flag vague or
contradictory answers. `outputs/nlp_demo_results.json` shows the output
for ten example answers.
