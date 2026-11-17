"""
FOOD PLANT AI — Machine Learning Training Pipeline
Trains 4 classifiers on spice quality prediction (PASS/FAIL).
Uses chronological split to prevent data leakage.
Saves the best model, pipeline, and evaluation artefacts.

Run:
    python src/train_model.py
"""

import os
import sys
import time
import json
import joblib
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model    import LogisticRegression
from sklearn.tree            import DecisionTreeClassifier
from sklearn.ensemble        import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing   import LabelEncoder, StandardScaler
from sklearn.compose         import ColumnTransformer
from sklearn.pipeline        import Pipeline
from sklearn.impute           import SimpleImputer
from sklearn.metrics          import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH   = os.path.join(BASE_DIR, "data", "cleaned_production_data.csv")
MODELS_DIR  = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(MODELS_DIR,  exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── Feature columns (no post-inspection leakage) ──────────────────────────────
NUMERIC_FEATURES = [
    "Raw_Material_Weight_Kg",
    "Moisture_Level",
    "Machine_Temperature",
    "Machine_Speed",
    "Production_Time",
    "Grade_Numeric",
    "Efficiency_Ratio",
    "Temp_in_Range",
    "Speed_in_Range",
    "Moisture_Risk",
]
CATEGORICAL_FEATURES = ["Production_Line", "Spice_Type"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "Quality_Result"


# ── Data loading and chronological split ──────────────────────────────────────

def load_and_split(path: str):
    print(f"Loading cleaned data from: {path}")
    df = pd.read_csv(path, low_memory=False, parse_dates=["Production_Date"])
    df = df.sort_values("Production_Date").reset_index(drop=True)
    print(f"  Rows: {len(df):,}  |  PASS: {(df[TARGET]=='PASS').sum():,}  |  FAIL: {(df[TARGET]=='FAIL').sum():,}")

    # Drop rows where any required feature is missing
    required = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]
    available = [c for c in required if c in df.columns]
    df = df.dropna(subset=available)

    n = len(df)
    train_end = int(n * 0.70)
    val_end   = int(n * 0.85)

    train_df = df.iloc[:train_end].copy()
    val_df   = df.iloc[train_end:val_end].copy()
    test_df  = df.iloc[val_end:].copy()

    print(f"  Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}")
    return train_df, val_df, test_df, df


def encode_categoricals(train_df, val_df, test_df):
    """
    One-hot encode Production_Line and Spice_Type consistently across all splits.
    Returns updated DataFrames and the final list of feature column names.
    """
    ohe_cols_all = []
    for col in CATEGORICAL_FEATURES:
        train_dummies = pd.get_dummies(train_df[col], prefix=col, drop_first=False)
        cat_cols = train_dummies.columns.tolist()
        ohe_cols_all.extend(cat_cols)
        for split in [train_df, val_df, test_df]:
            d = pd.get_dummies(split[col], prefix=col, drop_first=False)
            for c in cat_cols:
                if c not in d.columns:
                    d[c] = 0
            split[cat_cols] = d[cat_cols].values.astype(int)
        for split in [train_df, val_df, test_df]:
            split.drop(columns=[col], inplace=True, errors="ignore")

    final_features = NUMERIC_FEATURES + ohe_cols_all
    return train_df, val_df, test_df, final_features


def prepare_xy(df, feature_cols=None):
    """Select features and target. feature_cols defaults to all non-target columns."""
    if feature_cols is None:
        feature_cols = [c for c in df.columns if c not in [TARGET, "Production_Date", "Record_ID",
                                                             "Batch_ID", "Weight_Unit",
                                                             "Final_Product_Weight_Kg",
                                                             "Supplier_Name"]]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].copy()
    y = (df[TARGET] == "PASS").astype(int)   # PASS=1, FAIL=0
    return X, y


# ── Model evaluation ──────────────────────────────────────────────────────────

def evaluate_model(model, X_test, y_test, model_name):
    t0   = time.perf_counter()
    yhat = model.predict(X_test)
    t1   = time.perf_counter()
    yprob = model.predict_proba(X_test)[:, 1]

    # Measure single-record inference time (average of 100 runs on first row)
    if hasattr(X_test, "iloc"):
        single_row = X_test.iloc[[0]]
    else:
        single_row = X_test[:1]
    times = []
    for _ in range(100):
        t0s = time.perf_counter()
        model.predict(single_row)
        times.append(time.perf_counter() - t0s)
    avg_infer_ms = np.mean(times) * 1000

    acc   = accuracy_score(y_test, yhat)
    prec  = precision_score(y_test, yhat, average="weighted", zero_division=0)
    rec   = recall_score(y_test, yhat, average="weighted", zero_division=0)
    f1    = f1_score(y_test, yhat, average="weighted", zero_division=0)
    auc   = roc_auc_score(y_test, yprob)
    # FAIL-class recall (class 0 = FAIL)
    cm    = confusion_matrix(y_test, yhat)
    fail_recall = cm[0, 0] / cm[0].sum() if cm[0].sum() > 0 else 0.0

    return {
        "model_name":        model_name,
        "accuracy":          round(acc,  4),
        "precision_wt":      round(prec, 4),
        "recall_wt":         round(rec,  4),
        "f1_weighted":       round(f1,   4),
        "roc_auc":           round(auc,  4),
        "fail_class_recall": round(fail_recall, 4),
        "avg_inference_ms":  round(avg_infer_ms, 4),
        "confusion_matrix":  cm,
        "y_pred":            yhat,
        "y_prob":            yprob,
    }


