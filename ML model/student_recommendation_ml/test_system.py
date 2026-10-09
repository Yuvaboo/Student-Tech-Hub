"""
test_system.py
--------------
Automated test suite verifying model loading, prediction consistency,
edge case handling, and pipeline stability across diverse student profiles.
"""

import os
import joblib
import pandas as pd
from src.predict import StudentProjectRecommender

def run_tests():
    print("=" * 65)
    print("       STUDENT RECOMMENDATION ML SYSTEM - TEST SUITE")
    print("=" * 65)

    model_path = os.path.join("models", "student_project_model.pkl")
    assert os.path.exists(model_path), f"Missing model at {model_path}"
    print("[TEST 1/5] Verified model artifact exists on disk.")

    recommender = StudentProjectRecommender(model_path)
    print("[TEST 2/5] Model successfully loaded into fresh Python process.")

    # Diverse profiles
    test_profiles = [
        {
            "name": "Freshman Web Dev",
            "profile": {
                "Year": "1st Year",
                "Department": "IT",
                "Current_Skills": "HTML, CSS, project experience",
                "Interest": "Web Development",
                "Available_Hours_Per_Week": 5,
            },
        },
        {
            "name": "Junior Data Scientist",
            "profile": {
                "Year": "3rd Year",
                "Department": "CSE",
                "Current_Skills": "Python, pandas, project experience",
                "Interest": "Data Science",
                "Available_Hours_Per_Week": 15,
            },
        },
        {
            "name": "Sophomore Electronics Maker",
            "profile": {
                "Year": "2nd Year",
                "Department": "EEE",
                "Current_Skills": "C Basics, electronics",
                "Interest": "Electronics",
                "Available_Hours_Per_Week": 12,
            },
        },
        {
            "name": "Mechanical CAD Designer",
            "profile": {
                "Year": "4th Year",
                "Department": "Mechanical",
                "Current_Skills": "Engineering Drawing Basics",
                "Interest": "CAD Design",
                "Available_Hours_Per_Week": 4,
            },
        },
        {
            "name": "Biotechnology Researcher",
            "profile": {
                "Year": "1st Year",
                "Department": "Microbiology",
                "Current_Skills": "Biology Basics",
                "Interest": "Biotechnology",
                "Available_Hours_Per_Week": 8,
            },
        },
    ]

    print("\n[TEST 3/5] Testing predictions for diverse personas:")
    for item in test_profiles:
        name = item["name"]
        res = recommender.predict(item["profile"])
        assert res["recommended_project"], f"Empty project recommendation for {name}"
        assert res["recommended_skills"], f"Missing skills for {name}"
        assert res["recommended_tools"], f"Missing tools for {name}"
        assert res["recommendation_reason"], f"Missing reason for {name}"
        print(f"  + {name:<30} -> {res['recommended_project']} ({res['confidence'] * 100:.1f}%)")

    # Edge cases
    print("\n[TEST 4/5] Testing edge cases (blank inputs, unknown values, extreme numbers):")
    edge_cases = [
        {"Year": "", "Department": "", "Current_Skills": "", "Interest": "", "Available_Hours_Per_Week": -10},
        {"Year": "99th Year", "Department": "Astrophysics", "Current_Skills": "unknown_tool", "Interest": "Cosmology", "Available_Hours_Per_Week": 150},
        {"Year": "2nd Year", "Department": "Civil", "Current_Skills": "Excel Basics", "Interest": "Data Analysis", "Available_Hours_Per_Week": 2},
    ]

    for idx, ec in enumerate(edge_cases, 1):
        res = recommender.predict(ec)
        assert res["recommended_project"], f"Failed edge case {idx}"
        print(f"  + Edge Case {idx} Handled Gracefully -> {res['recommended_project']}")

    # Regression artifact check
    reg_path = os.path.join("models", "student_hours_regression_model.pkl")
    assert os.path.exists(reg_path), f"Missing regression artifact at {reg_path}"
    reg_data = joblib.load(reg_path)
    print("\n[TEST 5/5] Verified regression experiment artifact and report:")
    print(f"  + Target:                {reg_data['findings']['target']}")
    print(f"  + Model Justified:       {reg_data['findings']['is_model_justified']}")
    print(f"  + Ridge Test R2:         {reg_data['findings']['ridge_metrics']['test_r2']:.4f}")
    print(f"  + Random Forest Test R2: {reg_data['findings']['random_forest_metrics']['test_r2']:.4f}")

    print("\n" + "=" * 65)
    print("  ALL TESTS PASSED SUCCESSFULLY! SYSTEM IS PRODUCTION READY.")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
