"""
Generates the seed rows for the two vehicle tables in TradeSmartAI_Database.sql:

  dbo.VEHICLE_MODEL - one row per make + model (2,393), holding the typical
                      specs fed into the XGBoost model. These come straight
                      from the web app's own spec lookup (tradesmart-flask/
                      ml_service.py - median of each numeric spec, most common
                      value of each category, per exact make + model), so what
                      the database stores is exactly what the app uses.
  dbo.VEHICLE       - every listing in the corrected Autotrader dataset
                      (16,453), each linked to its VEHICLE_MODEL row.

Run it after the dataset or ml_service.py changes (from this folder):
    python build_vehicle_sql.py
"""

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tradesmart-flask"))
import ml_service  # noqa: E402  (needs the path above)

SQL_PATH = HERE / "TradeSmartAI_Database.sql"
BATCH_SIZE = 1000  # SQL Server's row limit for one multi-row VALUES insert

SECTION_START = "-- Seed data: VEHICLE"
SECTION_END = "-- Seed data: CUSTOMER, VALUATION_SESSION"

# VEHICLE_MODEL column -> spec_by_model column (features.py names)
MODEL_TEXT = {
    "BodyType": "Body Type",
    "Transmission": "Transmission",
    "FuelType": "Fuel Type",
    "DrivenWheels": "Driven wheels",
    "EnginePosition": "Engine position",
    "CylinderLayout": "Cylinder layout and quantity",
    "TypicalPreviousOwners": "Previous Owners",
}
MODEL_NUMBERS = {
    "EngineCapacityL": "Engine capacity (litre)",
    "PowerKW": "Power maximum (detail)",
    "TorqueNm": "Torque maximum",
    "Acceleration0To100Sec": "Acceleration 0-100 km/h",
    "TopSpeedKmh": "Maximum/top speed",
    "FuelConsumptionL100km": "Fuel consumption (average)",
    "FuelCapacityL": "Fuel capacity",
    "CO2EmissionsGKm": "CO2 emissions (average)",
    "Seats": "Seats (quantity)",
    "Doors": "No of doors",
}

# VEHICLE column -> dataset column
LISTING_TEXT = {
    "Transmission": "Transmission",
    "FuelType": "Fuel Type",
    "BodyType": "Body Type",
    "Colour": "Color",
    "PreviousOwners": "Previous Owners",
}
LISTING_TEXT_2 = {
    "CylinderLayout": "Cylinder layout and quantity",
    "DrivenWheels": "Driven wheels",
}
LISTING_NUMBERS = {
    "PowerKW": "Power maximum (detail)",
    "TorqueNm": "Torque maximum",
    "Acceleration0To100Sec": "Acceleration 0-100 km/h",
    "TopSpeedKmh": "Maximum/top speed",
    "FuelConsumptionL100km": "Fuel consumption (average)",
    "CO2EmissionsGKm": "CO2 emissions (average)",
    "Seats": "Seats (quantity)",
    "Doors": "No of doors",
}


def sql_str(value):
    if value is None or pd.isna(value):
        return "NULL"
    return "N'" + str(value).replace("'", "''") + "'"


def sql_num(value):
    return "NULL" if pd.isna(value) else str(round(float(value), 1))


def batched(table, columns, rows):
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    out = []
    for n, batch in enumerate(batches, start=1):
        out.append(f"-- {table}: batch {n} of {len(batches)} ({len(batch)} rows)")
        out.append(f"INSERT INTO dbo.{table} ({', '.join(columns)}) VALUES")
        out.append(",\n".join(batch) + ";")
        out.append("GO")
        out.append("")
    return out


def main():
    # VEHICLE_MODEL, with explicit IDs so each listing can reference its model
    specs = ml_service.service.spec_by_model.sort_index()
    model_ids = {}
    model_rows = []
    for model_id, ((make, model), spec) in enumerate(specs.iterrows(), start=1):
        model_ids[(make, model)] = model_id
        values = [str(model_id), sql_str(make), sql_str(model)]
        values += [sql_str(spec[col]) for col in MODEL_TEXT.values()]
        values += [sql_num(spec[col]) for col in MODEL_NUMBERS.values()]
        values.append(str(int(spec["ModelFrequency"])))
        model_rows.append("(" + ", ".join(values) + ")")

    # VEHICLE: the listings the specs above were summarised from
    df = ml_service.service.df
    listing_rows = []
    for _, r in df.iterrows():
        values = [str(model_ids[(r["Brand"], r["Model"])]), sql_str(r["Brand"]), sql_str(r["Model"]),
                  str(int(r["Year"])), str(int(r["Mileage"])), str(float(r["Price"]))]
        values += [sql_str(r[col]) for col in LISTING_TEXT.values()]
        values.append(sql_num(r["Engine capacity (litre)"]))
        values += [sql_str(r[col]) for col in LISTING_TEXT_2.values()]
        values += [sql_num(r[col]) for col in LISTING_NUMBERS.values()]
        listing_rows.append("(" + ", ".join(values) + ")")

    out = [
        "-- ------------------------------------------------------------------------",
        "-- Seed data: VEHICLE_MODEL and VEHICLE",
        f"-- {len(model_rows)} makes/models with their typical specs, then the",
        f"-- {len(listing_rows)} Autotrader listings they were summarised from, from the",
        "-- corrected dataset. Generated by database/build_vehicle_sql.py - don't",
        "-- edit by hand.",
        "-- ------------------------------------------------------------------------",
        "SET IDENTITY_INSERT dbo.VEHICLE_MODEL ON;",
        "GO",
        "",
    ]
    out += batched("VEHICLE_MODEL", ["ModelID", "Make", "Model", *MODEL_TEXT, *MODEL_NUMBERS, "ListingCount"], model_rows)
    out += ["SET IDENTITY_INSERT dbo.VEHICLE_MODEL OFF;", "GO", ""]
    out += batched("VEHICLE", ["ModelID", "Make", "Model", "VehicleYear", "Mileage", "Price", *LISTING_TEXT,
                               "EngineCapacityL", *LISTING_TEXT_2, *LISTING_NUMBERS], listing_rows)

    sql = SQL_PATH.read_text(encoding="utf-8")
    start = sql.rindex("\n", 0, sql.index(SECTION_START) - 1) + 1  # include the dashed line above
    end = sql.rindex("\n", 0, sql.index(SECTION_END) - 1) + 1
    SQL_PATH.write_text(sql[:start] + "\n".join(out) + "\n" + sql[end:], encoding="utf-8")

    print(f"Wrote {len(model_rows)} VEHICLE_MODEL rows and {len(listing_rows)} VEHICLE rows to {SQL_PATH.name}")


if __name__ == "__main__":
    main()
