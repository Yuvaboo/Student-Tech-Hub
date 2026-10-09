import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Initialize SentenceTransformer for embedding skills and domains
# MiniLM is fast, free, and runs locally.
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    projects_path = os.path.join(base_dir, 'data', 'projects.csv')
    skills_path = os.path.join(base_dir, 'data', 'skills.csv')
    
    df_projects = pd.read_csv(projects_path)
    df_skills = pd.read_csv(skills_path)
    return df_projects, df_skills

def recommend(user_profile: dict) -> dict:
    """
    Takes a user profile and returns recommended skills, projects, difficulty, and duration.
    """
    df_projects, df_skills = load_data()
    
    # 1. Recommend Skills (Skill Gap)
    user_skills_set = set([s.strip().lower() for s in user_profile['current_skills']])
    # For simplicity, extract all skills from projects related to user's interests
    all_req_skills = []
    for idx, row in df_projects.iterrows():
        if any(interest.lower() in row['domain'].lower() for interest in user_profile['interests']):
            all_req_skills.extend([s.strip().lower() for s in row['required_skills'].split(',')])
    
    all_req_skills = list(set(all_req_skills))
    skill_gap = [skill for skill in all_req_skills if skill not in user_skills_set]
    recommended_skills = skill_gap[:5] # Top 5 missing skills
    
    # 2. Recommend Projects
    # We match user skills + interests to the project's domain + required skills
    user_text = " ".join(user_profile['current_skills']) + " " + " ".join(user_profile['interests'])
    project_texts = (df_projects['domain'] + " " + df_projects['required_skills'] + " " + df_projects['description']).tolist()
    
    # Compute embeddings
    user_emb = model.encode([user_text])
    proj_embs = model.encode(project_texts)
    
    # Cosine similarity
    sim_scores = cosine_similarity(user_emb, proj_embs)[0]
    
    # Add heuristic filtering: year and department
    # For a real system, we parse the numbers and match. Here, we do a substring match.
    valid_indices = []
    for i, row in df_projects.iterrows():
        # Check year
        if str(user_profile['year']) in str(row['suitable_year']):
            # Check department
            if user_profile['department'] in row['suitable_departments']:
                valid_indices.append(i)
                
    if not valid_indices:
        # Fallback if no strict match
        valid_indices = list(range(len(df_projects)))
        
    # Rank by similarity among valid projects
    ranked_indices = sorted(valid_indices, key=lambda i: sim_scores[i], reverse=True)
    top_project_idx = ranked_indices[0] if ranked_indices else 0
    top_project = df_projects.iloc[top_project_idx]
    
    # Calculate required skills for this specific project
    proj_req_skills = [s.strip().lower() for s in top_project['required_skills'].split(',')]
    missing_for_proj = [s for s in proj_req_skills if s not in user_skills_set]
    
    # 3. Difficulty Level (%)
    # Heuristic formula: base difficulty + penalty for missing skills - bonus for high weekly hours
    # In a real system, this would be a trained Regression model (e.g. XGBoost).
    # Here, we use a heuristic for the prototype to avoid complex synthetic training loops.
    base_diff = (top_project['difficulty_1_to_10'] / 10.0) * 100
    missing_penalty = len(missing_for_proj) * 10
    hours_bonus = (user_profile['weekly_hours'] / 20.0) * 5
    calculated_difficulty = min(100, max(10, base_diff + missing_penalty - hours_bonus))
    
    # 4. Total Duration
    # Base estimated hours + (10 hours per missing skill to learn)
    total_hours_needed = top_project['estimated_hours'] + (len(missing_for_proj) * 10)
    weeks_needed = total_hours_needed / user_profile['weekly_hours'] if user_profile['weekly_hours'] > 0 else 999
    days_needed = weeks_needed * 7
    
    duration = f"{int(weeks_needed)} weeks and {int(days_needed % 7)} days"
    
    return {
        "recommended_skills": missing_for_proj if missing_for_proj else ["Advanced topics"],
        "recommended_project": {
            "title": top_project['title'],
            "description": top_project['description'],
            "domain": top_project['domain'],
            "tools": top_project['tools']
        },
        "difficulty_percentage": round(calculated_difficulty, 2),
        "duration": duration,
        "missing_skills_count": len(missing_for_proj)
    }

if __name__ == "__main__":
    # Test with a sample profile
    sample_user = {
        "year": 3,
        "department": "CSE",
        "current_skills": ["Python", "HTML"],
        "interests": ["AI/ML", "Web Development"],
        "weekly_hours": 10
    }
    res = recommend(sample_user)
    print("Test Recommendation:")
    print(res)
