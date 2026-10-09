"""
load_data.py
------------
Module for loading, validating, and inspecting the Student Recommendation Dataset.
Ensures data integrity, checks expected columns, and handles errors gracefully.
"""

import os
from typing import Dict, Any, Tuple
import pandas as pd

EXPECTED_COLUMNS = [
    "Student_ID",
    "Year",
    "Department",
    "Current_Skills",
    "Interest",
    "Available_Hours_Per_Week",
    "Recommended_Skills",
    "Recommended_Project",
    "Recommendation_Reason",
    "Recommended_Tools",
]

DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "student_recommendation_10000_no_difficulty.csv",
)


def load_raw_data(filepath: str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """
    Loads raw CSV dataset from the specified file path and performs validation.

    Parameters
    ----------
    filepath : str
        Path to the CSV dataset file.

    Returns
    -------
    pd.DataFrame
        Loaded pandas DataFrame.

    Raises
    ------
    FileNotFoundError
        If dataset file does not exist at the given path.
    ValueError
        If required columns are missing from the dataset.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Dataset not found at '{filepath}'. Please verify the file path."
        )

    df = pd.read_csv(filepath)

    # Validate column names
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset is missing required columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    return df


def inspect_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspects dataset characteristics including shapes, missing values,
    duplicates, and categorical/numerical distributions.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset to inspect.

    Returns
    -------
    Dict[str, Any]
        Dictionary of inspection findings.
    """
    inspection = {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {col: int(count) for col, count in df.isnull().sum().items()},
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_student_ids": int(df["Student_ID"].duplicated().sum()) if "Student_ID" in df.columns else 0,
        "unique_projects": int(df["Recommended_Project"].nunique()) if "Recommended_Project" in df.columns else 0,
        "unique_years": list(df["Year"].unique()) if "Year" in df.columns else [],
        "unique_departments": list(df["Department"].unique()) if "Department" in df.columns else [],
        "unique_interests_count": int(df["Interest"].nunique()) if "Interest" in df.columns else 0,
        "available_hours_stats": df["Available_Hours_Per_Week"].describe().to_dict() if "Available_Hours_Per_Week" in df.columns else {},
    }
    return inspection


def print_inspection_report(summary: Dict[str, Any]) -> None:
    """
    Prints a readable console summary of the dataset inspection.
    """
    print("=" * 60)
    print("  STUDENT RECOMMENDATION DATASET - INSPECTION REPORT")
    print("=" * 60)
    print(f"Total Records:      {summary['total_rows']:,}")
    print(f"Total Columns:      {summary['total_columns']}")
    print(f"Duplicate Rows:     {summary['duplicate_rows']}")
    print(f"Duplicate IDs:      {summary['duplicate_student_ids']}")
    print(f"Unique Projects:    {summary['unique_projects']}")
    print(f"Academic Years:     {summary['unique_years']}")
    print(f"Departments ({len(summary['unique_departments'])}):   {summary['unique_departments']}")
    print(f"Interests Count:    {summary['unique_interests_count']}")
    
    print("\nMissing Values per Column:")
    for col, count in summary["missing_values"].items():
        status = "None (0)" if count == 0 else f"{count} missing"
        print(f"  - {col:<26}: {status}")

    print("\nAvailable Hours per Week Summary:")
    stats = summary.get("available_hours_stats", {})
    if stats:
        print(f"  - Min: {stats.get('min', 'N/A')} hrs/wk | "
              f"Mean: {stats.get('mean', 0):.2f} hrs/wk | "
              f"Median: {stats.get('50%', 'N/A')} hrs/wk | "
              f"Max: {stats.get('max', 'N/A')} hrs/wk | "
              f"Std: {stats.get('std', 0):.2f}")
    print("=" * 60)


if __name__ == "__main__":
    print(f"Loading dataset from: {DEFAULT_DATA_PATH}")
    dataset = load_raw_data()
    report = inspect_data(dataset)
    print_inspection_report(report)
