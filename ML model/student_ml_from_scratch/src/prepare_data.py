"""
Step 3: Prepare Data - Build the sklearn Pipeline
=================================================
Reads the cleaned dataset, defines features + target,
and constructs a preprocessing pipeline (no fitting here
- fitting happens inside train_model.py to avoid leakage).

Run from the project root:
    python src/prepare_data.py
"""

import os
import sys
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.base import BaseEstimator, TransformerMixin

# Paths
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_CSV = os.path.join(BASE_DIR, "data", "cleaned_dataset.csv")

# Feature / Target definitions
CATEGORICAL_FEATURES = ["Year", "Department", "Interest"]
TEXT_FEATURE         = "Current_Skills"
NUMERIC_FEATURE      = "Available_Hours_Per_Week"
TARGET_COLUMN        = "Recommended_Project"

ALL_INPUT_FEATURES = CATEGORICAL_FEATURES + [TEXT_FEATURE, NUMERIC_FEATURE]


class _FlattenThenTfidf(BaseEstimator, TransformerMixin):
    """
    ColumnTransformer passes a 2-D array/DataFrame even for a single column.
    This wrapper flattens it to 1-D before handing it to TfidfVectorizer.
    It also fills NaN values with an empty string.
    """
    def __init__(self, max_features=200, ngram_range=(1, 2), sublinear_tf=True):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.sublinear_tf = sublinear_tf
        self._tfidf = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            sublinear_tf=self.sublinear_tf,
        )

    def _flatten(self, X):
        if hasattr(X, "iloc"):
            col = X.iloc[:, 0]
        elif hasattr(X, "ndim") and X.ndim > 1:
            col = X[:, 0]
        else:
            col = X
        return [str(v) if pd.notna(v) else "" for v in col]

    def fit(self, X, y=None):
        self._tfidf.fit(self._flatten(X))
        return self

    def transform(self, X):
        return self._tfidf.transform(self._flatten(X)).toarray()


def load_clean_data() -> pd.DataFrame:
    if not os.path.exists(CLEAN_CSV):
        print(f"\n[ERROR] Cleaned dataset not found at:\n  {CLEAN_CSV}")
        print("Please run  python src/load_data.py  first.")
        sys.exit(1)
    df = pd.read_csv(CLEAN_CSV)
    print(f"[OK] Cleaned dataset loaded - {len(df):,} rows, {df.shape[1]} columns.")
    return df


def get_X_y(df: pd.DataFrame):
    """Split into feature matrix X and target series y."""
    missing_cols = [c for c in ALL_INPUT_FEATURES + [TARGET_COLUMN]
                    if c not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing columns in dataset: {missing_cols}")
        sys.exit(1)

    X = df[ALL_INPUT_FEATURES].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y


def build_preprocessor() -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
      - OrdinalEncodes categorical columns (Year, Department, Interest)
      - TF-IDF vectorises the free-text Current_Skills column
      - Passes through the numeric Available_Hours_Per_Week column

    Nothing is fitted here - fitting is deferred to the training step
    so there is zero data leakage.
    """
    categorical_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OrdinalEncoder(handle_unknown="use_encoded_value",
                                  unknown_value=-1)),
    ])

    numeric_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
    ])

    text_pipeline = _FlattenThenTfidf(
        max_features=200,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat",  categorical_pipeline, CATEGORICAL_FEATURES),
            ("num",  numeric_pipeline,     [NUMERIC_FEATURE]),
            ("text", text_pipeline,        [TEXT_FEATURE]),
        ],
        remainder="drop",
        sparse_threshold=0,
    )
    return preprocessor


def inspect_prepared_data(X: pd.DataFrame, y: pd.Series) -> None:
    print("\n" + "=" * 60)
    print("  DATA PREPARATION REPORT")
    print("=" * 60)
    print(f"\nFeature matrix shape : {X.shape}")
    print(f"Target series shape  : {y.shape}")
    print(f"\nTarget classes ({y.nunique()} unique):")
    vc = y.value_counts()
    print(vc.head(15).to_string())

    min_count = vc.min()
    print(f"\nSmallest class count : {min_count}")
    if min_count < 2:
        print("  [!] Some classes have fewer than 2 samples.")
        print("      Stratification WILL be disabled during train/test split.")
    else:
        print("  [OK] All classes have >= 2 samples. Stratification is viable.")

    print(f"\nFeature columns used :")
    for f in ALL_INPUT_FEATURES:
        print(f"   * {f}")
    print(f"\nTarget column        : {TARGET_COLUMN}")
    print("\n[OK] Pipeline definition ready. Run  python src/train_model.py  next.\n")


def main():
    df = load_clean_data()
    X, y = get_X_y(df)
    inspect_prepared_data(X, y)


if __name__ == "__main__":
    main()
