"""
TradeSmart AI backend - ML valuation service.

Loads the trained XGBoost pipeline (models/xgboost_model.joblib - chosen
over Random Forest for serving because it scored best on RMSE/R2 in
tradesmart-ml's evaluation AND is a ~4MB file instead of ~100MB) and
exposes the functions app.py's routes call.

The price only uses make/model/year/mileage - exactly the inputs the
model was trained on. Condition details (dents, accidents, respray,
mods) never move it: the Autotrader dataset is market listings with no
damage history, so the model has no basis to price a "small dent". The
chat still asks about condition, but condition_nlp.py records those
answers for the inspection instead of feeding them in here.

--- Why this needs a "spec lookup" step, not just a form -------------
The trained model expects ~21 features per vehicle (engine capacity,
torque, CO2 emissions, top speed, seats, doors, drive wheels, etc. -
see tradesmart-ml/src/features.py). A real trade-in customer chatting
with the assistant does not know their car's torque figure or CO2
rating. They know: the make/model, the year, the mileage, and roughly
what condition it's in.

So exactly like a human sales consultant would draw on their own
knowledge of "what a 2019 Polo Vivo Hatch 1.4 Trendline is typically
equipped with," this service looks up the *typical* spec for the
customer's exact make/model from the real Autotrader listings data
(median for numeric specs, most-common value for categorical specs),
and only overrides the two things that actually vary per individual
car and that the customer DOES know: the vehicle's age (from the year
they give) and its mileage. That combined feature row is what actually
goes into the model.

This is also why the chat flow asks the customer to pick their exact
make/model from a search list (see /chat/search in app.py)
rather than free-typing it - the lookup needs an exact match against
the training data to find a spec profile.
"""

import json

import joblib
import pandas as pd

from features import (
    load_raw, NUMERIC_FEATURES, CATEGORICAL_FEATURES, NEWEST_MODEL_YEAR, PROJECT_ROOT,
)

MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


