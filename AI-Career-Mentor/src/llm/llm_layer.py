import os
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# We use the new google-genai SDK per guidelines.
# Initialize the client. API key should be in environment variables (GEMINI_API_KEY).

client = genai.Client()

class ToolSuggestion(BaseModel):
    name: str = Field(description="Name of the tool")
    purpose: str = Field(description="Purpose of the tool for this project")
    cost: str = Field(description="Is it free or paid?")

class RoadmapTask(BaseModel):
    week: int
    task: str
    hours_required: float
    milestone: str

class CareerRole(BaseModel):
    role: str
    required_skills: list[str]
    outlook_5_years: str

class LLMResponse(BaseModel):
    reason: str = Field(description="Personalized reason why this project suits the student.")
    week_by_week_roadmap: list[RoadmapTask]
    tools: list[ToolSuggestion]
    career_roles: list[CareerRole]

def generate_personalized_plan(user_profile: dict, ml_results: dict) -> dict:
    """
    Calls the Gemini API with structured output to get a personalized roadmap and career insights.
    Uses Structured Output (Pydantic) to ensure strictly valid JSON.
    """
    prompt = f"""
    You are an AI Career and Project Mentor. 
    A student has the following profile:
    Year: {user_profile.get('year')}
    Department: {user_profile.get('department')}
    Current Skills: {', '.join(user_profile.get('current_skills', []))}
    Interests: {', '.join(user_profile.get('interests', []))}
    Weekly Hours: {user_profile.get('weekly_hours')}
    
    The ML engine recommended the following project:
    Title: {ml_results['recommended_project']['title']}
    Domain: {ml_results['recommended_project']['domain']}
    Estimated Duration: {ml_results['duration']}
    Missing Skills: {', '.join(ml_results['recommended_skills'])}
    
    Please provide a personalized reason for this project, a detailed week-by-week roadmap, 
    tool suggestions (must be free/low-cost), and a futuristic career view based on this.
    """
    
    # Using Structured Outputs feature
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LLMResponse,
            ),
        )
        # Parse the JSON response
        return json.loads(response.text)
    except Exception as e:
        # Fallback/Retry logic could be added here
        print(f"LLM Generation failed: {e}")
        return {
            "reason": "Fallback reason due to API error.",
            "week_by_week_roadmap": [],
            "tools": [],
            "career_roles": []
        }
