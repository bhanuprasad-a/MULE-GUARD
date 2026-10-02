from pathlib import Path

import numpy as np
import xgboost as xgb

from app.services.feature_engine import (
    calculate_account_features_from_db,
)


MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "muleguard_postgres_model.json"
)


model = xgb.XGBClassifier()
model.load_model(str(MODEL_PATH))


def analyze_account(account_id: str):
    result = calculate_account_features_from_db(
        account_id
    )

    feature_vector = np.array(
        [result["feature_vector"]],
        dtype=float,
    )

    probability = float(
        model.predict_proba(feature_vector)[0][1]
    )

    prediction = int(
        model.predict(feature_vector)[0]
    )

    return {
        "account_id": account_id,
        "prediction": prediction,
        "risk_probability": probability,
        "risk_score": round(
            probability * 100,
            2,
        ),
        "features": result,
    }