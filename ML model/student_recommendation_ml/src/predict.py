"""
predict.py
----------
Inference module for recommending suitable projects, skills, tools, and explanations
for incoming student profiles.
Can be imported as a library or executed from the command line.
"""

import os
import sys
import argparse
import joblib
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "student_project_model.pkl",
)


class StudentProjectRecommender:
    """
    Wrapper around the trained scikit-learn recommendation pipeline.
    Loads model artifact once, validates student inputs, and formats recommendations.
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Trained model not found at '{model_path}'. "
                "Please run 'python src/train_model.py' to generate the model artifact."
            )
        self.artifact = joblib.load(model_path)
        self.pipeline = self.artifact["pipeline"]
        self.feature_columns = self.artifact.get(
            "feature_columns",
            ["Year", "Department", "Current_Skills", "Interest", "Available_Hours_Per_Week"],
        )
        self.project_metadata = self.artifact.get("project_metadata", {})
        self.unique_years = self.artifact.get("unique_years", [])
        self.unique_departments = self.artifact.get("unique_departments", [])
        self.unique_interests = self.artifact.get("unique_interests", [])

    def validate_and_clean_input(self, profile: Dict[str, Any]) -> pd.DataFrame:
        """
        Validates, cleans, and standardizes user inputs to avoid inference failures.
        """
        # Validate or default Year
        year = str(profile.get("Year", "1st Year")).strip()
        if not year:
            year = "1st Year"

        # Validate or default Department
        department = str(profile.get("Department", "General")).strip()
        if not department:
            department = "General"

        # Validate Current_Skills
        current_skills = str(profile.get("Current_Skills", "")).strip()
        if not current_skills:
            current_skills = "Basics"

        # Validate Interest
        interest = str(profile.get("Interest", "Computer Science")).strip()
        if not interest:
            interest = "Computer Science"

        # Validate Available_Hours_Per_Week
        try:
            hours = float(profile.get("Available_Hours_Per_Week", 10))
            if hours < 1:
                hours = 1.0
            elif hours > 60:
                hours = 60.0
        except (ValueError, TypeError):
            hours = 10.0

        cleaned_dict = {
            "Year": [year],
            "Department": [department],
            "Current_Skills": [current_skills],
            "Interest": [interest],
            "Available_Hours_Per_Week": [hours],
        }

        return pd.DataFrame(cleaned_dict)[self.feature_columns]

    def predict(
        self, profile: Dict[str, Any], top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive project recommendation for a student.

        Parameters
        ----------
        profile : Dict[str, Any]
            Student profile with keys:
            - 'Year'
            - 'Department'
            - 'Current_Skills'
            - 'Interest'
            - 'Available_Hours_Per_Week'
        top_k : int
            Number of top candidate projects to return (default: 3).

        Returns
        -------
        Dict[str, Any]
            Recommendation package including project name, confidence,
            associated skills, tools, and personalized reason.
        """
        input_df = self.validate_and_clean_input(profile)

        # Predict primary project
        predicted_project = self.pipeline.predict(input_df)[0]

        # Get probabilities if supported
        confidence = 1.0
        top_candidates = []
        if hasattr(self.pipeline, "predict_proba"):
            try:
                probs = self.pipeline.predict_proba(input_df)[0]
                classes = self.pipeline.classes_
                sorted_indices = np.argsort(probs)[::-1]
                confidence = float(probs[sorted_indices[0]])

                for idx in sorted_indices[:top_k]:
                    candidate_name = classes[idx]
                    cand_meta = self.project_metadata.get(candidate_name, {})
                    top_candidates.append({
                        "project": candidate_name,
                        "probability": round(float(probs[idx]), 4),
                        "recommended_skills": cand_meta.get("skills", "N/A"),
                    })
            except Exception:
                pass

        # Retrieve associated metadata
        meta = self.project_metadata.get(predicted_project, {})
        recommended_skills = meta.get("skills", "Technical foundations, domain tools")
        recommended_tools = meta.get("tools", "Standard developer toolchain")

        # Synthesize adaptive reason based on student's available hours
        student_hours = input_df["Available_Hours_Per_Week"].iloc[0]
        base_reason = meta.get("base_reason", "Build practical experience and apply core concepts.")
        
        # If student has 12+ hours, extend the reason contextually
        if student_hours >= 12 and "available time supports a broader extension" not in base_reason:
            recommendation_reason = f"{base_reason}; available time supports a broader extension."
        else:
            recommendation_reason = base_reason

        return {
            "recommended_project": predicted_project,
            "confidence": round(confidence, 4),
            "recommended_skills": recommended_skills,
            "recommended_tools": recommended_tools,
            "recommendation_reason": recommendation_reason,
            "student_inputs": {
                "Year": input_df["Year"].iloc[0],
                "Department": input_df["Department"].iloc[0],
                "Current_Skills": input_df["Current_Skills"].iloc[0],
                "Interest": input_df["Interest"].iloc[0],
                "Available_Hours_Per_Week": float(student_hours),
            },
            "top_candidates": top_candidates,
        }


def format_recommendation_cli(rec: Dict[str, Any]) -> str:
    """Formats recommendation dictionary into an aesthetic CLI card."""
    lines = [
        "=" * 60,
        "          PROJECT & SKILL RECOMMENDATION RESULT",
        "=" * 60,
        f"Recommended Project :  {rec['recommended_project']}",
        f"Confidence Score    :  {rec['confidence'] * 100:.1f}%",
        f"Recommended Skills  :  {rec['recommended_skills']}",
        f"Recommended Tools   :  {rec['recommended_tools']}",
        f"Recommendation Rationale:",
        f"  \"{rec['recommendation_reason']}\"",
        "-" * 60,
        "Student Profile Received:",
        f"  - Year:            {rec['student_inputs']['Year']}",
        f"  - Department:      {rec['student_inputs']['Department']}",
        f"  - Current Skills:  {rec['student_inputs']['Current_Skills']}",
        f"  - Interest:        {rec['student_inputs']['Interest']}",
        f"  - Weekly Hours:    {rec['student_inputs']['Available_Hours_Per_Week']} hrs/wk",
        "=" * 60,
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict recommended project and skills for a student.")
    parser.add_argument("--year", type=str, default="3rd Year", help="Academic Year (e.g. '3rd Year')")
    parser.add_argument("--dept", type=str, default="CSE", help="Department (e.g. 'CSE', 'IT', 'ECE')")
    parser.add_argument("--skills", type=str, default="Python, pandas", help="Current Skills (comma-separated)")
    parser.add_argument("--interest", type=str, default="Data Science", help="Interest (e.g. 'Data Science')")
    parser.add_argument("--hours", type=float, default=15.0, help="Available hours per week (e.g. 15)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH, help="Path to model .pkl file")

    args = parser.parse_args()

    recommender = StudentProjectRecommender(model_path=args.model)
    student_profile = {
        "Year": args.year,
        "Department": args.dept,
        "Current_Skills": args.skills,
        "Interest": args.interest,
        "Available_Hours_Per_Week": args.hours,
    }

    result = recommender.predict(student_profile)
    print(format_recommendation_cli(result))
