"""
Test Suite: Verify Multi-Project Recommendation Engine
========================================================
Verifies:
1. Top-5 recommendations count.
2. No duplicate projects returned (strictly unique).
3. Presence of all required fields:
   - Project name
   - Required skills
   - Difficulty level
   - Estimated duration
   - Why the project matches the student
   - Recommended tools
   - Relevance score
4. Valid mathematical scoring (probabilities / similarity in [0, 1]).
5. Behavior across diverse student profiles.
"""

import os
import sys
import unittest

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predict import recommend_project, get_project_catalog, load_model


class TestMultiProjectRecommendations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Pre-load model and catalog once for testing."""
        cls.pipeline = load_model()
        cls.catalog = get_project_catalog()

    def test_top_five_count(self):
        """Verify that exactly 5 recommendations are returned when top_k=5."""
        recs = recommend_project(
            year="2nd Year",
            department="DATA SCIENCE",
            current_skills="Python,Deep learning SQL",
            interest="Artificial Intelligence",
            available_hours=18,
            top_k=5,
            pipeline=self.pipeline,
        )
        self.assertEqual(len(recs), 5, f"Expected 5 recommendations, got {len(recs)}")

    def test_no_duplicate_projects(self):
        """Verify that all returned recommendations are unique with zero duplicates."""
        recs = recommend_project(
            year="2nd Year",
            department="DATA SCIENCE",
            current_skills="Python,Deep learning SQL",
            interest="Artificial Intelligence",
            available_hours=18,
            top_k=5,
            pipeline=self.pipeline,
        )
        project_names = [r["project_name"] for r in recs]
        unique_names = set(project_names)
        self.assertEqual(
            len(project_names), len(unique_names),
            f"Duplicate projects found in recommendations: {project_names}"
        )

    def test_all_required_fields_present(self):
        """Verify each recommendation contains all required specifications."""
        recs = recommend_project(
            year="3rd Year",
            department="CSE",
            current_skills="Python Basics, pandas, Machine Learning",
            interest="Data Science",
            available_hours=15,
            top_k=5,
            pipeline=self.pipeline,
        )

        required_keys = [
            "project_name",
            "required_skills",
            "difficulty_level",
            "estimated_duration",
            "why_matched",
            "recommended_tools",
            "relevance_score",
            "relevance_score_str",
            "scoring_method",
        ]

        for idx, rec in enumerate(recs, 1):
            for key in required_keys:
                self.assertIn(
                    key, rec,
                    f"Recommendation #{idx} is missing required field '{key}'"
                )
                self.assertTrue(
                    str(rec[key]).strip(),
                    f"Recommendation #{idx} has empty field '{key}'"
                )

    def test_difficulty_levels_valid(self):
        """Verify difficulty levels are categorized into recognized academic tiers."""
        recs = recommend_project(
            year="1st Year",
            department="IT",
            current_skills="HTML, CSS",
            interest="Web Development",
            available_hours=8,
            top_k=5,
            pipeline=self.pipeline,
        )
        valid_levels = {"Beginner", "Intermediate", "Advanced"}
        for r in recs:
            self.assertIn(
                r["difficulty_level"], valid_levels,
                f"Unexpected difficulty level '{r['difficulty_level']}' for project '{r['project_name']}'"
            )

    def test_relevance_scores_valid(self):
        """Verify relevance scores are mathematically valid numeric scores in [0, 1]."""
        recs = recommend_project(
            year="2nd Year",
            department="ECE",
            current_skills="C Basics, electronics, Arduino",
            interest="Electronics",
            available_hours=12,
            top_k=5,
            pipeline=self.pipeline,
        )
        for r in recs:
            score = r["relevance_score"]
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_multiple_diverse_student_profiles(self):
        """Verify recommendations work robustly across different student branches and years."""
        test_profiles = [
            ("1st Year", "Civil", "Civil Engineering Basics, Excel", "Sustainable Construction", 6),
            ("2nd Year", "Mechanical", "AutoCAD, Physics", "Robotics", 15),
            ("3rd Year", "EEE", "C Basics, Embedded Systems, Circuit Theory", "Embedded Systems", 10),
            ("4th Year", "CSE", "Python, PyTorch, Cloud Computing", "Artificial Intelligence", 25),
        ]

        for year, dept, skills, interest, hours in test_profiles:
            recs = recommend_project(
                year=year,
                department=dept,
                current_skills=skills,
                interest=interest,
                available_hours=hours,
                top_k=5,
                pipeline=self.pipeline,
            )
            self.assertEqual(len(recs), 5, f"Profile {dept}-{year} failed to return 5 recommendations")
            names = [r["project_name"] for r in recs]
            self.assertEqual(len(names), len(set(names)), f"Duplicates in profile {dept}-{year}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
