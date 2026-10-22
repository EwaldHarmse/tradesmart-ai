"""
TradeSmart AI - a running record of what every customer submitted.

Customers don't log in, so each time anyone presses Send / Continue /
Skip / Get my estimate in the chat, one row is appended to
logs/customer_submissions.csv - which opens directly in Excel. A ChatID
ties together the rows from one person's chat; the final row also carries
the SessionID it was saved under in VALUATION_SESSION.

Two practical details:
- Excel locks a CSV while it's open, so a write can fail. That's logged as
  a warning and the customer's chat carries on - the log must never break
  the valuation itself.
- POPIA: phone/email are only written here if the customer consented,
  the same rule as the CUSTOMER table (see app.py's chat_contact()).
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "logs" / "customer_submissions.csv"
COLUMNS = ["Timestamp", "ChatID", "SessionID", "Step", "CustomerInput", "BotReply"]

logger = logging.getLogger(__name__)


def _excel_safe(text):
    """Excel runs a cell starting with = + - @ as a formula, so a customer
    typing e.g. =HYPERLINK(...) would get it executed when the log is opened.
    A leading apostrophe makes Excel show it as plain text instead."""
    text = str(text)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def log_submission(chat_id, step, customer_input, bot_reply="", session_id=None):
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), chat_id,
           session_id if session_id is not None else "", step,
           _excel_safe(customer_input), _excel_safe(bot_reply)]
    try:
        LOG_PATH.parent.mkdir(exist_ok=True)
        is_new = not LOG_PATH.exists()
        # utf-8-sig: the byte-order mark tells Excel it's UTF-8, so "·" and
        # names with accents display correctly (only written at the start).
        with open(LOG_PATH, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(COLUMNS)
            writer.writerow(row)
    except OSError as exc:
        logger.warning("Couldn't write to %s (is it open in Excel?): %s", LOG_PATH.name, exc)