# ── Feature importance ────────────────────────────────────────────────────────

def get_feature_names_after_encode(X_train_raw):
    return X_train_raw.columns.tolist()


def plot_confusion_matrix(cm, model_name, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    plt.colorbar(im)
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Pred FAIL", "Pred PASS"], fontsize=11)
    ax.set_yticklabels(["True FAIL", "True PASS"], fontsize=11)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=14, fontweight="bold")
    ax.set_title(f"Confusion Matrix — {model_name}", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {path}")


def plot_feature_importance(importances, feature_names, model_name, path):
    idx = np.argsort(importances)[::-1][:15]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh([feature_names[i] for i in idx[::-1]], importances[idx[::-1]], color="#2563eb")
    ax.set_title(f"Top 15 Feature Importances — {model_name}", fontsize=12, fontweight="bold")
    ax.set_xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {path}")


# ── Main training pipeline ────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("FOOD PLANT AI — ML Quality Prediction Training")
    print("=" * 70)

    # 1. Load data
    train_df, val_df, test_df, full_df = load_and_split(DATA_PATH)

    # 2. Encode categoricals (consistent across splits)
    train_df, val_df, test_df, feature_names = encode_categoricals(
        train_df.copy(), val_df.copy(), test_df.copy()
    )

    X_train, y_train = prepare_xy(train_df, feature_names)
    X_val,   y_val   = prepare_xy(val_df,   feature_names)
    X_test,  y_test  = prepare_xy(test_df,  feature_names)
    print(f"\nFeatures used: {len(feature_names)}")
    print(f"  {feature_names}")

    # 3. Build preprocessing pipeline and fit on train only
    num_cols = [c for c in NUMERIC_FEATURES if c in X_train.columns]
    cat_ohe_cols = [c for c in feature_names if c not in NUMERIC_FEATURES]

    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])

    # Fit scaler on numeric features only (cats are already encoded as int)
    num_preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])

    # Save a full pipeline object for single-record prediction
    ct = ColumnTransformer([
        ("num", num_preprocessor, num_cols),
    ], remainder="passthrough")  # passthrough OHE int columns

    ct.fit(X_train)
    X_train_tr = pd.DataFrame(ct.transform(X_train))
    X_val_tr   = pd.DataFrame(ct.transform(X_val))
    X_test_tr  = pd.DataFrame(ct.transform(X_test))

    # Save column transformer
    joblib.dump(ct, os.path.join(MODELS_DIR, "preprocessing_pipeline.pkl"))
    print(f"\nPreprocessing pipeline saved.")

    # 4. Train 4 models
    models_config = [
        ("Logistic Regression",  LogisticRegression(max_iter=1000, C=1.0, random_state=42)),
        ("Decision Tree",        DecisionTreeClassifier(max_depth=10, random_state=42)),
        ("Random Forest",        RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)),
        ("Gradient Boosting",    GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)),
    ]

    results = []
    trained_models = {}

    print("\n" + "─" * 70)
    print("Training Models...")
    print("─" * 70)

    for name, clf in models_config:
        print(f"\n[{name}] training...")
        t0 = time.time()
        clf.fit(X_train_tr, y_train)
        elapsed = time.time() - t0
        print(f"  Trained in {elapsed:.1f}s")

        metrics = evaluate_model(clf, X_test_tr, y_test, name)
        metrics["train_time_s"] = round(elapsed, 2)
        results.append(metrics)
        trained_models[name] = clf

        print(f"  Accuracy:   {metrics['accuracy']:.4f}")
        print(f"  F1:         {metrics['f1_weighted']:.4f}")
        print(f"  ROC-AUC:    {metrics['roc_auc']:.4f}")
        print(f"  FAIL Recall:{metrics['fail_class_recall']:.4f}")
        print(f"  Infer time: {metrics['avg_inference_ms']:.4f} ms")

    # 5. Select best model (highest FAIL recall × F1 product)
    for r in results:
        r["selection_score"] = r["fail_class_recall"] * r["f1_weighted"]
    best = max(results, key=lambda r: r["selection_score"])
    best_name  = best["model_name"]
    best_model = trained_models[best_name]
    print(f"\n✅ Best model: {best_name}  (selection score: {best['selection_score']:.4f})")

    # 6. Save best model
    joblib.dump(best_model, os.path.join(MODELS_DIR, "quality_model.pkl"))
    print(f"   Saved → models/quality_model.pkl")

    # 7. Save model metadata
    fi = None
    if hasattr(best_model, "feature_importances_"):
        fi = dict(zip(feature_names, best_model.feature_importances_.tolist()))
    elif hasattr(best_model, "coef_"):
        fi = dict(zip(feature_names, best_model.coef_[0].tolist()))

    # Reconstruct full feature names after ColumnTransformer
    transformed_feature_names = num_cols + [c for c in feature_names if c not in num_cols]

    metadata = {
        "model_name":        best_name,
        "feature_columns":   feature_names,
        "num_cols":          num_cols,
        "cat_ohe_cols":      [c for c in feature_names if c not in num_cols],
        "classes":           ["FAIL", "PASS"],
        "train_date":        pd.Timestamp.now().strftime("%Y-%m-%d"),
        "test_metrics":      {k: v for k, v in best.items() if k not in ("confusion_matrix", "y_pred", "y_prob")},
        "feature_importances": fi,
        "all_model_results":  [
            {k: v for k, v in r.items() if k not in ("confusion_matrix", "y_pred", "y_prob")}
            for r in results
        ],
    }
    joblib.dump(metadata, os.path.join(MODELS_DIR, "model_metadata.pkl"))
    print(f"   Saved → models/model_metadata.pkl")

    # 8. Save reports
    # 8a. Text evaluation report
    report_lines = [
        "=" * 70,
        "FOOD PLANT AI — Model Evaluation Report",
        f"Generated: {pd.Timestamp.now()}",
        "=" * 70,
        "",
        f"Best Model: {best_name}",
        f"Selection criterion: highest (FAIL_Recall × F1_weighted)",
        "",
    ]
    for r in results:
        report_lines += [
            f"─── {r['model_name']} ───",
            f"  Accuracy:            {r['accuracy']:.4f}",
            f"  Precision (weighted):{r['precision_wt']:.4f}",
            f"  Recall (weighted):   {r['recall_wt']:.4f}",
            f"  F1 (weighted):       {r['f1_weighted']:.4f}",
            f"  ROC-AUC:             {r['roc_auc']:.4f}",
            f"  FAIL-class Recall:   {r['fail_class_recall']:.4f}",
            f"  Avg Inference (ms):  {r['avg_inference_ms']:.4f}",
            f"  Training Time (s):   {r['train_time_s']:.2f}",
            f"  Confusion Matrix:\n{r['confusion_matrix']}",
            "",
        ]
    report_path = os.path.join(REPORTS_DIR, "model_evaluation.txt")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"   Saved → {report_path}")

    # 8b. Test results CSV (50+ independent test cases)
    test_results_df = pd.DataFrame({
        "Index":            range(len(y_test)),
        "True_Label":       ["PASS" if y == 1 else "FAIL" for y in y_test],
        "Predicted_Label":  ["PASS" if y == 1 else "FAIL" for y in best["y_pred"]],
        "FAIL_Probability": [round(1 - p, 4) for p in best["y_prob"]],
        "PASS_Probability": [round(p, 4)      for p in best["y_prob"]],
        "Correct":          [t == p for t, p in zip(y_test, best["y_pred"])],
    })
    tr_path = os.path.join(REPORTS_DIR, "test_results.csv")
    test_results_df.to_csv(tr_path, index=False)
    print(f"   Saved → {tr_path}  ({len(test_results_df):,} test cases)")

    # 8c. Confusion matrix plot
    cm_path = os.path.join(REPORTS_DIR, "confusion_matrix.png")
    plot_confusion_matrix(best["confusion_matrix"], best_name, cm_path)

    # 8d. Feature importance plot
    if fi is not None:
        fi_path = os.path.join(REPORTS_DIR, "feature_importance.png")
        fi_arr  = np.array(list(fi.values()))
        fi_names = list(fi.keys())
        plot_feature_importance(fi_arr, fi_names, best_name, fi_path)

    # 9. Final summary
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE — ALL MODELS SUMMARY")
    print("=" * 70)
    print(f"{'Model':<25} {'Accuracy':>9} {'F1':>9} {'ROC-AUC':>9} {'FAIL Recall':>12}")
    print("─" * 70)
    for r in results:
        marker = " ← BEST" if r["model_name"] == best_name else ""
        print(f"{r['model_name']:<25} {r['accuracy']:>9.4f} {r['f1_weighted']:>9.4f} "
              f"{r['roc_auc']:>9.4f} {r['fail_class_recall']:>12.4f}{marker}")
    print("=" * 70)
    print(f"\nAll artefacts saved to: models/ and reports/")


if __name__ == "__main__":
    main()
