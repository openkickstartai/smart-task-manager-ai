import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from ..database import SessionLocal
from ..models import Task, TaskCompletion

class DeadlinePredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def extract_features(self, task: Task, user_history: List[Dict]) -> np.ndarray:
        """Extract features for deadline prediction"""
        now = datetime.utcnow()
        
        # Task features
        task_length = len(task.description) if task.description else 0
        title_length = len(task.title)
        estimated_hours = task.estimated_hours or 1.0
        
        # User performance features
        avg_completion_time = np.mean([h.get("actual_hours", 1.0) for h in user_history]) if user_history else 1.0
        completion_variance = np.var([h.get("actual_hours", 1.0) for h in user_history]) if user_history and len(user_history) > 1 else 0.5
        
        return np.array([
            task_length,
            title_length,
            estimated_hours,
            avg_completion_time,
            completion_variance
        ])
    
    def train(self, training_data: List[Dict]):
        """Train the deadline prediction model"""
        if len(training_data) < 10:
            return False
            
        df = pd.DataFrame(training_data)
        
        features = [
            "task_length", "title_length", "estimated_hours",
            "avg_completion_time", "completion_variance"
        ]
        
        X = df[features].values
        y = df["actual_hours_taken"].values
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        return True
    
    def predict_deadline(self, task: Task, user_id: int) -> Tuple[float, float]:
        """Predict hours needed and confidence score"""
        if not self.is_trained:
            return self._calculate_estimated_hours(task), 0.6
            
        db = SessionLocal()
        try:
            # Get user completion history
            completions = db.query(TaskCompletion).filter(TaskCompletion.user_id == user_id).all()
            user_history = [
                {
                    "actual_hours": c.actual_hours,
                    "completion_date": c.completion_date
                } for c in completions
            ]
        finally:
            db.close()
        
        features = self.extract_features(task, user_history)
        features_scaled = self.scaler.transform([features])
        
        predicted_hours = float(self.model.predict(features_scaled)[0])
        
        # Calculate confidence based on model prediction variance
        confidence = 0.8 if self.is_trained else 0.6
        
        return predicted_hours, confidence
    
    def _calculate_estimated_hours(self, task: Task) -> float:
        """Fallback estimated hours calculation"""
        if task.estimated_hours:
            return task.estimated_hours
            
        base_hours = 1.0
        
        # Add complexity based on description length
        if task.description:
            word_count = len(task.description.split())
            base_hours += max(0, word_count / 50)
        
        # Add complexity based on title
        if task.title:
            title_words = len(task.title.split())
            base_hours += max(0, title_words / 10)
        
        return min(40, base_hours)  # Cap at 40 hours