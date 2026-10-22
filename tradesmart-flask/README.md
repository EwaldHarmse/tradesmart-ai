# TradeSmart AI: web app

One Flask process serves the whole app: pages, the chat, the valuation
model and the database writes. Pages are Jinja2 templates, and the chat
runs on [htmx](https://htmx.org). Every step is a normal form that posts
to Flask, and Flask sends back the updated chat card as HTML.
`static/js/htmx.min.js` is the unmodified library. The only hand-written
JavaScript is a short script in `base.html` that adds thousands
separators to the mileage and deposit boxes as you type.

## Files

```
app.py                 routes: the page, and one /chat/* route per chat step
ml_service.py          loads the XGBoost model and produces the estimate
features.py            feature list shared with tradesmart-ml
condition_nlp.py       turns the condition answer into findings for inspection
db.py                  SQL Server writes (one transaction per completed chat)
submission_log.py      appends each chat step to logs/customer_submissions.csv
templates_content.py   the Jinja2 templates, loaded with jinja2.DictLoader
styles.py              the stylesheet, served at /assets/style.css
data/ models/ outputs/ dataset, trained models and metrics, copied in by
                       tradesmart-ml/src/copy_to_app.py
static/                htmx, background video, images
```

The templates and CSS are kept as strings in `.py` files rather than in
`templates/` and `static/css/`. Flask doesn't care where template text
comes from, so `DictLoader` reads them straight from the dict.

## The chat flow

1. **Vehicle.** Search as you type (`/chat/search`), then pick from the
   list. Only makes/models in the dataset are accepted.
2. **Year and mileage.** The server validates these: the year must be four
   digits from 1950 to next year, and mileage can be written as `85000`,
   `85,000`, `85k` or `85 000 km`.
3. **Condition (optional).** Accident yes/no, plus free text about damage
   and modifications.
4. **Deposit (optional).** A cash deposit towards another car.
5. **Name and contact.** Phone and email are only stored if the POPIA
   consent box is ticked.

The chat state lives in Flask's signed session cookie, so there's no
server-side session store.

## How the estimate works

The model was trained on about 21 features per car (engine size, power,
torque, CO2, seats, body type, ...). A customer won't know most of those.
So `ml_service.py` looks up the typical spec for their exact make/model
in the dataset (median for numbers, most common value for categories).
It then puts in the customer's own year and mileage and runs XGBoost.

The range shown is the estimate ± the model's average error. If the year
is outside the 2018–2023 model years in the training data, the result is
flagged as low confidence instead of being shown as a normal estimate.

## Condition answers

The condition answer never changes the price. The Autotrader data has no
damage information, so the model has nothing to base an adjustment on.
Instead `condition_nlp.py`:

1. splits the answer into separate mentions ("small dent on the door,
   windscreen chip" becomes two) and drops negatives like "no dents";
2. categorises each mention with the classifier from
   `tradesmart-ml/src/nlp_parser.py`;
3. pulls out details with simple rules: dent size ("golf ball" → small,
   "4cm" → medium), type of modification, DIY or professional install;
4. marks a finding for review if the classifier wasn't confident, the
   answer was vague, or it contradicts the accident question.

Each finding becomes a row in `CONDITION_FINDING`.

## Running it

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Settings in `.env`:

| Variable | What it does |
|---|---|
| `DB_ENABLED` | `false` runs without SQL Server; nothing is saved |
| `DB_SERVER`, `DB_NAME`, `DB_DRIVER` | SQL Server connection. Needs "ODBC Driver 17 for SQL Server" |
| `DB_TRUSTED_CONNECTION` / `DB_USER`, `DB_PASSWORD` | Windows auth (default) or SQL auth |
| `SECRET_KEY` | signs the session cookie; a random one is generated if unset |
| `PORT`, `HOST` | defaults `5000` and `127.0.0.1` |
| `FLASK_DEBUG` | `1` turns on the Flask debugger. Only use this locally |
| `NO_BROWSER` | `1` stops the browser opening on start |

## Known limitations

- Only above-the-fold elements animate in. Animating sections as you
  scroll to them needs JavaScript.
- The chat scrolls to the latest message using htmx's `scroll:`/`show:`
  options, which is close to the original behaviour but not exact.
- There's no rate limiting, so it isn't ready to be hosted publicly as is.
