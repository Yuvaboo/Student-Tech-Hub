import os
import sys

# Ensure src directory is in Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predict import recommend_project, format_recommendations

student_profile = {
    "year": "2nd Year",
    "department": "DATA SCIENCE",
    "current_skills": "Python,Deep learning SQL",
    "interest": "Artificial Intelligence",
    "available_hours": 18,
}

# Generate TOP 5 personalized recommendations
recommendations = recommend_project(
    year=student_profile["year"],
    department=student_profile["department"],
    current_skills=student_profile["current_skills"],
    interest=student_profile["interest"],
    available_hours=student_profile["available_hours"],
    top_k=5,
)

# Display formatted recommendations
print(format_recommendations(recommendations, {
    "Year": student_profile["year"],
    "Department": student_profile["department"],
    "Current_Skills": student_profile["current_skills"],
    "Interest": student_profile["interest"],
    "Available_Hours_Per_Week": student_profile["available_hours"],
}))

print(f"\n[Summary] Total Recommendations Returned: {len(recommendations)} unique projects.")
for r in recommendations:
    print(f"  #{r['rank']}: {r['project_name']} | Level: {r['difficulty_level']} | Score: {r['relevance_score_str']}")
