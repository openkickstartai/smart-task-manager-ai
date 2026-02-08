from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import get_db, engine, Base
from .routers import tasks, users, analytics
from .ml_models import TaskPrioritizer, DeadlinePredictor

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Task Manager AI",
    description="An intelligent task management system with ML-powered prioritization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
def root():
    return {"message": "Smart Task Manager AI API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "ai_status": "active"}