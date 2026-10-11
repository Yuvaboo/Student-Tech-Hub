"""
Step 5: Evaluate the Model
===========================
Loads the saved model and held-out test split, computes every metric,
prints a detailed report, and saves results to the reports/ folder.

Also runs an optional regression experiment (Step 6) at the bottom.

Run from the project root:
    python src/evaluate_model.py
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

# Paths
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH      = os.path.join(BASE_DIR, "models", "student_project_model.pkl")
SPLIT_PATH      = os.path.join(BASE_DIR, "models", "_test_split.pkl")
CLEAN_CSV       = os.path.join(BASE_DIR, "data", "cleaned_dataset.csv")
EVAL_JSON       = os.path.join(BASE_DIR, "reports", "evaluation_results.json")
CLF_REPORT_TXT  = os.path.join(BASE_DIR, "reports", "classification_report.txt")
REGRESSION_TXT  = os.path.join(BASE_DIR, "reports", "regression_report.txt")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepare_data import get_X_y, load_clean_data, TARGET_COLUMN


def evaluate_classification():
    print("=" * 65)
    print("  STEP 5: MODEL EVALUATION - CLASSIFICATION")
    print("=" * 65)

    # 1. Load model
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model not found: {MODEL_PATH}")
        print("Run  python src/train_model.py  first.")
        sys.exit(1)
    pipeline = joblib.load(MODEL_PATH)
    print(f"\n[OK] Model loaded from:\n   {MODEL_PATH}")

    # 2. Load split
    if not os.path.exists(SPLIT_PATH):
        print(f"[ERROR] Test split not found: {SPLIT_PATH}")
        print("Run  python src/train_model.py  first.")
        sys.exit(1)
    X_test, y_test = joblib.load(SPLIT_PATH)
    print(f"[OK] Test split loaded - {len(X_test):,} rows")

    # 3. Reload full dataset to evaluate training split
    df = load_clean_data()
    X_all, y_all = get_X_y(df)

    from sklearn.model_selection import train_test_split
    min_count = y_all.value_counts().min()
    stratify  = y_all if min_count >= 2 else None
    X_train, _, y_train, _ = train_test_split(
        X_all, y_all, test_size=0.20, random_state=42, stratify=stratify
    )

    # 4. Predictions
    y_pred_train = pipeline.predict(X_train)
    y_pred_test  = pipeline.predict(X_test)

    # 5. Metrics
    train_acc   = accuracy_score(y_train, y_pred_train)
    test_acc    = accuracy_score(y_test,  y_pred_test)
    precision   = precision_score(y_test,  y_pred_test, average="weighted", zero_division=0)
    recall      = recall_score(y_test,    y_pred_test, average="weighted", zero_division=0)
    f1          = f1_score(y_test,        y_pred_test, average="weighted", zero_division=0)
    cm          = confusion_matrix(y_test, y_pred_test)
    clf_report  = classification_report(y_test, y_pred_test, zero_division=0)

    print(f"\n-- Metrics --------------------------------------------------")
    print(f"   Training accuracy : {train_acc:.4f}  ({train_acc*100:.2f}%)")
    print(f"   Test accuracy     : {test_acc:.4f}  ({test_acc*100:.2f}%)")
    print(f"   Precision (wtd)   : {precision:.4f}")
    print(f"   Recall    (wtd)   : {recall:.4f}")
    print(f"   F1-score  (wtd)   : {f1:.4f}")

    gap = train_acc - test_acc
    print(f"\n-- Overfitting Check ----------------------------------------")
    if gap > 0.15:
        print(f"   [!] Train-test gap = {gap:.4f} - OVERFITTING detected.")
        print("   The model memorised aspects of the training data.")
    elif abs(gap) <= 0.05:
        print(f"   [OK] Train-test gap = {gap:.4f} - No significant overfitting.")
    else:
        print(f"   [i] Train-test gap = {gap:.4f} - Mild gap; acceptable for complex data.")

    print(f"\n-- Confusion Matrix (Shape: {cm.shape}) ----------------------")
    if cm.shape[0] <= 10:
        print(cm)
    else:
        print(f"   Confusion matrix calculated for {cm.shape[0]} classes.")
        print("   Saved in reports/evaluation_results.json.")

    print(f"\n-- Full Classification Report -------------------------------")
    print(clf_report)

    # Synthetic data warning
    print("-- Notice Regarding Synthetic Data --------------------------")
    print("   This dataset is synthetically generated. Metrics reflect")
    print("   statistical alignment with synthetic rules, not real-world")
    print("   recommendation efficacy.")

    # Save reports
    os.makedirs(os.path.dirname(EVAL_JSON), exist_ok=True)

    results = {
        "model"             : str(pipeline.named_steps["classifier"].__class__.__name__),
        "training_accuracy" : round(float(train_acc),   4),
        "test_accuracy"     : round(float(test_acc),    4),
        "precision_weighted": round(float(precision),   4),
        "recall_weighted"   : round(float(recall),      4),
        "f1_weighted"       : round(float(f1),          4),
        "train_test_gap"    : round(float(gap),         4),
        "confusion_matrix"  : cm.tolist(),
        "note"              : (
            "Dataset is synthetic. Metrics describe fit to synthetic "
            "rules only and do not establish real-world project quality."
        ),
    }
    with open(EVAL_JSON, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"\n[OK] Evaluation results saved to:\n   {EVAL_JSON}")

    with open(CLF_REPORT_TXT, "w", encoding="utf-8") as fh:
        fh.write("STUDENT PROJECT RECOMMENDATION MODEL\n")
        fh.write("Classification Report\n")
        fh.write("=" * 65 + "\n\n")
        fh.write(clf_report)
        fh.write(
            "\nNOTE: Dataset is synthetic. Results reflect fit to "
            "generated data, not real recommendation quality.\n"
        )
    print(f"[OK] Classification report saved to:\n   {CLF_REPORT_TXT}")

    return results


def evaluate_regression():
    """
    Predict Available_Hours_Per_Week from student characteristics.
    """
    print("\n" + "=" * 65)
    print("  STEP 6: REGRESSION EXPERIMENT (Available_Hours_Per_Week)")
    print("=" * 65)

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OrdinalEncoder
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline as SKPipeline
    from prepare_data import _FlattenThenTfidf

    REGRESSION_TARGET = "Available_Hours_Per_Week"
    REG_FEATURES      = ["Year", "Department", "Current_Skills",
                         "Interest", "Recommended_Project"]

    df = load_clean_data()
    if REGRESSION_TARGET not in df.columns:
        print(f"[SKIP] Column '{REGRESSION_TARGET}' not found in dataset.")
        return

    available_features = [c for c in REG_FEATURES if c in df.columns]
    X_reg = df[available_features].copy()
    y_reg = df[REGRESSION_TARGET].copy()

    print(f"\n   Target feature : {REGRESSION_TARGET}")
    print(f"   Input features : {available_features}")
    print(f"   Target range   : {y_reg.min()} - {y_reg.max()}")
    print(f"   Target mean    : {y_reg.mean():.2f}")
    print(f"   Target std     : {y_reg.std():.2f}")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_reg, y_reg, test_size=0.20, random_state=42
    )

    cat_cols  = [c for c in available_features if c != "Current_Skills"]
    text_cols = [c for c in ["Current_Skills"] if c in available_features]

    transformers = [
        ("cat", SKPipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("enc", OrdinalEncoder(handle_unknown="use_encoded_value",
                                   unknown_value=-1)),
        ]), cat_cols),
    ]
    if text_cols:
        transformers.append(
            ("text", _FlattenThenTfidf(max_features=100), text_cols)
        )

    pre = ColumnTransformer(transformers=transformers,
                            remainder="drop",
                            sparse_threshold=0)

    reg_pipeline = SKPipeline([
        ("pre", pre),
        ("reg", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)),
    ])
    reg_pipeline.fit(X_tr, y_tr)
    y_pred_reg = reg_pipeline.predict(X_te)

    mae  = mean_absolute_error(y_te, y_pred_reg)
    rmse = np.sqrt(mean_squared_error(y_te, y_pred_reg))
    r2   = r2_score(y_te, y_pred_reg)

    print(f"\n-- Regression Metrics ---------------------------------------")
    print(f"   MAE  : {mae:.3f} hours")
    print(f"   RMSE : {rmse:.3f} hours")
    print(f"   R2   : {r2:.4f}")

    print(f"\n-- Interpretation -------------------------------------------")
    if r2 < 0.10:
        print("   R2 is near zero - student characteristics have virtually no")
        print("   predictive relationship with Available_Hours_Per_Week in this dataset.")
        print("   This confirms that hours were generated independently of other features.")
        verdict = "Low predictive relationship (R2 near zero)."
    elif r2 < 0.40:
        print("   R2 is modest. Some weak signal detected, but insufficient for reliable predictions.")
        verdict = "Moderate/weak relationship."
    else:
        print(f"   Meaningful relationship detected (R2 = {r2:.4f}).")
        verdict = f"Reasonable relationship (R2 = {r2:.4f})."

    reg_summary = {
        "target"  : REGRESSION_TARGET,
        "features": available_features,
        "MAE"     : round(mae,  3),
        "RMSE"    : round(rmse, 3),
        "R2"      : round(r2,   4),
        "verdict" : verdict,
    }
    with open(REGRESSION_TXT, "w", encoding="utf-8") as fh:
        fh.write("REGRESSION EXPERIMENT - Available_Hours_Per_Week\n")
        fh.write("=" * 65 + "\n\n")
        fh.write(f"MAE   : {mae:.3f} hours\n")
        fh.write(f"RMSE  : {rmse:.3f} hours\n")
        fh.write(f"R2    : {r2:.4f}\n\n")
        fh.write(f"Verdict: {verdict}\n\n")
        fh.write("NOTE: Regression is kept completely separate from the project recommendation classifier.\n")
    print(f"\n[OK] Regression report saved to:\n   {REGRESSION_TXT}")
    return reg_summary


def main():
    evaluate_classification()
    evaluate_regression()
    print("\n" + "=" * 65)
    print("  Evaluation complete. Run: python src/predict.py")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
