"""
Copies what the web app needs from a training run into tradesmart-flask/:

  models/xgboost_model.joblib                         -> the model the app serves
  models/nlp_intent_classifier.joblib                 -> categorises the chat's condition answers
  outputs/model_comparison.json                        -> the models' measured MAE / R^2
  outputs/split_experiments.json                       -> average accuracy over random splits (shown in the app)
  data/autotrader-south-africa-usedcars (corrected).csv -> the spec lookup table it predicts from

Run after train_models.py, train_deep_learning.py (which adds the MLP's
results to model_comparison.json) and nlp_parser.py, from the src folder:
    python copy_to_app.py
"""

import shutil

from features import PROJECT_ROOT, DATA_PATH

APP_DIR = PROJECT_ROOT.parent / "tradesmart-flask"

FILES = [
    PROJECT_ROOT / "models" / "xgboost_model.joblib",
    PROJECT_ROOT / "models" / "nlp_intent_classifier.joblib",
    PROJECT_ROOT / "outputs" / "model_comparison.json",
    PROJECT_ROOT / "outputs" / "split_experiments.json",
    DATA_PATH,
]


def main():
    for src in FILES:
        dst = APP_DIR / src.parent.name / src.name
        shutil.copy2(src, dst)
        print(f"Copied {src.parent.name}/{src.name}")


if __name__ == "__main__":
    main()
