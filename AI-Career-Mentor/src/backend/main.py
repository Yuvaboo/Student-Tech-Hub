from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import json
import datetime
from dotenv import load_dotenv

# Load ENV before starting
load_dotenv()

from src.backend.database import SessionLocal, init_db, User, Recommendation, Task
from src.backend.models import UserCreate, ChatMessage, TaskComplete
from src.ml.recommender import recommend
from src.llm.llm_layer import generate_personalized_plan
from src.llm.youtube import get_youtube_links
from src.llm.chatbot import update_context, chat_with_mentor
from src.scheduler.reminders import start_scheduler, schedule_reminders_for_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    start_scheduler()
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/recommend")
def create_recommendation(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Save User
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if not db_user:
        db_user = User(
            email=user_in.email,
            year=user_in.year,
            department=user_in.department,
            current_skills=",".join(user_in.current_skills),
            interests=",".join(user_in.interests),
            weekly_hours=user_in.weekly_hours
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
    user_dict = user_in.dict()
    
    # 2. ML Engine
    ml_res = recommend(user_dict)
    
    # 3. LLM Layer
    llm_res = generate_personalized_plan(user_dict, ml_res)
    
    # 4. YouTube Links
    youtube_links = get_youtube_links(ml_res['recommended_skills'])
    
    # 5. Save to DB
    db_rec = Recommendation(
        user_id=db_user.id,
        recommended_skills=",".join(ml_res['recommended_skills']),
        project_title=ml_res['recommended_project']['title'],
        project_domain=ml_res['recommended_project']['domain'],
        difficulty=ml_res['difficulty_percentage'],
        duration=ml_res['duration'],
        reason=llm_res.get('reason', ''),
        tools=json.dumps(llm_res.get('tools', [])),
        career_roles=json.dumps(llm_res.get('career_roles', []))
    )
    db.add(db_rec)
    db.commit()
    
    # 6. Save Tasks & Schedule Reminders
    for task_data in llm_res.get('week_by_week_roadmap', []):
        db_task = Task(
            user_id=db_user.id,
            week=task_data['week'],
            task_desc=task_data['task']
        )
        db.add(db_task)
    db.commit()
    
    # Schedule
    schedule_reminders_for_user(db_user.email, llm_res.get('week_by_week_roadmap', []), datetime.date.today())
    
    # 7. Update AI Twin Context
    update_context(str(db_user.id), user_dict, ml_res['recommended_project'], llm_res.get('week_by_week_roadmap', []))
    
    return {
        "user_id": db_user.id,
        "ml_results": ml_res,
        "llm_results": llm_res,
        "youtube": youtube_links
    }

@app.post("/chat")
def chat(message: ChatMessage, db: Session = Depends(get_db)):
    # Calculate AI Twin Pace
    total_tasks = db.query(Task).filter(Task.user_id == message.user_id).count()
    completed_tasks = db.query(Task).filter(Task.user_id == message.user_id, Task.is_completed == True).count()
    progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    pace = "on track" if progress >= 50 else "falling behind"
    
    twin_state = {"progress": progress, "pace": pace}
    reply = chat_with_mentor(str(message.user_id), message.message, twin_state)
    return {"reply": reply}

@app.post("/task/complete")
def complete_task(req: TaskComplete, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == req.task_id).first()
    if task:
        task.is_completed = True
        db.commit()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/progress/{user_id}")
def get_progress(user_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return [{"id": t.id, "week": t.week, "task_desc": t.task_desc, "is_completed": t.is_completed} for t in tasks]
