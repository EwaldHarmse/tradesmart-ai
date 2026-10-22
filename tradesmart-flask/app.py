"""
TradeSmart AI - Flask + Jinja2 frontend and API, in one process.

This is the "100% Python frontend" version of the project: the old
tradesmart-aura React app (TypeScript + Vite + Tailwind + Framer Motion,
built into a JS bundle) is gone. Every page is a Jinja2 template rendered
by Flask, every bit of visual polish is plain CSS, and the chat demo's
step-by-step interactivity runs through htmx (static/js/htmx.min.js - a
small, off-the-shelf library, not a framework, and the one piece of this
project that isn't ours - see .gitattributes) sending plain HTML forms
back to this server. The only hand-written JavaScript is a few lines in
base.html that put thousands separators into the mileage/deposit boxes.

The markup and CSS themselves are stored as plain Python string constants
- templates_content.py's TEMPLATES dict and styles.py's STYLE_CSS - rather
than as separate .html/.css files, and wired into Flask/Jinja just below
via jinja2.DictLoader. See those two modules' docstrings for why; nothing
about how the pages render changed, only where the source text lives.

The ML/data layer is untouched from the original backend - ml_service.py,
features.py and db.py are the same modules the React version talked to
over a JSON API, doing the same job here. The only thing that changed is
*how the browser gets its HTML*: instead of an API returning JSON that a
React component turns into DOM nodes, these Flask routes return rendered
HTML directly (either a full page, or - for htmx requests - just the
`chat-card` fragment that needs to change).

Chat state (the conversation so far, which step we're on, the vehicle the
customer picked, etc.) lives in the signed Flask session cookie - there is
no server-side session store to run or configure.

Run it exactly like the original backend:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000/
"""

import os
import re
import secrets
import uuid
import webbrowser
from datetime import datetime
from threading import Timer

from flask import Flask, request, render_template, session, Response
from jinja2 import DictLoader

from dotenv import load_dotenv
load_dotenv()

import ml_service
import db
import condition_nlp
from submission_log import log_submission
from templates_content import TEMPLATES
from styles import STYLE_CSS

app = Flask(__name__)
# No SECRET_KEY in .env -> a random one per run, so nobody can forge the
# session cookie with a key that's published in the source code.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
# CSRF: every form is posted by htmx from this same site, so SameSite=Lax
# stops another website from posting into a visitor's chat with their cookie.
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# The chat forms are a few short text fields - refuse oversized request bodies.
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

# Templates are supplied from the TEMPLATES dict (templates_content.py)
# instead of Flask's normal *.html-files-on-disk loader - see that module's
# docstring for why. Every render_template(...)/{% include %}/{% extends %}
# name below is completely unaffected: DictLoader is a drop-in replacement
# for the filesystem loader, keyed by the exact same template-name strings.
app.jinja_loader = DictLoader(TEMPLATES)


# The model years the training data covers (2018-2023), read from the data
# itself - shown to the customer up front, since older/newer cars only get
# a low-confidence estimate (see ml_service.estimate()).
MODEL_YEARS = (f"{ml_service.service.oldest_model_year_in_data}-"
               f"{ml_service.service.newest_model_year_in_data}")


@app.context_processor
def inject_template_globals():
    return {"condition_names": condition_nlp.CATEGORY_NAMES, "model_years": MODEL_YEARS}


STEP_ORDER = ["vehicle", "details", "condition", "deposit", "contact"]
TOTAL_STEPS = len(STEP_ORDER)

INITIAL_BOT_MESSAGE = (
    f"Hi! Let's get an estimate for your trade-in. This works for {MODEL_YEARS} "
    "model years. Start typing your vehicle's make and model below."
)


CONDITION_QUESTION = (
    "Has it been in any accidents, and does it have any dents, windscreen damage, "
    "respray work, or aftermarket mods?"
)


def condition_reply(findings):
    """The bot's answer to the condition step, telling the customer what the
    NLP picked out - and that it's recorded for inspection, not priced."""
    if not findings:
        return "Thanks - nothing there to note for the inspection."
    return (
        f"Thanks - I've noted for the inspection: {condition_nlp.summary_text(findings)}. "
        "These don't change your estimate; they're checked when the car is inspected."
    )


# "45000", "45,000", "45 000", "45k", "85000 km", "R20 000", "20,000.00"
AMOUNT_PATTERN = re.compile(
    r"^\s*r?\s*(\d{1,3}(?:[ ,]\d{3})+|\d+(?:\.\d+)?)(?:\.\d+)?\s*(k)?\s*(?:km|kms|kilometres|kilometers)?\s*$",
    re.IGNORECASE,
)
OLDEST_YEAR = 1950
MAX_MILEAGE = 1_000_000
MAX_DEPOSIT = 10_000_000

