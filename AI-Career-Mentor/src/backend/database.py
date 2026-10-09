from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./career_mentor.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    year = Column(Integer)
    department = Column(String)
    current_skills = Column(Text) # CSV
    interests = Column(Text) # CSV
    weekly_hours = Column(Float)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recommended_skills = Column(Text)
    project_title = Column(String)
    project_domain = Column(String)
    difficulty = Column(Float)
    duration = Column(String)
    reason = Column(Text)
    tools = Column(Text) # JSON string
    career_roles = Column(Text) # JSON string

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    week = Column(Integer)
    task_desc = Column(String)
    is_completed = Column(Boolean, default=False)
    
class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    scheduled_time = Column(String) # For simplicity, a string timestamp
    sent = Column(Boolean, default=False)

def init_db():
    Base.metadata.create_all(bind=engine)