class ValuationService:
    def __init__(self):
        self.pipeline = joblib.load(MODELS_DIR / "xgboost_model.joblib")

        self.df = load_raw()
        self.df["VehicleAge"] = NEWEST_MODEL_YEAR - self.df["Year"] + 1
        self.df["ModelFrequency"] = self.df.groupby("Model")["Model"].transform("count")
        self.df["Previous Owners"] = self.df["Previous Owners"].astype(str)

        # A single lookup table: one row per exact (Brand, Model), with the
        # median of every numeric feature and the most-common value of
        # every categorical feature for that exact model string.
        agg = {}
        for col in NUMERIC_FEATURES:
            if col in ("VehicleAge",):
                continue  # overridden per-request from the customer's stated year
            agg[col] = "median"
        for col in CATEGORICAL_FEATURES:
            agg[col] = lambda s: s.mode().iloc[0] if not s.mode().empty else None
        agg["ModelFrequency"] = "first"

        self.spec_by_model = self.df.groupby(["Brand", "Model"]).agg(agg)
        self.spec_by_brand = self.df.groupby("Brand").agg(agg)
        self.spec_global = self.df.agg(
            {**{c: "median" for c in agg if c in NUMERIC_FEATURES},
             **{c: (lambda s: s.mode().iloc[0]) for c in agg if c in CATEGORICAL_FEATURES},
             "ModelFrequency": "median"}
        )

        # Distinct (Brand, Model) pairs for the search-as-you-type endpoint.
        self.known_vehicles = (
            self.df[["Brand", "Model"]].drop_duplicates().sort_values(["Brand", "Model"])
        )

        # Accuracy shown to the customer, and the +/- margin of the range.
        # Measured, not invented: the average over 5 random 80/20 splits from
        # tradesmart-ml/src/split_experiments.py. A single split can flatter
        # the model - R^2 swings from 0.86 to 0.95 depending on which few
        # very expensive cars land in the test set - so the average is the
        # honest figure. Falls back to the one-split result if the
        # experiment hasn't been run.
        splits_path = OUTPUTS_DIR / "split_experiments.json"
        if splits_path.exists():
            with open(splits_path) as f:
                row = next(r for r in json.load(f)["split_ratio"] if r["train_pct"] == 80)
            self.point_error_margin = row["MAE"]["mean"]
            self.model_r2 = row["R2"]["mean"]
            self.accuracy_basis = "average R² over 5 random test splits"
        else:
            with open(OUTPUTS_DIR / "model_comparison.json") as f:
                report = json.load(f)
            self.point_error_margin = report["test_results"]["XGBoost"]["MAE"]
            self.model_r2 = report["test_results"]["XGBoost"]["R2"]
            self.accuracy_basis = "test-set R²"

        # The Autotrader dataset behind this model is entirely 2018-2023
        # model years (nothing older, no exceptions - every brand/model).
        # XGBoost can't extrapolate past what it saw in training: asked
        # about an older/newer vehicle than that, it silently produces a
        # number anyway, and that number is not trustworthy (it's the
        # nearest training leaf, not a real depreciation curve). estimate()
        # below checks every request against these bounds and flags it
        # rather than presenting an extrapolated guess as a normal result.
        self.min_vehicle_age = int(self.df["VehicleAge"].min())
        self.max_vehicle_age = int(self.df["VehicleAge"].max())
        self.oldest_model_year_in_data = NEWEST_MODEL_YEAR - self.max_vehicle_age + 1
        self.newest_model_year_in_data = NEWEST_MODEL_YEAR - self.min_vehicle_age + 1

    def search_vehicles(self, query: str, limit: int = 10):
        query = (query or "").strip().lower()
        if not query:
            return []
        combined = self.known_vehicles["Brand"] + " " + self.known_vehicles["Model"]
        # regex=False: the search box is plain text, not a regex - "(" would
        # otherwise crash the request and a crafted pattern could hang it.
        mask = combined.str.lower().str.contains(query, na=False, regex=False)
        matches = self.known_vehicles[mask].head(limit)
        return [
            {"brand": row.Brand, "model": row.Model, "label": f"{row.Brand} {row.Model}"}
            for row in matches.itertuples()
        ]

    def is_known_vehicle(self, brand: str, model: str) -> bool:
        """True only for a make/model the search list can actually offer."""
        return (brand, model) in self.spec_by_model.index

    def _lookup_spec(self, brand: str, model: str) -> dict:
        if (brand, model) in self.spec_by_model.index:
            row = self.spec_by_model.loc[(brand, model)]
            source = "exact_model"
        elif brand in self.spec_by_brand.index:
            row = self.spec_by_brand.loc[brand]
            source = "brand_average"
        else:
            row = self.spec_global
            source = "global_average"
        return row.to_dict(), source

    def estimate(self, brand: str, model: str, year: int, mileage: int) -> dict:
        spec, spec_source = self._lookup_spec(brand, model)
        vehicle_age = NEWEST_MODEL_YEAR - int(year) + 1

        row = {**spec}
        row["Brand"] = brand
        row["VehicleAge"] = vehicle_age
        row["Mileage"] = int(mileage)

        X = pd.DataFrame([row])[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
        point_estimate = float(self.pipeline.predict(X)[0])

        low = max(0.0, point_estimate - self.point_error_margin)
        high = point_estimate + self.point_error_margin

        # Flag (don't hide) predictions for vehicles older/newer than
        # anything the model was trained on - see the note in __init__.
        out_of_range = vehicle_age > self.max_vehicle_age or vehicle_age < self.min_vehicle_age
        out_of_range_reason = None
        if vehicle_age > self.max_vehicle_age:
            out_of_range_reason = (
                f"This {year} vehicle is older than every car in the training data, which only "
                f"covers {self.oldest_model_year_in_data}-{self.newest_model_year_in_data} model "
                "years. The model has never seen a vehicle this old, so it's extrapolating rather "
                "than predicting - treat this number as unreliable, not a real valuation."
            )
        elif vehicle_age < self.min_vehicle_age:
            out_of_range_reason = (
                f"This {year} vehicle is newer than every car in the training data "
                f"({self.oldest_model_year_in_data}-{self.newest_model_year_in_data} model years). "
                "Treat this number with caution."
            )

        return {
            "point_estimate": round(point_estimate, 2),
            "estimated_low": round(low, 2),
            "estimated_high": round(high, 2),
            "spec_source": spec_source,  # 'exact_model' | 'brand_average' | 'global_average'
            "model_used": "XGBoost",
            "model_r2": self.model_r2,  # measured R^2 - see accuracy_basis and __init__
            "accuracy_basis": self.accuracy_basis,
            "out_of_range": out_of_range,
            "out_of_range_reason": out_of_range_reason,
        }


# Loaded once per process, at import time (model loading takes a moment -
# doing it here, not per-request, is why app.py imports this module at
# startup rather than inside a route handler).
service = ValuationService()
