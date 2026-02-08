import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from ..database import SessionLocal
from ..models import Task, TaskCompletion, ProductivityLog

class TaskPrioritizer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def extract_features(self, task: Task, user_history: List[Dict]) -> np.ndarray:
        """Extract features from task and user history"""
        now = datetime.utcnow()
        
        # Task features
        days_to_deadline = (task.deadline - now).days if task.deadline else 30
        task_age = (now - task.created_at).days
        estimated_hours = task.estimated_hours or 1.0
        
        # User performance features
        avg_completion_time = np.mean([h.get("actual_hours", 1.0) for h in user_history]) if user_history else 1.0
        productivity_score = np.mean([h.get("productivity_score", 0.5) for h in user_history]) if user_history else 0.5
        tasks_per_day = np.mean([h.get("tasks_completed", 1) for h in user_history]) if user_history else 1.0
        
        return np.array([
            days_to_deadline,
            task_age,
            estimated_hours,
            avg_completion_time,
            productivity_score,
            tasks_per_day
        ])
    
    def train(self, training_data: List[Dict]):
        """Train the prioritization model"""
        if len(training_data) < 10:
            return False
            
        df = pd.DataFrame(training_data)
        
        features = [
            "days_to_deadline", "task_age", "estimated_hours",
            "avg_completion_time", "productivity_score", "tasks_per_day"
        ]
        
        X = df[features].values
        y = df["was_completed_on_time"].values
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        return True
    
    def predict_priority(self, task: Task, user_id: int) -> Tuple[int, float]:
        """Predict task priority and confidence score"""
        if not self.is_trained:
            return self._calculate_priority_rules(task)
            
        db = SessionLocal()
        try:
            # Get user history
            completions = db.query(TaskCompletion).filter(TaskCompletion.user_id == user_id).all()
            user_history = [
                {
                    "actual_hours": c.actual_hours,
                    "completion_date": c.completion_date
                } for c in completions
            ]
            
            productivity_logs = db.query(ProductivityLog).filter(ProductivityLog.user_id == user_id).all()
            user_history.extend([
                {
                    "productivity_score": p.productivity_score,
                    "tasks_completed": p.tasks_completed
                } for p in productivity_logs
            ])
            
        finally:
            db.close()
        
        features = self.extract_features(task, user_history)
        features_scaled = self.scaler.transform([features])
        
        # Predict probability of timely completion
        priority_score = self.model.predict_proba(features_scaled)[0][1]
        
        # Convert to 1-10 priority scale (inverse of completion probability)
        priority = int(10 * (1 - priority_score)) + 1
        confidence = float(np.max(self.model.predict_proba(features_scaled)))
        
        return priority, confidence
    
    def _calculate_priority_rules(self, task: Task) -> Tuple[int, float]:
        """Fallback rule-based priority calculation"""
        now = datetime.utcnow()
        base_priority = 5
        confidence = 0.7
        
        if task.deadline:
            days_to_deadline = (task.deadline - now).days
            if days_to_deadline <= 1:
                base_priority = 10
            elif days_to_deadline <= 3:
                base_priority = 8
            elif days_to_deadline <= 7:
                base_priority = 6
        
        if task.estimated_hours and task.estimated_hours > 8:
            base_priority = min(10, base_priority + 2)
        
        return base_priority, confidence