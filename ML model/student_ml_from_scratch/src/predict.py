"""
Step 7: Predict - Personalized Student Project Recommendations
===============================================================
Loads the trained ML model and returns the TOP-K (default 5) personalized
project recommendations for a student profile based on:
  - Year
  - Department
  - Current skills
  - Primary interest
  - Available hours per week

For each recommendation, the system provides:
  - Project name
  - Required skills
  - Difficulty level
  - Estimated duration
  - Why the project matches the student
  - Recommended tools
  - Mathematically valid relevance scores (Random Forest ensemble probabilities)
  - Content-based profile similarity fallback when ML class diversity is limited

Usage:
    python src/predict.py
"""

import os
import sys
import re
import joblib
import numpy as np
import pandas as pd

# ── Dynamic Path Resolution ──────────────────────────────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == "src" else CURRENT_DIR

# Ensure 'src' is in sys.path so pickled custom transformers can be unpickled
SRC_DIR = os.path.join(BASE_DIR, "src") if os.path.isdir(os.path.join(BASE_DIR, "src")) else BASE_DIR
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

MODEL_PATH = os.path.join(BASE_DIR, "models", "student_project_model.pkl")
DATA_PATH = os.path.join(BASE_DIR, "data", "cleaned_dataset.csv")

# Feature order matches pipeline expectation
FEATURE_COLUMNS = [
    "Year",
    "Department",
    "Current_Skills",
    "Interest",
    "Available_Hours_Per_Week",
]

_CACHED_CATALOG = None
_CACHED_MODEL = None


