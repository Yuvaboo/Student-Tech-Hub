"""
Step 2: Load and Inspect the Dataset
======================================
This script loads the student recommendation CSV, performs a full
inspection, reports all findings honestly, and saves a cleaned copy.

Run from the project root:
    python src/load_data.py
"""

import os
import sys
import pandas as pd

# Paths
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV   = os.path.join(BASE_DIR, "data", "student_recommendation_10000_no_difficulty.csv")
CLEAN_CSV = os.path.join(BASE_DIR, "data", "cleaned_dataset.csv")


def load_and_inspect(csv_path: str) -> pd.DataFrame:
    """Load the CSV, print a full inspection report, and return the cleaned DataFrame."""

    # 1. Check file exists
    if not os.path.exists(csv_path):
        print(f"\n[ERROR] Dataset not found at:\n  {csv_path}")
        print("\nPlease copy student_recommendation_10000_no_difficulty.csv")
        print(f"into:  {os.path.join(BASE_DIR, 'data')}")
        sys.exit(1)

    print("=" * 65)
    print("  STUDENT RECOMMENDATION DATASET - INSPECTION REPORT")
    print("=" * 65)

    # 2. Load
    df = pd.read_csv(csv_path)
    print(f"\n[OK] File loaded: {csv_path}")

    # 3. Shape
    print(f"\n-- Shape -----------------------------------------------------")
    print(f"   Rows   : {df.shape[0]:,}")
    print(f"   Columns: {df.shape[1]}")

    # 4. Column names & dtypes
    print(f"\n-- Columns & Data Types ---------------------------------------")
    for col, dtype in df.dtypes.items():
        print(f"   {col:<35} {str(dtype)}")

    # 5. First few rows
    print(f"\n-- First 3 Rows -----------------------------------------------")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    print(df.head(3).to_string(index=False))

    # 6. Missing values
    print(f"\n-- Missing Values ---------------------------------------------")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("   No missing values found. [OK]")
    else:
        print(missing[missing > 0].to_string())

    # 7. Duplicates
    n_dup = df.duplicated().sum()
    print(f"\n-- Duplicate Rows ---------------------------------------------")
    print(f"   Duplicate rows found: {n_dup}")

    # 8. Target column verification
    target = "Recommended_Project"
    print(f"\n-- Target Column: '{target}' -----------------------------------")
    if target not in df.columns:
        print(f"   [ERROR] Column '{target}' is MISSING from the dataset!")
        print("   Available columns:", list(df.columns))
        sys.exit(1)

    n_classes = df[target].nunique()
    print(f"   Target column verified: EXISTS [OK]")
    print(f"   Unique classes : {n_classes}")
    print(f"\n   Class distribution (top 15):")
    dist = df[target].value_counts()
    print(dist.head(15).to_string())
    pct_min = dist.min() / len(df) * 100
    pct_max = dist.max() / len(df) * 100
    print(f"\n   Smallest class : {dist.idxmin()!r} ({dist.min()} rows, {pct_min:.2f}%)")
    print(f"   Largest  class : {dist.idxmax()!r} ({dist.max()} rows, {pct_max:.2f}%)")

    # 9. Feature columns check
    required_features = ["Year", "Department", "Current_Skills",
                         "Interest", "Available_Hours_Per_Week"]
    print(f"\n-- Required Feature Columns -----------------------------------")
    all_present = True
    for col in required_features:
        present = col in df.columns
        mark = "[OK]" if present else "[MISSING]"
        print(f"   {mark:<9}  {col}")
        if not present:
            all_present = False
    if not all_present:
        print("\n[ERROR] One or more required feature columns are missing.")
        sys.exit(1)

    # 10. Clean
    df_clean = df.drop_duplicates().copy()
    cols_needed = required_features + [target]
    before = len(df_clean)
    df_clean = df_clean.dropna(subset=cols_needed)
    after = len(df_clean)
    dropped = before - after
    print(f"\n-- Cleaning Summary -------------------------------------------")
    print(f"   Duplicate rows removed : {n_dup}")
    print(f"   Rows with null dropped : {dropped}")
    print(f"   Final dataset size     : {after:,} rows")

    return df_clean


def save_cleaned(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"\n[OK] Cleaned dataset saved to:\n   {path}")


def main():
    df_clean = load_and_inspect(RAW_CSV)
    save_cleaned(df_clean, CLEAN_CSV)
    print("\n" + "=" * 65)
    print("  Data inspection complete. Proceed to: python src/prepare_data.py")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
