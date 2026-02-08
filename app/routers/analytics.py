from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict
from ..database import get_db
from ..models import Task, TaskCompletion, ProductivityLog

router = APIRouter()

@router.get("/productivity/{user_id}")
def get_productivity_analytics(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get productivity analytics for a user"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Task completion trends
    daily_completions = db.query(
        func.date(Task.completed_at).label("date"),
        func.count(Task.id).label("completed")
    ).filter(
        Task.user_id == user_id,
        Task.completed == True,
        Task.completed_at >= start_date
    ).group_by(func.date(Task.completed_at)).all()
    
    # Average completion time
    avg_completion = db.query(
        func.avg(TaskCompletion.actual_hours)
    ).filter(
        TaskCompletion.user_id == user_id
    ).scalar() or 0
    
    # Task distribution by priority
    priority_dist = db.query(
        Task.priority,
        func.count(Task.id).label("count")
    ).filter(
        Task.user_id == user_id
    ).group_by(Task.priority).all()
    
    return {
        "period_days": days,
        "daily_completions": [{"date": str(d.date), "completed": d.completed} for d in daily_completions],
        "average_completion_hours": round(avg_completion, 2),
        "priority_distribution": [{"priority": p.priority, "count": p.count} for p in priority_dist]
    }

@router.get("/predictions/{user_id}")
def get_ai_predictions(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get AI predictions for user performance"""
    # Get recent task patterns
    recent_tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.completed == True
    ).order_by(Task.completed_at.desc()).limit(20).all()
    
    if len(recent_tasks) < 5:
        return {"message": "Insufficient data for predictions", "status": "collecting_data"}
    
    # Calculate patterns
    completion_times = []
    for task in recent_tasks:
        completion = db.query(TaskCompletion).filter(
            TaskCompletion.task_id == task.id
        ).first()
        if completion:
            completion_times.append(completion.actual_hours)
    
    if not completion_times:
        return {"message": "No completion data available", "status": "no_data"}
    
    avg_completion_time = sum(completion_times) / len(completion_times)
    
    # Predict next week capacity
    next_week_capacity = 40 / avg_completion_time  # Assuming 40-hour work week
    
    return {
        "status": "ready",
        "data_points": len(recent_tasks),
        "average_completion_time": round(avg_completion_time, 2),
        "predicted_weekly_capacity": round(next_week_capacity, 1),
        "recommendations": [
            "Consider breaking large tasks into smaller subtasks",
            "Schedule similar tasks together for efficiency",
            "Take breaks during long work sessions"
        ]
    }