# Same limits as the CUSTOMER columns in TradeSmartAI_Database.sql, so a
# long answer can't make the database insert fail.
MAX_NAME = 100
MAX_PHONE = 20
MAX_EMAIL = 100


def parse_amount(text):
    """A whole-number amount the way people actually type it, or None if it
    can't be read. The customer's input is checked at the step where they
    type it, so a bad value never reaches the valuation."""
    m = AMOUNT_PATTERN.match(text or "")
    if not m:
        return None
    value = float(re.sub(r"[ ,]", "", m.group(1)))
    if m.group(2):
        value *= 1000
    return int(round(value))


def parse_year(text):
    text = (text or "").strip()
    if not re.fullmatch(r"\d{4}", text):
        return None
    year = int(text)
    return year if OLDEST_YEAR <= year <= datetime.now().year + 1 else None


def format_clock(dt=None):
    """'Wed May 6 1:09 PM' - built by hand instead of one strftime format
    string because the %-d / %-I "no leading zero" flags aren't portable
    to Windows, which is where this app actually runs."""
    dt = dt or datetime.now()
    hour_12 = dt.strftime("%I").lstrip("0") or "12"
    return f"{dt.strftime('%a %b')} {dt.day} {hour_12}:{dt.strftime('%M %p')}"


# ---------------------------------------------------------------------
# Chat session state
#
# Everything the old ChatDemo.tsx kept in React `useState` now lives in
# the signed session cookie instead - small, plain-Python dictionaries,
# not JSON sent to a client-side store.
# ---------------------------------------------------------------------
def _fresh_chat():
    return {
        "chat_id": uuid.uuid4().hex[:8],  # ties this chat's rows together in the submissions log
        "messages": [{"from": "bot", "text": INITIAL_BOT_MESSAGE}],
        "step": "vehicle",
        "selected_vehicle": None,
        "vehicle_year": "",
        "vehicle_mileage": "",
        "condition_answer": None,    # what the customer typed, as one line (None = skipped)
        "condition_findings": [],    # condition_nlp findings - recorded for inspection, not priced
        "deposit_amount": None,
        "result": None,
        "error_text": None,
    }


def get_chat():
    if "chat" not in session or "chat_id" not in session["chat"]:
        session["chat"] = _fresh_chat()
    return session["chat"]


def save_chat(chat):
    session["chat"] = chat


def push_bot(chat, text):
    chat["messages"].append({"from": "bot", "text": text})


def push_user(chat, text):
    chat["messages"].append({"from": "user", "text": text})


def log_step(chat, step, customer_input, bot_reply=None):
    """One row in the submissions CSV for what the customer just submitted,
    with the bot's reply to it (by default its latest message)."""
    if bot_reply is None:
        bot_reply = next((m["text"] for m in reversed(chat["messages"]) if m["from"] == "bot"), "")
    log_submission(chat["chat_id"], step, customer_input, bot_reply)


def render_state(chat):
    """Chat dict plus the derived progress-bar fields the template needs -
    a plain-Python equivalent of the `activeIndex`/`progressStep`/
    `progressPct` calculations that used to run in the React component."""
    state = dict(chat)
    if chat["step"] in ("loading", "done", "error"):
        active_index = TOTAL_STEPS - 1
    else:
        active_index = STEP_ORDER.index(chat["step"])
    progress_step = min(active_index + 1, TOTAL_STEPS)
    progress_pct = 100 if chat["step"] == "done" else round(progress_step / TOTAL_STEPS * 100)
    state["progress_step"] = progress_step
    state["progress_pct"] = progress_pct
    state["total_steps"] = TOTAL_STEPS
    return state


def chat_fragment():
    """Every /chat/* route ends by re-rendering just the chat card, which
    htmx swaps back into the page (hx-target="#chat-panel")."""
    return render_template("chat/panel.html", chat=render_state(get_chat()))


# ---------------------------------------------------------------------
# Valuation - same steps app.py's /api/valuation/estimate used to run,
# just called as a normal Python function instead of over HTTP.
# ---------------------------------------------------------------------
def run_valuation(full_name, contact_number, email, popia_consent,
                   brand, model, year, mileage, deposit_amount, condition_findings):
    # The estimate uses make/model, year and mileage only. Anything the
    # customer said about the car's condition is saved below as findings
    # to check at inspection - it never moves the price.
    valuation = ml_service.service.estimate(brand, model, year, mileage)

    customer_id = None
    session_id = None
    db_warning = None
    try:
        customer_id, session_id = db.save_valuation(
            full_name=full_name,
            contact_number=contact_number if popia_consent else None,
            email=email if popia_consent else None,
            popia_consent=popia_consent,
            make=brand, model=model, year=year, mileage=mileage,
            valuation=valuation, deposit_amount=deposit_amount,
            findings=condition_findings,
        )
    except Exception:
        # Full error goes to the terminal only - the customer just gets a
        # plain message, not internal details about the database.
        app.logger.exception("Database write failed")
        customer_id = None
        session_id = None
        db_warning = (
            "Your estimate is shown below, but it couldn't be saved right now."
        )

    response = {
        "sessionId": session_id,
        "customerId": customer_id,
        "valuation": valuation,
        "disclaimer": (
            "This is an AI-generated first-pass estimate for your reference, "
            "not a final offer."
        ),
    }
    if db_warning:
        response["dbWarning"] = db_warning
    return response


# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------
@app.get("/")
def index():
    # A fresh visit starts a fresh conversation, same as the old page
    # reload used to reset React's in-memory state.
    save_chat(_fresh_chat())
    return render_template("index.html", chat=render_state(get_chat()), now_text=format_clock())


@app.get("/health")
def health():
    return {"status": "ok", "dbEnabled": db.DB_ENABLED}


@app.get("/assets/style.css")
def style_css():
    """Serves STYLE_CSS (styles.py) - the stylesheet, stored as a Python
    string rather than a static .css file. Same bytes a browser would get
    from a normal static file, just with the Content-Type set by hand
    since this isn't going through Flask's static-file handler."""
    return Response(STYLE_CSS, mimetype="text/css")


@app.get("/clock")
def clock():
    """Polled by the menu-bar clock every 30s (see menu_bar_strip.html) so
    it shows the real, current time instead of a hardcoded string - no
    JavaScript involved, just htmx re-fetching this tiny route."""
    return format_clock()


# ---------------------------------------------------------------------
# Chat steps (all htmx endpoints - each returns the chat-card fragment)
# ---------------------------------------------------------------------
@app.get("/chat/search")
def chat_search():
    query = request.args.get("q", "")
    results = ml_service.service.search_vehicles(query, limit=10) if query.strip() else []
    return render_template("chat/vehicle_results.html", results=results)


@app.post("/chat/vehicle")
def chat_vehicle():
    chat = get_chat()
    if chat["step"] != "vehicle":
        return chat_fragment()

    brand = request.form.get("brand", "").strip()
    model = request.form.get("model", "").strip()
    # Only a make/model from the search list - anything else would be
    # priced off a brand or market average without the customer knowing.
    if not ml_service.service.is_known_vehicle(brand, model):
        return chat_fragment()
    label = f"{brand} {model}"

    chat["selected_vehicle"] = {"brand": brand, "model": model, "label": label}
    push_user(chat, label)
    chat["step"] = "details"
    push_bot(chat, f"Thanks. What year is it ({MODEL_YEARS}), and roughly how many kilometres has it done?")
    log_step(chat, "Vehicle", label)
    save_chat(chat)
    return chat_fragment()


@app.post("/chat/details")
def chat_details():
    chat = get_chat()
    if chat["step"] != "details":
        return chat_fragment()

    year_text = request.form.get("year", "").strip()
    mileage_text = request.form.get("mileage", "").strip()
    if not year_text or not mileage_text:
        return chat_fragment()

    year = parse_year(year_text)
    mileage = parse_amount(mileage_text)
    if year is None or mileage is None or mileage > MAX_MILEAGE:
        push_user(chat, f"{year_text} - {mileage_text}")
        if year is None:
            push_bot(chat, f"Please enter the year as four digits between {OLDEST_YEAR} and "
                           f"{datetime.now().year + 1}, e.g. 2019.")
        else:
            push_bot(chat, "I couldn't read that mileage - try something like 85000, 85,000 or 85k.")
        log_step(chat, "Year and mileage (not accepted)", f"{year_text}, {mileage_text}")
        save_chat(chat)
        return chat_fragment()

    chat["vehicle_year"] = year
    chat["vehicle_mileage"] = mileage
    push_user(chat, f"{year} - {mileage:,} km")
    chat["step"] = "condition"
    push_bot(chat, CONDITION_QUESTION + " Let me know, or skip this.")
    log_step(chat, "Year and mileage", f"{year}, {mileage:,} km")
    save_chat(chat)
    return chat_fragment()


