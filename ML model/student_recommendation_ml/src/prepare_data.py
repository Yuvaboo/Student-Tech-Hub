"""
prepare_data.py
---------------
Module for preprocessing data, engineering features, and building leak-free pipelines.
Prepares train/test splits and saves the cleaned dataset.
"""

import os
from typing import Tuple, Dict, Any
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from src.load_data import load_raw_data, DEFAULT_DATA_PATH
except ImportError:
    from load_data import load_raw_data, DEFAULT_DATA_PATH

CLEANED_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "cleaned_dataset.csv",
)

# Explicit feature definitions to prevent data leakage
FEATURE_COLUMNS = [
    "Year",
    "Department",
    "Current_Skills",
    "Interest",
    "Available_Hours_Per_Week",
]

TARGET_COLUMN = "Recommended_Project"

# Excluded columns that represent recommendation outputs or non-predictive IDs
EXCLUDED_COLUMNS = [
    "Student_ID",
    "Recommended_Skills",
    "Recommendation_Reason",
    "Recommended_Tools",
]


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw dataframe:
    - Strips whitespace from string columns
    - Validates data types
    - Checks and handles missing values / duplicates

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe.
    """
    df_clean = df.copy()

    # Strip whitespace from text fields
    string_cols = [
        "Year", "Department", "Current_Skills", "Interest",
        "Recommended_Skills", "Recommended_Project",
        "Recommendation_Reason", "Recommended_Tools"
    ]
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

    # Ensure numeric columns are properly typed
    if "Available_Hours_Per_Week" in df_clean.columns:
        df_clean["Available_Hours_Per_Week"] = pd.to_numeric(
            df_clean["Available_Hours_Per_Week"], errors="coerce"
        )
        # Impute any invalid numerical entries with the median
        if df_clean["Available_Hours_Per_Week"].isnull().any():
            median_hours = df_clean["Available_Hours_Per_Week"].median()
            df_clean["Available_Hours_Per_Week"].fillna(median_hours, inplace=True)

    # Drop exact full-row duplicates if present
    initial_len = len(df_clean)
    df_clean.drop_duplicates(inplace=True)
    dropped = initial_len - len(df_clean)
    if dropped > 0:
        print(f"Dropped {dropped} exact duplicate rows.")

    return df_clean


def build_preprocessor() -> ColumnTransformer:
    """
    Constructs an unfitted scikit-learn ColumnTransformer.
    Applies:
    - OneHotEncoder to nominal categorical features (Year, Department, Interest)
    - TfidfVectorizer to free-text skill list (Current_Skills)
    - StandardScaler to numeric feature (Available_Hours_Per_Week)

    Fitting happens strictly inside the training pipeline to prevent data leakage.

    Returns
    -------
    ColumnTransformer
        Preconfigured scikit-learn transformer.
    """
    categorical_features = ["Year", "Department", "Interest"]
    text_feature = "Current_Skills"
    numerical_features = ["Available_Hours_Per_Week"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
            (
                "text",
                TfidfVectorizer(
                    token_pattern=r"(?u)\b[\w-]+\b",
                    ngram_range=(1, 2),
                    min_df=1,
                ),
                text_feature,
            ),
            (
                "num",
                StandardScaler(),
                numerical_features,
            ),
        ],
        remainder="drop",
    )
    return preprocessor


def extract_project_metadata(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Extracts associated recommendation outputs (Skills, Tools, Reason templates)
    for each Recommended_Project so the prediction interface can display
    comprehensive recommendation packages.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataset containing recommendation columns.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Mapping of project title to its output attributes.
    """
    metadata = {}
    grouped = df.groupby("Recommended_Project")

    for project_name, group in grouped:
        skills = group["Recommended_Skills"].mode().iloc[0]
        tools = group["Recommended_Tools"].mode().iloc[0]
        reasons = group["Recommendation_Reason"].unique().tolist()
        
        # Identify standard base reason
        base_reason = min(reasons, key=len) if reasons else ""

        metadata[project_name] = {
            "skills": skills,
            "tools": tools,
            "base_reason": base_reason,
            "all_reasons": reasons,
        }

    return metadata


def split_data(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Splits features and target into reproducible train and test sets using stratification.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataframe.
    test_size : float
        Proportion of dataset to include in test split (default: 0.2).
    random_state : int
        Seed for reproducibility (default: 42).

    Returns
    -------
    X_train, X_test, y_train, y_test
    """
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    return X_train, X_test, y_train, y_test


def prepare_and_save_data(
    raw_path: str = DEFAULT_DATA_PATH, clean_path: str = CLEANED_DATA_PATH
) -> Tuple[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]]:
    """
    Full preparation pipeline:
    - Loads raw data
    - Cleans data
    - Saves cleaned dataset to disk
    - Performs train/test split

    Returns
    -------
    df_clean, (X_train, X_test, y_train, y_test)
    """
    print(f"Loading raw data from: {raw_path}")
    raw_df = load_raw_data(raw_path)

    print("Cleaning dataset...")
    clean_df = clean_dataset(raw_df)

    os.makedirs(os.path.dirname(clean_path), exist_ok=True)
    clean_df.to_csv(clean_path, index=False)
    print(f"Cleaned dataset saved successfully to: {clean_path} ({len(clean_df):,} rows)")

    X_train, X_test, y_train, y_test = split_data(clean_df)
    print(f"Train/Test split complete: Train={len(X_train):,} samples, Test={len(X_test):,} samples")

    return clean_df, (X_train, X_test, y_train, y_test)


if __name__ == "__main__":
    df_cleaned, (X_tr, X_te, y_tr, y_te) = prepare_and_save_data()
    meta = extract_project_metadata(df_cleaned)
    print(f"Extracted metadata for {len(meta)} unique projects.")
