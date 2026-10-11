"""
Step 4: Train the Model
========================
Builds and trains a full sklearn Pipeline (preprocessing + classifier),
evaluates on a held-out test set, and saves the pipeline to disk.

Two models are compared:
  1. Logistic Regression  (baseline)
  2. Random Forest        (usually stronger for multi-class text tasks)

The better model is saved.

Run from the project root:
    python src/train_model.py
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepare_data import (
    load_clean_data, get_X_y, build_preprocessor,
    ALL_INPUT_FEATURES, TARGET_COLUMN,
)

# Paths
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "student_project_model.pkl")


def make_pipeline(preprocessor, classifier) -> Pipeline:
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   classifier),
    ])


def train_and_evaluate(name: str, pipeline: Pipeline,
                       X_train, X_test, y_train, y_test) -> float:
    print(f"\n-- Training: {name} ------------------------------------------")
    pipeline.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, pipeline.predict(X_train))
    test_acc  = accuracy_score(y_test,  pipeline.predict(X_test))

    print(f"   Training accuracy : {train_acc:.4f} ({train_acc*100:.2f}%)")
    print(f"   Test     accuracy : {test_acc:.4f}  ({test_acc*100:.2f}%)")
    gap = train_acc - test_acc
    if gap > 0.15:
        print(f"   [!] Gap = {gap:.4f} - potential overfitting observed.")
    elif gap < 0.0:
        print("   [i] Test acc slightly above train acc - due to sample distribution.")
    else:
        print(f"   [OK] Train-test gap = {gap:.4f} - healthy balance.")
    return test_acc


def main():
    print("=" * 65)
    print("  STEP 4: MODEL TRAINING")
    print("=" * 65)

    # 1. Load data
    df = load_clean_data()
    X, y = get_X_y(df)

    # 2. Decide stratification
    min_class_count = y.value_counts().min()
    use_stratify    = min_class_count >= 2
    stratify_arg    = y if use_stratify else None
    print(f"\n[INFO] Stratification: {'ENABLED' if use_stratify else 'DISABLED'} "
          f"(smallest class has {min_class_count} sample(s)).")

    # 3. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=stratify_arg,
    )
    print(f"[INFO] Training set : {len(X_train):,} rows")
    print(f"[INFO] Test set     : {len(X_test):,} rows")

    # 4. Build pipelines
    pre1 = build_preprocessor()
    pre2 = build_preprocessor()

    lr_pipeline = make_pipeline(
        pre1,
        LogisticRegression(
            max_iter=1000,
            random_state=42,
            solver="lbfgs",
            C=1.0,
        ),
    )

    rf_pipeline = make_pipeline(
        pre2,
        RandomForestClassifier(
            n_estimators=150,
            max_depth=None,
            random_state=42,
            n_jobs=-1,
        ),
    )

    # 5. Train both and compare
    lr_acc = train_and_evaluate("Logistic Regression", lr_pipeline,
                                X_train, X_test, y_train, y_test)
    rf_acc = train_and_evaluate("Random Forest",       rf_pipeline,
                                X_train, X_test, y_train, y_test)

    # 6. Pick the better model
    print("\n-- Model Selection ------------------------------------------")
    if rf_acc >= lr_acc:
        best_pipeline = rf_pipeline
        best_name     = "Random Forest"
        best_acc      = rf_acc
    else:
        best_pipeline = lr_pipeline
        best_name     = "Logistic Regression"
        best_acc      = lr_acc

    print(f"   Selected Best Model: {best_name} (test acc = {best_acc:.4f})")

    # 7. Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"\n[OK] Model saved to:\n   {MODEL_PATH}")

    # 8. Save split info for evaluate_model.py
    split_path = os.path.join(BASE_DIR, "models", "_test_split.pkl")
    joblib.dump((X_test, y_test), split_path)
    print(f"[OK] Test split saved to:\n   {split_path}")

    print("\n" + "=" * 65)
    print("  Training complete. Run: python src/evaluate_model.py")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