@app.post("/chat/condition")
def chat_condition():
    chat = get_chat()
    if chat["step"] != "condition":
        return chat_fragment()

    action = request.form.get("action", "skip")
    if action == "continue":
        accident = request.form.get("accident", "no")
        damage_text = request.form.get("damage", "").strip()
        mods_text = request.form.get("mods", "").strip()
        summary_bits = ["Accident: yes" if accident == "yes" else "Accident: no"]
        if damage_text:
            summary_bits.append(f"Damage/paint: {damage_text}")
        if mods_text:
            summary_bits.append(f"Mods: {mods_text}")
        findings = condition_nlp.analyser.analyse(accident, damage_text, mods_text)
        chat["condition_answer"] = " · ".join(summary_bits)
        chat["condition_findings"] = findings
        push_user(chat, chat["condition_answer"])
        push_bot(chat, condition_reply(findings))
    else:
        chat["condition_answer"] = None
        chat["condition_findings"] = []
        push_user(chat, "Skipped")

    chat["step"] = "deposit"
    push_bot(chat, "Would you like to add a cash deposit toward another vehicle? Enter an amount, or skip.")
    # Log the NLP's reply ("I've noted for the inspection: ..."), not the deposit question after it
    log_step(chat, "Condition", chat["condition_answer"] or "Skipped",
             condition_reply(chat["condition_findings"]) if chat["condition_answer"] else "")
    save_chat(chat)
    return chat_fragment()


@app.post("/chat/deposit")
def chat_deposit():
    chat = get_chat()
    if chat["step"] != "deposit":
        return chat_fragment()

    action = request.form.get("action", "skip")
    amount = request.form.get("amount", "").strip()

    deposit = None
    if action == "add" and amount:
        deposit = parse_amount(amount)
        if deposit is None or deposit > MAX_DEPOSIT:
            push_user(chat, amount)
            push_bot(chat, "I couldn't read that amount - try something like 20000 or R20 000, or press Skip.")
            log_step(chat, "Deposit (not accepted)", amount)
            save_chat(chat)
            return chat_fragment()

    deposit = deposit or None  # "0" means no deposit
    chat["deposit_amount"] = deposit
    push_user(chat, f"R{deposit:,} deposit" if deposit else "No deposit")
    chat["step"] = "contact"
    push_bot(chat, "Last thing - what's your name? Contact details are optional and only stored if you consent (POPIA).")
    log_step(chat, "Deposit", f"R{deposit:,}" if deposit else "No deposit")
    save_chat(chat)
    return chat_fragment()


@app.post("/chat/contact")
def chat_contact():
    chat = get_chat()
    if chat["step"] != "contact":
        return chat_fragment()

    full_name = request.form.get("fullName", "").strip()[:MAX_NAME]
    contact_number = request.form.get("contactNumber", "").strip()[:MAX_PHONE] or None
    email = request.form.get("email", "").strip()[:MAX_EMAIL] or None
    popia_consent = request.form.get("popiaConsent") == "true"

    if not full_name or not chat.get("selected_vehicle"):
        return chat_fragment()

    push_user(chat, full_name)

    vehicle = chat["selected_vehicle"]
    try:
        year = chat["vehicle_year"]
        mileage = chat["vehicle_mileage"]
        result = run_valuation(
            full_name=full_name, contact_number=contact_number, email=email,
            popia_consent=popia_consent,
            brand=vehicle["brand"], model=vehicle["model"], year=year, mileage=mileage,
            deposit_amount=chat["deposit_amount"],
            condition_findings=chat["condition_findings"],
        )
        v = result["valuation"]
        push_bot(chat, (
            f"Thanks - based on this, your estimated trade-in value is "
            f"R{v['estimated_low']:,.0f}-R{v['estimated_high']:,.0f}."
        ))
        chat["result"] = result
        chat["step"] = "done"
    except Exception:
        app.logger.exception("Valuation failed")
        chat["error_text"] = (
            "Sorry, something went wrong working out your estimate. Please try again."
        )
        chat["step"] = "error"

    # POPIA: contact details only go into the log with consent, like CUSTOMER.
    contact = f" · {contact_number or '-'} · {email or '-'}" if popia_consent else " (no POPIA consent - contact details not stored)"
    session_id = chat["result"]["sessionId"] if chat["step"] == "done" else None
    reply = chat["error_text"] if chat["step"] == "error" else chat["messages"][-1]["text"]
    log_submission(chat["chat_id"], "Contact + estimate", full_name + contact, reply, session_id)
    save_chat(chat)
    return chat_fragment()


@app.post("/chat/retry")
def chat_retry():
    chat = get_chat()
    if chat["step"] == "error":
        chat["step"] = "contact"
        chat["error_text"] = None
        save_chat(chat)
    return chat_fragment()


@app.post("/chat/restart")
def chat_restart():
    save_chat(_fresh_chat())
    return chat_fragment()


def _open_browser(port):
    webbrowser.open(f"http://localhost:{port}/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true" and not os.environ.get("NO_BROWSER"):
        Timer(1.0, _open_browser, args=(port,)).start()
    # localhost only, debugger off: Flask's debugger runs any Python code
    # typed into its error page, so it must never be reachable from the
    # network. Set FLASK_DEBUG=1 in .env to turn it on while developing.
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=port, debug=debug)
