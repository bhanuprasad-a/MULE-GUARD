import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import xgboost as xgb

from app.services.feature_engine import (
    calculate_account_features_from_db,
    FEATURE_ORDER,
)


MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "muleguard_postgres_model.json"
)


model = xgb.XGBClassifier()
model.load_model(str(MODEL_PATH))

# Thread-safe in-process telemetry for live risk inferences
_telemetry_lock = threading.Lock()
_telemetry = {
    "total_inferences": 0,
    "successful_inferences": 0,
    "failed_inferences": 0,
    "total_latency_ms": 0.0,
    "avg_latency_ms": 0.0,
    "latest_latency_ms": None,
    "latest_inference_time": None,
    "risk_distribution": {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    },
}


def record_inference_event(latency_ms: float, risk_score: float, success: bool = True):
    with _telemetry_lock:
        if success:
            _telemetry["successful_inferences"] += 1
            _telemetry["total_latency_ms"] += latency_ms
            _telemetry["avg_latency_ms"] = round(
                _telemetry["total_latency_ms"] / _telemetry["successful_inferences"], 2
            )
            _telemetry["latest_latency_ms"] = latency_ms
            _telemetry["latest_inference_time"] = datetime.now(timezone.utc).isoformat()

            if risk_score >= 80:
                _telemetry["risk_distribution"]["critical"] += 1
            elif risk_score >= 60:
                _telemetry["risk_distribution"]["high"] += 1
            elif risk_score >= 30:
                _telemetry["risk_distribution"]["medium"] += 1
            else:
                _telemetry["risk_distribution"]["low"] += 1
        else:
            _telemetry["failed_inferences"] += 1
            _telemetry["latest_latency_ms"] = latency_ms
            _telemetry["latest_inference_time"] = datetime.now(timezone.utc).isoformat()


def get_inference_telemetry():
    with _telemetry_lock:
        return {
            "total_inferences": _telemetry["total_inferences"],
            "successful_inferences": _telemetry["successful_inferences"],
            "failed_inferences": _telemetry["failed_inferences"],
            "avg_latency_ms": _telemetry["avg_latency_ms"],
            "latest_latency_ms": _telemetry["latest_latency_ms"],
            "latest_inference_time": _telemetry["latest_inference_time"],
            "risk_distribution": dict(_telemetry["risk_distribution"]),
        }


def analyze_account(account_id: str):
    t0 = time.perf_counter()
    with _telemetry_lock:
        _telemetry["total_inferences"] += 1

    try:
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

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        score = round(
            probability * 100,
            2,
        )

        record_inference_event(latency_ms, score, success=True)

        return {
            "account_id": account_id,
            "prediction": prediction,
            "risk_probability": probability,
            "risk_score": score,
            "features": result,
        }
    except Exception:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        record_inference_event(latency_ms, 0.0, success=False)
        raise