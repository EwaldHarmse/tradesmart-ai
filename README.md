# TradeSmart AI

A trade-in valuation chatbot for a used-car dealership. The customer picks
their car, gives the year and mileage, describes its condition, and gets an
estimated trade-in value from an XGBoost model trained on ~16,000 real
Autotrader South Africa listings.

Built as a third-year project at VUT.

## What it does

- **Valuation.** XGBoost regression on make/model, year and mileage, plus
  the typical specs for that model (engine size, power, torque, body type
  and so on) looked up from the dataset. Average error is about R42,000,
  and R² averages 0.91 over five random 80/20 splits.
- **Condition notes (NLP).** The customer's free-text answer about dents,
  accidents, windscreen damage or modifications is split into separate
  mentions and categorised with a TF-IDF + logistic regression classifier.
  Rules then pull out details like dent size or who fitted a modification.
  These go to the database as things to check at inspection. They don't
  change the price, because the training data has no condition information.
- **Database.** A SQL Server schema with six tables: listings, models,
  customers, valuation sessions, condition findings and categories.
  Contact details are only stored if the customer consents (POPIA).
- **Model comparison.** A depreciation baseline, Linear Regression, Random
  Forest, XGBoost and an MLP neural network are trained and evaluated on
  the same split. XGBoost had the best results and is the one the app uses.

## Tech

Python, Flask, Jinja2, htmx, scikit-learn, XGBoost, TensorFlow/Keras,
spaCy, pandas, SQL Server (pyodbc).

## Repository layout

```
tradesmart-flask/   the web app: Flask routes, chat flow, valuation service, NLP, DB access
tradesmart-ml/      dataset fixes, training and evaluation for every model
database/           SQL Server schema + seed data, ERD, script that builds the seed rows
documentation/      project write-up and poster
```

Each of the first two folders has its own README with more detail.

## Running it

You need Python 3.12 on Windows. SQL Server is optional.

```bash
cd tradesmart-flask
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

The app opens at http://localhost:5000/. To try it without SQL Server, set
`DB_ENABLED=false` in `.env`. The valuation still works, but nothing is
saved. To use the database, run `database/TradeSmartAI_Database.sql` in
SSMS first and set `DB_SERVER` in `.env`. On Windows you can also just
double-click `Start TradeSmart AI.bat`, which sets up the venv the first time.

## Data

The dataset comes from Victor Adewoyin's
[used-car-price-prediction](https://github.com/vaadewoyin/used-car-price-prediction)
project (2023, MIT licence), which scraped Autotrader South Africa. Its
published CSV has three cleaning errors (split brand names, fuel
consumption figures missing a digit, and a few impossible mileages).
`tradesmart-ml/src/fix_dataset.py` corrects them before anything is trained.
