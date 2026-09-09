import os
import json
import tempfile
import subprocess
import numpy as np
import pandas as pd
from collections import Counter

# Import ML libraries
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    precision_recall_curve, auc, confusion_matrix
)

def extract_db_from_js():
    js_filepath = r"frontend/scripts/data-store.js"
    if not os.path.exists(js_filepath):
        raise FileNotFoundError(f"data-store.js not found at {js_filepath}")

    # Temporary JS extractor script
    extractor_js = """
    const fs = require('fs');
    const vm = require('vm');
    const dbExpandedCode = fs.readFileSync('frontend/scripts/synthetic_db_expanded.js', 'utf8');
    const storeCode = fs.readFileSync('frontend/scripts/data-store.js', 'utf8');
    const sandbox = {
        window: {},
        location: { pathname: '' },
        localStorage: { getItem: () => null, setItem: () => null }
    };
    try {
        vm.createContext(sandbox);
        vm.runInContext(dbExpandedCode, sandbox);
        vm.runInContext(storeCode, sandbox);
        const db = sandbox.window.MuleGuardStore.reset();
        console.log(JSON.stringify(db));
    } catch (e) {
        console.error("Extraction error: " + e.message);
        process.exit(1);
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tf:
        tf.write(extractor_js)
        temp_name = tf.name

    try:
        res = subprocess.run(["node", temp_name], capture_output=True, text=True, check=True)
        db = json.loads(res.stdout)
        return db
    except subprocess.CalledProcessError as e:
        print("Node extraction failed:")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        raise e
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def parse_time_to_minutes(time_str):
    if not time_str:
        return 999999
    if 'Just now' in time_str:
        return 0
    try:
        parts = time_str.split()
        num = int(parts[0])
        if 'min' in time_str:
            return num
        if 'hr' in time_str:
            return num * 60
        if 'day' in time_str:
            return num * 1440
    except Exception:
        pass
    return 999999

def build_feature_matrix(db):
    accounts = db["accounts"]
    transactions = db["transactions"]
    
    # Pre-build adjacency list for cycle/loop detection
    adj = {}
    for t in transactions:
        s = t.get("senderId")
        r = t.get("receiverId")
        if s and r:
            if s not in adj:
                adj[s] = set()
            adj[s].add(r)

    rows = []
    for acc_id, acc in accounts.items():
        inbound = [t for t in transactions if t.get("receiverId") == acc_id]
        outbound = [t for t in transactions if t.get("senderId") == acc_id]
        all_txs = inbound + outbound
        
        # --- 14 Behavioural Features ---
        tx_count = len(all_txs)
        in_tx_count = len(inbound)
        out_tx_count = len(outbound)
        
        total_in_amount = sum(t.get("amountNumeric", 0) for t in inbound)
        total_out_amount = sum(t.get("amountNumeric", 0) for t in outbound)
        
        counterparties = set()
        for t in all_txs:
            s = t.get("senderId")
            r = t.get("receiverId")
            if s and s != acc_id: counterparties.add(s)
            if r and r != acc_id: counterparties.add(r)
        unique_counterparties = len(counterparties)
        
        velocity = tx_count
        
        amounts = [t.get("amountNumeric", 0) for t in all_txs]
        avg_tx_amount = np.mean(amounts) if amounts else 0.0
        amount_std_dev = np.std(amounts) if len(amounts) > 1 else 0.0
        
        rapid_holding_ratio = 0.0
        if total_in_amount > 0:
            rapid_holding_ratio = min(100.0, (total_out_amount / total_in_amount) * 100.0)
            
        in_out_ratio = total_out_amount / total_in_amount if total_in_amount > 0 else 0.0
        
        recent_txs = [t for t in all_txs if 'min' in t.get('time', '') or '1 hr' in t.get('time', '') or 'Just now' in t.get('time', '')]
        behavioral_shift = len(recent_txs) / tx_count if tx_count > 0 else 0.0
        
        inbound_degree = in_tx_count
        outbound_degree = out_tx_count
        network_degree = inbound_degree + outbound_degree
        
        inbound_counterparties = len(set(t.get("senderId") for t in inbound if t.get("senderId") != acc_id))
        outbound_counterparties = len(set(t.get("receiverId") for t in outbound if t.get("receiverId") != acc_id))
        is_fan_in = 1.0 if inbound_counterparties >= 3 else 0.0
        is_fan_out = 1.0 if outbound_counterparties >= 3 else 0.0
        
        shared_suspicious = 0.0
        for other_id, other in accounts.items():
            if other_id != acc_id and other.get("status") in ["Blocked", "Flagged", "Critical"]:
                if acc.get("phone") == other.get("phone") or acc.get("device") == other.get("device") or acc.get("ip") == other.get("ip"):
                    shared_suspicious = 1.0
                    break
                    
        # --- 11 Network Intelligence Features ---
        total_degree = inbound_degree + outbound_degree
        fan_in = inbound_counterparties
        fan_out = outbound_counterparties
        
        counterparty_volumes = {}
        for t in all_txs:
            partner = t.get("receiverId") if t.get("senderId") == acc_id else t.get("senderId")
            if partner and partner != acc_id:
                counterparty_volumes[partner] = counterparty_volumes.get(partner, 0) + t.get("amountNumeric", 0)
        total_vol = sum(counterparty_volumes.values())
        network_concentration = 0.0
        if total_vol > 0:
            for v in counterparty_volumes.values():
                share = v / total_vol
                network_concentration += share * share
                
        cycle_participation = 0.0
        visited = set()
        def find_cycle(current, depth):
            if depth > 4:
                return False
            neighbors = adj.get(current, set())
            for next_node in neighbors:
                if next_node == acc_id and depth >= 2:
                    return True
                if next_node not in visited:
                    visited.add(next_node)
                    if find_cycle(next_node, depth + 1):
                        return True
                    visited.remove(next_node)
            return False
        
        visited.add(acc_id)
        if find_cycle(acc_id, 1):
            cycle_participation = 1.0
            
        direct_nbrs = set()
        for t in all_txs:
            s = t.get("senderId")
            r = t.get("receiverId")
            if s and s != acc_id: direct_nbrs.add(s)
            if r and r != acc_id: direct_nbrs.add(r)
        two_hop_nbrs = set(direct_nbrs)
        for n in direct_nbrs:
            nTxs = [t for t in transactions if t.get("senderId") == n or t.get("receiverId") == n]
            for t in nTxs:
                s = t.get("senderId")
                r = t.get("receiverId")
                if s and s != acc_id: two_hop_nbrs.add(s)
                if r and r != acc_id: two_hop_nbrs.add(r)
        multi_hop_connectivity = len(two_hop_nbrs)
        
        temporal_proximity = 1440.0
        for in_tx in inbound:
            in_time = parse_time_to_minutes(in_tx.get("time"))
            for out_tx in outbound:
                out_time = parse_time_to_minutes(out_tx.get("time"))
                if out_time <= in_time:
                    gap = in_time - out_time
                    if gap < temporal_proximity:
                        temporal_proximity = gap
                        
        recent_txs_count = len([t for t in all_txs if parse_time_to_minutes(t.get("time")) <= 120])
        activity_pattern = recent_txs_count / tx_count if tx_count > 0 else 0.0

        is_mule = 1 if acc.get("status") in ["Flagged", "Critical", "Blocked", "Under Review"] else 0
        
        row = {
            "account_id": acc_id,
            "name": acc.get("name"),
            "scenario": acc.get("scenario", "Unknown"),
            # Behavioural Features
            "txCount": tx_count,
            "inTxCount": in_tx_count,
            "outTxCount": out_tx_count,
            "totalInAmount": total_in_amount,
            "totalOutAmount": total_out_amount,
            "uniqueCounterparties": unique_counterparties,
            "velocity": velocity,
            "avgTxAmount": avg_tx_amount,
            "amountStdDev": amount_std_dev,
            "rapidHoldingRatio": rapid_holding_ratio,
            "inOutRatio": in_out_ratio,
            "behavioralShift": behavioral_shift,
            "networkDegree": network_degree,
            "inboundDegree": inbound_degree,
            "outboundDegree": outbound_degree,
            "isFanIn": is_fan_in,
            "isFanOut": is_fan_out,
            "sharedSuspiciousConnection": shared_suspicious,
            # Network Features
            "totalDegree": total_degree,
            "fanIn": fan_in,
            "fanOut": fan_out,
            "networkConcentration": network_concentration,
            "cycleParticipation": cycle_participation,
            "multiHopConnectivity": multi_hop_connectivity,
            "temporalProximity": temporal_proximity,
            "activityPattern": activity_pattern,
            "label_is_mule": is_mule
        }
        rows.append(row)
        
    return pd.DataFrame(rows)

def tune_and_evaluate_nested(X, y):
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    oof_probs = np.zeros(len(y))
    oof_preds = np.zeros(len(y))
    
    outer_metrics = []
    selected_params_per_fold = []
    
    param_grid = []
    for max_depth in [2, 3, 4]:
        for lr in [0.05, 0.1, 0.2]:
            for n_est in [30, 50, 80]:
                for subsample in [0.8, 1.0]:
                    param_grid.append({
                        "max_depth": max_depth,
                        "learning_rate": lr,
                        "n_estimators": n_est,
                        "subsample": subsample
                    })

    for fold_idx, (train_idx, val_idx) in enumerate(outer_cv.split(X, y)):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
        
        # Inner loop 3-fold CV for hyperparameter tuning
        inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        best_param = None
        best_inner_score = -1.0
        
        for params in param_grid:
            inner_scores = []
            for inner_train_idx, inner_val_idx in inner_cv.split(X_train, y_train):
                X_itrain, y_itrain = X_train.iloc[inner_train_idx], y_train.iloc[inner_train_idx]
                X_ival, y_ival = X_train.iloc[inner_val_idx], y_train.iloc[inner_val_idx]
                
                clf = xgb.XGBClassifier(
                    max_depth=params["max_depth"],
                    learning_rate=params["learning_rate"],
                    n_estimators=params["n_estimators"],
                    subsample=params["subsample"],
                    random_state=42,
                    eval_metric='logloss'
                )
                clf.fit(X_itrain, y_itrain)
                
                ipreds = clf.predict(X_ival)
                # Optimize for inner F1
                if sum(ipreds) == 0 and sum(y_ival) == 0:
                    score = 1.0
                elif sum(ipreds) == 0 or sum(y_ival) == 0:
                    score = 0.0
                else:
                    score = f1_score(y_ival, ipreds, zero_division=0)
                inner_scores.append(score)
                
            avg_inner_score = np.mean(inner_scores)
            if avg_inner_score > best_inner_score:
                best_inner_score = avg_inner_score
                best_param = params
                
        selected_params_per_fold.append(best_param)
        
        # Train outer model with best parameters
        outer_clf = xgb.XGBClassifier(
            max_depth=best_param["max_depth"],
            learning_rate=best_param["learning_rate"],
            n_estimators=best_param["n_estimators"],
            subsample=best_param["subsample"],
            random_state=42,
            eval_metric='logloss'
        )
        outer_clf.fit(X_train, y_train)
        
        probs = outer_clf.predict_proba(X_val)[:, 1]
        preds = outer_clf.predict(X_val)
        
        oof_probs[val_idx] = probs
        oof_preds[val_idx] = preds
        
        # Calculate metrics
        acc = accuracy_score(y_val, preds)
        prec = precision_score(y_val, preds, zero_division=0)
        rec = recall_score(y_val, preds, zero_division=0)
        f1 = f1_score(y_val, preds, zero_division=0)
        
        pr, rec_curve, _ = precision_recall_curve(y_val, probs)
        prauc = auc(rec_curve, pr)
        
        # Robustly handle 1-class edge cases in confusion matrix
        cm = confusion_matrix(y_val, preds)
        if cm.shape == (1, 1):
            # Check single class
            if y_val.iloc[0] == 0:
                tn, fp, fn, tp = cm[0, 0], 0, 0, 0
            else:
                tn, fp, fn, tp = 0, 0, 0, cm[0, 0]
        else:
            tn, fp, fn, tp = cm.ravel()
            
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        outer_metrics.append({
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "prauc": float(prauc),
            "fpr": float(fpr),
            "confusion": [int(tn), int(fp), int(fn), int(tp)]
        })
        
    return oof_probs, oof_preds, outer_metrics, selected_params_per_fold

def get_stats(metrics_list, key):
    vals = [m[key] for m in metrics_list]
    return float(np.mean(vals)), float(np.std(vals))

def analyze_thresholds(y, oof_probs):
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    records = []
    for t in thresholds:
        preds = (oof_probs >= t).astype(int)
        prec = precision_score(y, preds, zero_division=0)
        rec = recall_score(y, preds, zero_division=0)
        f1 = f1_score(y, preds, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y, preds).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        records.append({
            "threshold": float(t),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "fpr": float(fpr),
            "confusion": [int(tn), int(fp), int(fn), int(tp)]
        })
    return records

def train_and_evaluate():
    print("Loading expanded database...")
    db = extract_db_from_js()
    df = build_feature_matrix(db)
    
    # 1. Behavioural Features list
    behavioural_cols = [
        "txCount", "inTxCount", "outTxCount", "totalInAmount", "totalOutAmount",
        "uniqueCounterparties", "velocity", "avgTxAmount", "amountStdDev",
        "rapidHoldingRatio", "inOutRatio", "behavioralShift", "networkDegree",
        "inboundDegree", "outboundDegree", "isFanIn", "isFanOut", "sharedSuspiciousConnection"
    ]
    
    # 2. Network Features list
    network_cols = [
        "totalDegree", "fanIn", "fanOut", "networkConcentration",
        "cycleParticipation", "multiHopConnectivity", "temporalProximity", "activityPattern"
    ]
    
    combined_cols = behavioural_cols + network_cols
    
    X_behav = df[behavioural_cols]
    X_comb = df[combined_cols]
    y = df["label_is_mule"]
    
    # Count scenarios for metadata reporting
    scenario_counts = df["scenario"].value_counts().to_dict()
    class_counts = y.value_counts().to_dict()
    
    print("\n=======================================================")
    print("       Nested Stratified K-Fold Cross-Validation      ")
    print("=======================================================")
    
    print("Evaluating Model A (Behaviour-only)...")
    oof_probs_a, oof_preds_a, metrics_a, params_a = tune_and_evaluate_nested(X_behav, y)
    
    print("Evaluating Model B (Behaviour + Network)...")
    oof_probs_b, oof_preds_b, metrics_b, params_b = tune_and_evaluate_nested(X_comb, y)
    
    # Select most frequent hyperparameter config for full dataset retraining
    def select_best_config(params_list):
        tuple_list = [tuple(p.items()) for p in params_list]
        most_common = Counter(tuple_list).most_common(1)[0][0]
        return dict(most_common)

    best_config_a = select_best_config(params_a)
    best_config_b = select_best_config(params_b)
    
    print(f"\nOptimal Model A Hyperparameters: {best_config_a}")
    print(f"Optimal Model B Hyperparameters: {best_config_b}")
    
    # Threshold Analysis
    thresholds_a = analyze_thresholds(y, oof_probs_a)
    thresholds_b = analyze_thresholds(y, oof_probs_b)
    
    # Summary Metrics (mean ± std)
    summary_results = {}
    for key in ["accuracy", "precision", "recall", "f1", "prauc", "fpr"]:
        mean_a, std_a = get_stats(metrics_a, key)
        mean_b, std_b = get_stats(metrics_b, key)
        summary_results[key] = {
            "model_a": {"mean": mean_a, "std": std_a},
            "model_b": {"mean": mean_b, "std": std_b}
        }
        
    print("\n=======================================================")
    print("            OUTER K-FOLD PERFORMANCE RESULTS           ")
    print("=======================================================")
    print("Metric          | Model A (Behav)       | Model B (Combined)")
    print("-------------------------------------------------------")
    for metric, res in summary_results.items():
        ma, sa = res["model_a"]["mean"], res["model_a"]["std"]
        mb, sb = res["model_b"]["mean"], res["model_b"]["std"]
        print(f"{metric.capitalize():15} | {ma:.4f} ± {sa:.4f}       | {mb:.4f} ± {sb:.4f}")
        
    # Retrain final models on the entire dataset using optimal configs
    print("\nRetraining final models on the full dataset...")
    final_model_a = xgb.XGBClassifier(
        max_depth=best_config_a["max_depth"],
        learning_rate=best_config_a["learning_rate"],
        n_estimators=best_config_a["n_estimators"],
        subsample=best_config_a["subsample"],
        random_state=42,
        eval_metric='logloss'
    )
    final_model_a.fit(X_behav, y)
    
    final_model_b = xgb.XGBClassifier(
        max_depth=best_config_b["max_depth"],
        learning_rate=best_config_b["learning_rate"],
        n_estimators=best_config_b["n_estimators"],
        subsample=best_config_b["subsample"],
        random_state=42,
        eval_metric='logloss'
    )
    final_model_b.fit(X_comb, y)
    
    # Save Model B JSON Booster for future UI integration
    os.makedirs("data", exist_ok=True)
    model_b_path = "data/best_muleguard_model.json"
    final_model_b.save_model(model_b_path)
    print(f"Saved optimal combined model to: {model_b_path}")
    
    # Also save as JS file for browser synchronous loading
    with open(model_b_path, "r", encoding="utf-8") as f:
        model_json_str = f.read()
    js_model_content = f"// Automatically generated XGBoost model booster seed\nwindow.MuleGuardModelBooster = {model_json_str};\n"
    js_model_path = "frontend/scripts/best_muleguard_model.js"
    os.makedirs(os.path.dirname(js_model_path), exist_ok=True)
    with open(js_model_path, "w", encoding="utf-8") as f:
        f.write(js_model_content)
    print(f"Saved JS model booster seed to: {js_model_path}")
    
    # Report feature importances of final Model B
    importances = final_model_b.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\n=======================================================")
    print("        Final Model B Full Feature Importances         ")
    print("=======================================================")
    for i, idx in enumerate(indices):
        f_name = combined_cols[idx]
        f_type = "Network" if f_name in network_cols else "Behav"
        print(f"{i+1:02d}. {f_name:<28} ({f_type:<7}) : {importances[idx]:.4f}")
        
    # Write experiment results JSON report
    report_data = {
        "dataset_statistics": {
            "total_accounts": len(df),
            "class_distribution": {str(k): int(v) for k, v in class_counts.items()},
            "scenario_distribution": {str(k): int(v) for k, v in scenario_counts.items()}
        },
        "selected_hyperparameters": {
            "model_a": best_config_a,
            "model_b": best_config_b
        },
        "outer_fold_metrics": summary_results,
        "oof_threshold_analysis": {
            "model_a": thresholds_a,
            "model_b": thresholds_b
        }
    }
    
    results_path = "data/experiment_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)
    print(f"Saved experiment results JSON report to: {results_path}")

if __name__ == "__main__":
    train_and_evaluate()
