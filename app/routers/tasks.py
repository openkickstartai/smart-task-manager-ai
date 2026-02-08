from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..database import get_db
from ..models import Task, TaskCompletion
from ..ml_models.prioritizer import TaskPrioritizer
from ..ml_models.deadline_predictor import DeadlinePredictor

router = APIRouter()
prioritizer = TaskPrioritizer()
deadline_predictor = DeadlinePredictor()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    estimated_hours: Optional[float] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: int
    estimated_hours: float
    deadline: Optional[datetime]
    completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskWithAI(TaskResponse):
    ai_priority: int
    priority_confidence: float
    predicted_hours: float
    prediction_confidence: float

@router.post("/", response_model=TaskWithAI)
def create_task(
    task: TaskCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create a new task with AI-powered analysis"""
    db_task = Task(
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        estimated_hours=task.estimated_hours,
        user_id=user_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # AI analysis
    priority, priority_confidence = prioritizer.predict_priority(db_task, user_id)
    predicted_hours, prediction_confidence = deadline_predictor.predict_deadline(db_task, user_id)
    
    # Update with AI insights
    db_task.priority = priority
    db.commit()
    
    return TaskWithAI(
        **db_task.__dict__,
        ai_priority=priority,
        priority_confidence=priority_confidence,
        predicted_hours=predicted_hours,
        prediction_confidence=prediction_confidence
    )

@router.get("/", response_model=List[TaskWithAI])
def get_tasks(
    user_id: int,
    completed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get tasks with AI analysis"""
    query = db.query(Task).filter(Task.user_id == user_id)
    
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    tasks = query.all()
    
    tasks_with_ai = []
    for task in tasks:
        priority, priority_confidence = prioritizer.predict_priority(task, user_id)
        predicted_hours, prediction_confidence = deadline_predictor.predict_deadline(task, user_id)
        
        tasks_with_ai.append(TaskWithAI(
            **task.__dict__,
            ai_priority=priority,
            priority_confidence=priority_confidence,
            predicted_hours=predicted_hours,
            prediction_confidence=prediction_confidence
        ))
    
    # Sort by AI priority
    tasks_with_ai.sort(key=lambda x: x.ai_priority, reverse=True)
    return tasks_with_ai

@router.put("/{task_id}/complete")
def complete_task(
    task_id: int,
    user_id: int,
    actual_hours: float,
    db: Session = Depends(get_db)
):
    """Mark a task as complete and log actual hours"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.completed = True
    task.completed_at = datetime.utcnow()
    
    # Log completion for ML training
    completion = TaskCompletion(
        task_id=task_id,
        actual_hours=actual_hours,
        user_id=user_id
    )
    
    db.add(completion)
    db.commit()
    
    return {"message": "Task completed successfully"}

@router.get("/insights/{user_id}")
def get_task_insights(user_id: int, db: Session = Depends(get_db)):
    """Get AI-powered insights about user tasks"""
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    completed_tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.completed == True
    ).all()
    
    total_tasks = len(tasks)
    completed_count = len(completed_tasks)
    completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get overdue tasks
    now = datetime.utcnow()
    overdue = db.query(Task).filter(
        Task.user_id == user_id,
        Task.deadline < now,
        Task.completed == False
    ).count()
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_count,
        "completion_rate": round(completion_rate, 2),
        "overdue_tasks": overdue,
        "avg_priority": round(sum(t.priority for t in tasks) / len(tasks), 2) if tasks else 0
    }