from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    email: str
    year: int
    department: str
    current_skills: List[str]
    interests: List[str]
    weekly_hours: float

class ChatMessage(BaseModel):
    user_id: int
    message: str
    
class TaskComplete(BaseModel):
    task_id: int
