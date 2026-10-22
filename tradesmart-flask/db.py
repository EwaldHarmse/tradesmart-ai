"""
TradeSmart AI backend - SQL Server data access layer.

All the actual T-SQL lives here, isolated from app.py and ml_service.py,
for two reasons:
  1. Every INSERT here has to match TradeSmartAI_Database.sql's schema
     exactly (column names, NOT NULL constraints, FK requirements) -
     keeping it in one file makes that easy to audit against the .sql
     script if the schema ever changes.
  2. Set DB_ENABLED=false (see .env.example) to run the rest of the
     backend - the ML/NLP logic, the chat flow, the frontend - without
     a SQL Server connection at all. With DB_ENABLED=false, IDs are fake
     (in-memory counters) and nothing is written to a database - useful
     for a dry run before wiring up the real connection string.

What a completed chat writes, matching the schema's relationships:
    CUSTOMER          - who asked
    VALUATION_SESSION - their car + the predicted price, linked to that
                        CUSTOMER and to the VEHICLE_MODEL row for the
                        make/model they picked
    CONDITION_FINDING - each condition mention, linked to the session
All three are written together by save_valuation(), in one transaction.
VEHICLE (the 16,453 listings), VEHICLE_MODEL and CONDITION_CATEGORY are
reference tables, filled once by the .sql script.

Setup on your PC: install the "ODBC Driver 17 for SQL Server" from
Microsoft (see README.md), then set DB_SERVER / DB_TRUSTED_CONNECTION
(or DB_USER/DB_PASSWORD) in a .env file copied from .env.example.
"""

import itertools
import os


DB_ENABLED = os.environ.get("DB_ENABLED", "true").lower() not in ("false", "0", "no")

DB_SERVER = os.environ.get("DB_SERVER", r"localhost\SQLEXPRESS")
DB_NAME = os.environ.get("DB_NAME", "TradeSmartAI")
DB_DRIVER = os.environ.get("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_TRUSTED_CONNECTION = os.environ.get("DB_TRUSTED_CONNECTION", "yes")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")


def _build_connection_string() -> str:
    parts = [f"DRIVER={{{DB_DRIVER}}}", f"SERVER={DB_SERVER}", f"DATABASE={DB_NAME}"]
    if DB_USER:
        parts.append(f"UID={DB_USER}")
        parts.append(f"PWD={DB_PASSWORD}")
    else:
        parts.append(f"Trusted_Connection={DB_TRUSTED_CONNECTION}")
    return ";".join(parts) + ";"


def get_connection():
    """Only imports pyodbc when actually needed, so DB_ENABLED=false
    environments (e.g. without the ODBC driver installed) never need
    pyodbc importable at all."""
    import pyodbc
    return pyodbc.connect(_build_connection_string())


# In-memory ID counters used when DB_ENABLED=false.
_fake_customer_ids = itertools.count(1)
_fake_session_ids = itertools.count(1)


def save_valuation(full_name: str, contact_number: str, email: str, popia_consent: bool,
                   make: str, model: str, year: int, mileage: int,
                   valuation: dict, deposit_amount, findings: list) -> tuple:
    """Writes one completed chat - CUSTOMER, then VALUATION_SESSION, then a
    CONDITION_FINDING per finding - in a single transaction, so a failure
    part-way leaves nothing behind instead of a customer with no session.
    Returns (customer_id, session_id)."""
    if not DB_ENABLED:
        return next(_fake_customer_ids), next(_fake_session_ids)

    conn = get_connection()
    try:
        cur = conn.cursor()
        customer_id = _insert_customer(cur, full_name, contact_number, email, popia_consent)
        session_id = _insert_session(cur, customer_id, make, model, year, mileage, valuation, deposit_amount)
        for finding in findings:
            _insert_finding(cur, session_id, finding)
        conn.commit()
        return customer_id, session_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _insert_customer(cur, full_name, contact_number, email, popia_consent) -> int:
    cur.execute(
        """
        INSERT INTO dbo.CUSTOMER (FullName, ContactNumber, Email, POPIAConsentGiven)
        OUTPUT INSERTED.CustomerID
        VALUES (?, ?, ?, ?)
        """,
        full_name, contact_number, email, 1 if popia_consent else 0,
    )
    return cur.fetchone()[0]


def _insert_session(cur, customer_id, make, model, year, mileage, valuation, deposit_amount) -> int:
    """valuation is ml_service.service.estimate()'s result. The VEHICLE_MODEL
    row is found by make + model (unique in that table) - the vehicle search
    lists exactly the makes/models VEHICLE_MODEL was built from."""
    cur.execute(
        """
        INSERT INTO dbo.VALUATION_SESSION
            (CustomerID, ModelID, VehicleYear, Mileage,
             EstimatedValue, EstimatedValueLow, EstimatedValueHigh,
             ValuationModelUsed, OutsideTrainingYears, DesiredCashDeposit)
        OUTPUT INSERTED.SessionID
        SELECT ?, v.ModelID, ?, ?, ?, ?, ?, ?, ?, ?
        FROM dbo.VEHICLE_MODEL v
        WHERE v.Make = ? AND v.Model = ?
        """,
        customer_id, int(year), int(mileage),
        valuation["point_estimate"], valuation["estimated_low"], valuation["estimated_high"],
        valuation["model_used"], 1 if valuation["out_of_range"] else 0, deposit_amount,
        make, model,
    )
    row = cur.fetchone()
    if row is None:
        raise LookupError(f"No VEHICLE_MODEL row for {make} {model} - re-run build_vehicle_sql.py and the .sql script.")
    return row[0]


def _insert_finding(cur, session_id, finding) -> None:
    """One row in dbo.CONDITION_FINDING - finding is one of the dicts
    condition_nlp.analyser.analyse() returns."""
    cur.execute(
        """
        INSERT INTO dbo.CONDITION_FINDING
            (SessionID, CategoryCode, CustomerText, ExtractedDetail, DetectedBy,
             Confidence, NeedsReview, ReviewReason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        session_id, finding["category"], finding["customer_text"][:500],
        finding["detail"], finding["detected_by"], finding["confidence"],
        1 if finding["needs_review"] else 0, finding["review_reason"],
    )
