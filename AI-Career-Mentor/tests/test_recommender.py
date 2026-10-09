import pytest
from src.ml.recommender import recommend

# We use 5 sample student profiles for testing.
profiles = [
    {
        "year": 1,
        "department": "CSE",
        "current_skills": [],
        "interests": ["Web Development"],
        "weekly_hours": 5
    },
    {
        "year": 3,
        "department": "ECE",
        "current_skills": ["C++", "Arduino"],
        "interests": ["IoT", "Robotics"],
        "weekly_hours": 15
    },
    {
        "year": 4,
        "department": "Mech",
        "current_skills": ["AutoCAD"],
        "interests": ["Civil", "Robotics"],
        "weekly_hours": 20
    },
    {
        "year": 2,
        "department": "IT",
        "current_skills": ["Python"],
        "interests": ["AI/ML", "Data Science"],
        "weekly_hours": 10
    },
    {
        "year": 3,
        "department": "EEE",
        "current_skills": ["Arduino", "Python"],
        "interests": ["Power Systems", "IoT"],
        "weekly_hours": 2
    }
]

def test_recommend_basic():
    for profile in profiles:
        res = recommend(profile)
        assert "recommended_skills" in res
        assert "recommended_project" in res
        assert "difficulty_percentage" in res
        assert "duration" in res
        assert res["difficulty_percentage"] >= 0 and res["difficulty_percentage"] <= 100
