import os
import json
import sys

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_DIR)

from app.services.feature_engine import FEATURE_ORDER
from app.services.risk_engine import load_model, predict_account_risk

print(f"Canonical FEATURE_ORDER ({len(FEATURE_ORDER)} features):")
for i, f in enumerate(FEATURE_ORDER):
    print(f"  {i:2}: {f}")

# Inspect active postgres model
pg_model_path = os.path.join(PROJECT_DIR, "data", "muleguard_postgres_model.json")
with open(pg_model_path, "r") as f:
    pg_model = json.load(f)

tree_count = len(pg_model.get("learner", {}).get("gradient_booster", {}).get("model", {}).get("trees", []))
num_features = int(pg_model.get("learner", {}).get("learner_model_param", {}).get("num_feature", 0))
feature_names = pg_model.get("learner", {}).get("feature_names", [])

print("\nActive Model (data/muleguard_postgres_model.json):")
print(f"  Tree count: {tree_count}")
print(f"  Num features: {num_features}")
print(f"  Feature names match FEATURE_ORDER: {feature_names == FEATURE_ORDER}")

# Inspect legacy model
legacy_model_path = os.path.join(PROJECT_DIR, "data", "best_muleguard_model.json")
with open(legacy_model_path, "r") as f:
    legacy_model = json.load(f)

leg_tree_count = len(legacy_model.get("learner", {}).get("gradient_booster", {}).get("model", {}).get("trees", []))
leg_num_features = int(legacy_model.get("learner", {}).get("learner_model_param", {}).get("num_feature", 0))
leg_feature_names = legacy_model.get("learner", {}).get("feature_names", [])

print("\nLegacy Model (data/best_muleguard_model.json):")
print(f"  Tree count: {leg_tree_count}")
print(f"  Num features: {leg_num_features}")
print(f"  Feature names match FEATURE_ORDER: {leg_feature_names == FEATURE_ORDER}")

# Test active risk_engine load
loaded_booster = load_model()
print(f"\nrisk_engine.load_model() loaded booster: {loaded_booster is not None}")