def load_model(path: str = None):
    """Load the trained pipeline from disk (cached in memory)."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL

    target_path = path or MODEL_PATH
    if not os.path.exists(target_path):
        # Fallback search
        alt_paths = [
            os.path.join(os.getcwd(), "models", "student_project_model.pkl"),
            os.path.join(os.getcwd(), "student_ml_from_scratch", "models", "student_project_model.pkl"),
            os.path.join(BASE_DIR, "..", "models", "student_project_model.pkl"),
        ]
        for p in alt_paths:
            if os.path.exists(p):
                target_path = p
                break

    if not os.path.exists(target_path):
        raise FileNotFoundError(
            f"Trained model not found at:\n  {target_path}\n"
            "Please run  python src/train_model.py  first."
        )

    _CACHED_MODEL = joblib.load(target_path)
    return _CACHED_MODEL


def tokenize(text: str) -> set:
    """Extract lowercase alphanumeric tokens from text."""
    if not text:
        return set()
    return set(re.findall(r"\b[a-zA-Z0-9_]+\b", str(text).lower()))


def get_project_catalog() -> dict:
    """
    Extract and cache all unique projects and their ground-truth metadata
    from the cleaned dataset.
    """
    global _CACHED_CATALOG
    if _CACHED_CATALOG is not None:
        return _CACHED_CATALOG

    csv_path = DATA_PATH
    if not os.path.exists(csv_path):
        alt_paths = [
            os.path.join(os.getcwd(), "data", "cleaned_dataset.csv"),
            os.path.join(os.getcwd(), "student_ml_from_scratch", "data", "cleaned_dataset.csv"),
            os.path.join(BASE_DIR, "data", "student_recommendation_10000_no_difficulty.csv"),
        ]
        for p in alt_paths:
            if os.path.exists(p):
                csv_path = p
                break

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}. Please run src/load_data.py first.")

    df = pd.read_csv(csv_path)
    catalog = {}
    for proj, group in df.groupby("Recommended_Project"):
        req_skills = str(group["Recommended_Skills"].mode()[0]) if not group["Recommended_Skills"].empty else "N/A"
        tools = str(group["Recommended_Tools"].mode()[0]) if not group["Recommended_Tools"].empty else "N/A"
        base_reason = str(group["Recommendation_Reason"].mode()[0]) if not group["Recommendation_Reason"].empty else "Structured academic capstone project."
        depts = [str(d) for d in group["Department"].dropna().unique()]
        interests = [str(i) for i in group["Interest"].dropna().unique()]
        years = [str(y) for y in group["Year"].dropna().unique()]
        avg_hrs = float(group["Available_Hours_Per_Week"].mean())

        # Determine realistic difficulty level based on domain and technical depth
        sk_lower = req_skills.lower()
        tl_lower = tools.lower()
        if any(k in sk_lower or k in tl_lower for k in [
            "scikit-learn", "deep learning", "vector database", "simulation",
            "privacy, bias", "control logic", "ml evaluation", "computer vision"
        ]):
            diff = "Advanced"
            typical_effort_hours = 90
        elif any(k in sk_lower or k in tl_lower for k in [
            "pandas", "matplot", "rest api", "api", "microcontroller",
            "cad", "qgis", "statistics", "crud", "mqtt", "database"
        ]):
            diff = "Intermediate"
            typical_effort_hours = 60
        else:
            diff = "Beginner"
            typical_effort_hours = 35

        catalog[proj] = {
            "project_name": proj,
            "required_skills": req_skills,
            "recommended_tools": tools,
            "base_reason": base_reason,
            "departments": depts,
            "interests": interests,
            "years": years,
            "avg_hours": avg_hrs,
            "difficulty_level": diff,
            "typical_effort_hours": typical_effort_hours,
        }

    _CACHED_CATALOG = catalog
    return _CACHED_CATALOG


def calculate_duration(typical_hours: int, available_hours: float) -> str:
    """
    Calculate estimated project duration range based on typical total project effort
    and student's weekly availability.
    """
    hrs = max(1.0, float(available_hours))
    est_weeks = max(1, round(typical_hours / hrs))
    if est_weeks <= 2:
        week_range = "1-2 weeks"
    elif est_weeks <= 4:
        week_range = f"{max(2, est_weeks - 1)}-{est_weeks + 1} weeks"
    elif est_weeks <= 8:
        week_range = f"{est_weeks - 1}-{est_weeks + 2} weeks"
    else:
        week_range = f"{est_weeks - 2}-{est_weeks + 2} weeks"
    return f"{week_range} (approx. {typical_hours} hours total at {int(hrs)} hrs/week)"


def calculate_profile_similarity(student: dict, project_meta: dict) -> float:
    """
    Compute a multi-factor content-based relevance score between student profile
    and project characteristics for fallback ranking.
    """
    student_skills = tokenize(student.get("Current_Skills", ""))
    project_skills = tokenize(project_meta["required_skills"] + " " + project_meta["recommended_tools"])

    # 1. Skill overlap score (Jaccard similarity with core tech preservation)
    if student_skills and project_skills:
        skill_inter = student_skills.intersection(project_skills)
        skill_score = len(skill_inter) / max(len(student_skills.union(project_skills)), 1)
        if any(tech in student_skills and tech in project_skills for tech in ["python", "c", "javascript", "sql", "excel", "cad"]):
            skill_score = max(skill_score, 0.45)
    else:
        skill_score = 0.2

    # 2. Interest alignment
    student_interest = tokenize(student.get("Interest", ""))
    proj_interest = tokenize(" ".join(project_meta["interests"]) + " " + project_meta["project_name"])
    if student_interest.intersection(proj_interest):
        interest_score = 0.95
    else:
        interest_score = 0.15

    # 3. Department alignment
    dept = student.get("Department", "")
    dept_score = 0.90 if dept in project_meta["departments"] else 0.25

    # 4. Hours compatibility
    target_hours = project_meta["avg_hours"]
    hours_diff = abs(float(student.get("Available_Hours_Per_Week", 10)) - target_hours)
    hours_score = max(0.2, 1.0 - (hours_diff / 30.0))

    composite = (0.35 * skill_score) + (0.35 * interest_score) + (0.18 * dept_score) + (0.12 * hours_score)
    return round(float(composite), 4)


def generate_match_reason(student: dict, meta: dict, is_ml: bool, score: float) -> str:
    """
    Synthesize an honest, personalized explanation of why this project matches
    the student's profile.
    """
    dept = student.get("Department", "your department")
    interest = student.get("Interest", "your field of interest")
    skills = student.get("Current_Skills", "")
    hrs = student.get("Available_Hours_Per_Week", 10)
    base = meta["base_reason"]

    s_tokens = tokenize(skills)
    p_tokens = tokenize(meta["required_skills"] + " " + meta["recommended_tools"])
    common = s_tokens.intersection(p_tokens)
    common_str = ", ".join(sorted(common)) if common else "foundational technical competencies"

    if is_ml:
        reason = (
            f"High alignment with your interest in {interest} and background in {dept}. "
            f"Directly leverages your skills in {common_str}. "
            f"Core objective: {base}. "
            f"Designed to fit your schedule of {int(hrs)} hrs/week."
        )
    else:
        reason = (
            f"Curriculum match for {dept} students exploring {interest}. "
            f"Applies your background in {common_str} to build hands-on experience. "
            f"Core objective: {base}. "
            f"Paced for your {int(hrs)} hrs/week availability."
        )
    return reason


def recommend_project(
    year: str,
    department: str,
    current_skills: str,
    interest: str,
    available_hours: float,
    pipeline=None,
    top_k: int = 5,
    return_dict: bool = True,
):
    """
    Return the top_k personalized project recommendations for a student profile.

    Parameters:
    -----------
    year : str
        Academic year (e.g., '1st Year', '2nd Year', '3rd Year', '4th Year').
    department : str
        Student department (e.g., 'CSE', 'IT', 'ECE', 'DATA SCIENCE', 'Civil').
    current_skills : str
        Comma-separated student skills.
    interest : str
        Primary field of interest (e.g., 'Artificial Intelligence', 'Data Science').
    available_hours : float or int
        Weekly project hours (1 - 40).
    pipeline : sklearn.pipeline.Pipeline, optional
        Pre-loaded model pipeline.
    top_k : int, default 5
        Number of unique recommendations to return.
    return_dict : bool, default True
        If True, returns list of recommendation dictionaries.
        If False and top_k == 1, returns single project name string.

    Returns:
    --------
    list of dict
        Up to top_k unique recommendations with complete project profiles.
    """
    if pipeline is None:
        pipeline = load_model()

    catalog = get_project_catalog()

    student_data = {
        "Year": str(year),
        "Department": str(department),
        "Current_Skills": str(current_skills),
        "Interest": str(interest),
        "Available_Hours_Per_Week": float(available_hours),
    }

    student_df = pd.DataFrame([student_data], columns=FEATURE_COLUMNS)

    # ── 1. Calculate Valid ML Model Probabilities ─────────────────────────────
    # Random Forest ensemble calculates class probability as fraction of voting trees
    if hasattr(pipeline, "predict_proba"):
        probabilities = pipeline.predict_proba(student_df)[0]
        classes = pipeline.classes_
    else:
        # Fallback if classifier does not provide probabilities
        pred = pipeline.predict(student_df)[0]
        probabilities = [1.0 if c == pred else 0.0 for c in pipeline.classes_]
        classes = pipeline.classes_

    # Sort all classes by ML probability in descending order
    sorted_indices = np.argsort(probabilities)[::-1]
    ml_candidates = []
    for idx in sorted_indices:
        prob = float(probabilities[idx])
        if prob > 0:
            ml_candidates.append((classes[idx], prob))

    recommendations = []
    seen_projects = set()

    # ── 2. Add Top ML Recommendations ─────────────────────────────────────────
    for proj_name, prob in ml_candidates:
        if len(recommendations) >= top_k:
            break
        if proj_name not in seen_projects and proj_name in catalog:
            meta = catalog[proj_name]
            recommendations.append({
                "rank": len(recommendations) + 1,
                "project_name": proj_name,
                "relevance_score": prob,
                "relevance_score_str": f"{prob * 100:.2f}% (ML Probability)",
                "required_skills": meta["required_skills"],
                "difficulty_level": meta["difficulty_level"],
                "estimated_duration": calculate_duration(meta["typical_effort_hours"], available_hours),
                "why_matched": generate_match_reason(student_data, meta, is_ml=True, score=prob),
                "recommended_tools": meta["recommended_tools"],
                "scoring_method": "Random Forest Ensemble Classifier (Tree Vote Ratio)",
            })
            seen_projects.add(proj_name)

    # ── 3. Handle Fallback Ranking if fewer than top_k projects found ──────────
    ml_count = len(recommendations)
    fallback_used = False
    fallback_message = None

    if ml_count < top_k:
        fallback_used = True
        remaining_needed = top_k - ml_count

        # Compute profile similarity scores for all unselected catalog projects
        fallback_candidates = []
        for p_name, p_meta in catalog.items():
            if p_name not in seen_projects:
                sim = calculate_profile_similarity(student_data, p_meta)
                fallback_candidates.append((p_name, sim))

        # Sort by similarity descending
        fallback_candidates.sort(key=lambda x: x[1], reverse=True)

        for p_name, sim in fallback_candidates[:remaining_needed]:
            p_meta = catalog[p_name]
            recommendations.append({
                "rank": len(recommendations) + 1,
                "project_name": p_name,
                "relevance_score": sim,
                "relevance_score_str": f"{sim * 100:.1f}% (Profile Similarity Fallback)",
                "required_skills": p_meta["required_skills"],
                "difficulty_level": p_meta["difficulty_level"],
                "estimated_duration": calculate_duration(p_meta["typical_effort_hours"], available_hours),
                "why_matched": generate_match_reason(student_data, p_meta, is_ml=False, score=sim),
                "recommended_tools": p_meta["recommended_tools"],
                "scoring_method": "Content-Based Profile Similarity (Fallback)",
            })
            seen_projects.add(p_name)

        if ml_count == 1:
            fallback_message = (
                "[Notice] The ML model assigned non-zero probability to only 1 project for this profile combination. "
                "The remaining 4 projects were ranked using Content-Based Profile Similarity (matching skills, "
                "interests, and department curriculum). To enhance purely ML-driven diversity, consider expanding "
                "the dataset with more multi-class student profiles."
            )
        elif ml_count == 0:
            fallback_message = (
                "[Notice] No non-zero probabilities were produced by the ML model for this combination. "
                "All 5 projects were ranked via Content-Based Profile Similarity fallback. "
                "Consider expanding the training dataset with representative samples."
            )
        else:
            fallback_message = (
                f"[Notice] The ML model provided {ml_count} projects with non-zero probability. "
                f"The remaining {top_k - ml_count} project(s) were ranked using Content-Based Profile Similarity."
            )

    # Attach diagnostic metadata to the returned list
    for rec in recommendations:
        if fallback_message:
            rec["note"] = fallback_message

    if top_k == 1 and not return_dict:
        return recommendations[0]["project_name"] if recommendations else "General Capstone Project"

    return recommendations


# Alias for clarity
recommend_top_projects = recommend_project


def format_recommendations(recommendations: list, student_profile: dict = None) -> str:
    """Format the list of recommendations into a clean, human-readable report."""
    if not recommendations:
        return "No recommendations generated."

    lines = []
    lines.append("=" * 80)
    lines.append("       TOP PERSONALIZED PROJECT RECOMMENDATIONS FOR STUDENT")
    lines.append("=" * 80)

    if student_profile:
        lines.append(f"Student: {student_profile.get('Year', 'N/A')} | {student_profile.get('Department', 'N/A')}")
        lines.append(f"Skills : {student_profile.get('Current_Skills', 'N/A')}")
        lines.append(f"Interest: {student_profile.get('Interest', 'N/A')} ({student_profile.get('Available_Hours_Per_Week', 'N/A')} hrs/week)")
        lines.append("-" * 80)

    if "note" in recommendations[0]:
        lines.append(f"NOTE: {recommendations[0]['note']}")
        lines.append("-" * 80)

    for rec in recommendations:
        lines.append(f"\n[#{rec['rank']}] PROJECT: {rec['project_name']}")
        lines.append(f"   - Relevance Score   : {rec['relevance_score_str']}")
        lines.append(f"   - Difficulty Level  : {rec['difficulty_level']}")
        lines.append(f"   - Estimated Duration: {rec['estimated_duration']}")
        lines.append(f"   - Required Skills   : {rec['required_skills']}")
        lines.append(f"   - Recommended Tools : {rec['recommended_tools']}")
        lines.append(f"   - Why It Matches    : {rec['why_matched']}")
        lines.append(f"   - Ranking Method    : {rec['scoring_method']}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def demo_predictions(pipeline=None):
    """Run a demonstration showing top 5 recommendations for varied student profiles."""
    examples = [
        {
            "year": "2nd Year",
            "department": "DATA SCIENCE",
            "current_skills": "Python,Deep learning SQL",
            "interest": "Artificial Intelligence",
            "available_hours": 18,
        },
        {
            "year": "1st Year",
            "department": "CSE",
            "current_skills": "HTML, CSS, JavaScript",
            "interest": "Web Development",
            "available_hours": 8,
        },
        {
            "year": "3rd Year",
            "department": "ECE",
            "current_skills": "C Basics, electronics, Arduino",
            "interest": "Electronics",
            "available_hours": 20,
        },
        {
            "year": "1st Year",
            "department": "Civil",
            "current_skills": "Civil Engineering Basics, Excel",
            "interest": "Sustainable Construction",
            "available_hours": 5,
        },
    ]

    print("\n" + "=" * 80)
    print("                  MULTI-PROJECT RECOMMENDATION DEMO")
    print("=" * 80)

    for i, ex in enumerate(examples, 1):
        recs = recommend_project(pipeline=pipeline, top_k=5, **ex)
        print(f"\n--- Example {i}: {ex['year']} {ex['department']} ({ex['interest']}) ---")
        print(format_recommendations(recs, ex))


def main():
    print("=" * 80)
    print("  STEP 7: MULTI-PROJECT RECOMMENDATION ENGINE")
    print("=" * 80)
    print("\n[INFO] Loading model and dataset catalog...")
    pipeline = load_model()
    print(f"[OK] Model loaded from:\n   {MODEL_PATH}")
    demo_predictions(pipeline)
    print("\n[OK] Recommendations complete.\n")


if __name__ == "__main__":
    main()
