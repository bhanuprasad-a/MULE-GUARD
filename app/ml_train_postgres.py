import os

import numpy as np
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold

from app.services.feature_engine import (
    calculate_all_features,
    FEATURE_ORDER,
)


def main():
    print("Loading PostgreSQL analysis data...")

    results = calculate_all_features()

    print(f"Accounts: {len(results)}")
    print(f"Features per account: {len(FEATURE_ORDER)}")

    # ---------------------------------------------------------
    # Build feature matrix
    # ---------------------------------------------------------

    X = np.array(
        [result["feature_vector"] for result in results],
        dtype=float,
    )

    # ---------------------------------------------------------
    # Build labels from PostgreSQL account status
    # ---------------------------------------------------------

    suspicious_statuses = {
        "Flagged",
        "Critical",
        "Blocked",
        "Under Review",
    }

    y = np.array(
        [
            1 if result["status"] in suspicious_statuses else 0
            for result in results
        ],
        dtype=int,
    )

    print(f"X shape: {X.shape}")
    print(f"Normal: {(y == 0).sum()}")
    print(f"Mule/Suspicious: {(y == 1).sum()}")

    # Safety checks
    assert X.shape[1] == 26
    assert len(X) == len(y)
    assert len(FEATURE_ORDER) == 26

    # ---------------------------------------------------------
    # 5-fold stratified cross-validation
    # ---------------------------------------------------------

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    metrics = []

    for fold, (train_idx, val_idx) in enumerate(
        cv.split(X, y),
        start=1,
    ):
        print(f"\nTraining fold {fold}/5...")

        model = xgb.XGBClassifier(
            max_depth=3,
            learning_rate=0.1,
            n_estimators=80,
            subsample=1.0,
            random_state=42,
            eval_metric="logloss",
        )

        model.fit(
            X[train_idx],
            y[train_idx],
        )

        predictions = model.predict(X[val_idx])

        accuracy = accuracy_score(
            y[val_idx],
            predictions,
        )

        precision = precision_score(
            y[val_idx],
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y[val_idx],
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y[val_idx],
            predictions,
            zero_division=0,
        )

        cm = confusion_matrix(
            y[val_idx],
            predictions,
        )

        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1:        {f1:.4f}")
        print("Confusion Matrix:")
        print(cm)

        metrics.append(
            {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    # ---------------------------------------------------------
    # CV summary
    # ---------------------------------------------------------

    print("\n======================================")
    print("5-FOLD CROSS-VALIDATION SUMMARY")
    print("======================================")

    for metric_name in (
        "accuracy",
        "precision",
        "recall",
        "f1",
    ):
        values = [
            metric[metric_name]
            for metric in metrics
        ]

        print(
            f"{metric_name.capitalize():10}: "
            f"{np.mean(values):.4f} ± "
            f"{np.std(values):.4f}"
        )

    # ---------------------------------------------------------
    # Final model
    # ---------------------------------------------------------

    print("\nTraining final model on all PostgreSQL data...")

    final_model = xgb.XGBClassifier(
        max_depth=3,
        learning_rate=0.1,
        n_estimators=80,
        subsample=1.0,
        random_state=42,
        eval_metric="logloss",
    )

    final_model.fit(X, y)

    # ---------------------------------------------------------
    # Save new model
    # ---------------------------------------------------------

    os.makedirs("data", exist_ok=True)

    model_path = "data/muleguard_postgres_model.json"

    final_model.save_model(model_path)

    print(f"\nSaved model: {model_path}")

    # ---------------------------------------------------------
    # Feature importance
    # ---------------------------------------------------------

    print("\n======================================")
    print("FEATURE IMPORTANCE")
    print("======================================")

    importances = final_model.feature_importances_

    indices = np.argsort(importances)[::-1]

    for rank, index in enumerate(indices, start=1):
        print(
            f"{rank:02d}. "
            f"{FEATURE_ORDER[index]:30} "
            f"{importances[index]:.4f}"
        )


if __name__ == "__main__":
    main()