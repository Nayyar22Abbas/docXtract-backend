"""
User Data Aggregation Service
Fetches and aggregates user data from MongoDB for predictive analysis
This integrates with existing quiz, user, and recommendation data
"""

from config.db import authconn, quizconn, recommendations_conn
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics


class UserDataAggregator:
    """Aggregates user data from MongoDB for predictive analytics"""
    
    @staticmethod
    def get_user_quiz_history(user_id: str, limit: int = 50) -> List[Dict]:
        """
        Fetch user's quiz history from MongoDB
        
        Args:
            user_id: User ID
            limit: Maximum number of records to fetch
        
        Returns:
            List of quiz records with scores and timestamps
        """
        try:
            quiz_records = list(
                quizconn.find(
                    {"user_id": user_id},
                    sort=[("created_at", -1)],
                    limit=limit
                )
            )
            
            # Convert ObjectId to string
            for record in quiz_records:
                record["_id"] = str(record["_id"])
            
            return quiz_records
        except Exception as e:
            print(f"Error fetching quiz history: {e}")
            return []
    
    @staticmethod
    def analyze_quiz_trends(user_id: str) -> Dict:
        """
        Analyze quiz score trends over time
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with trend analysis
        """
        quiz_history = UserDataAggregator.get_user_quiz_history(user_id, limit=20)
        
        if not quiz_history:
            return {
                "trend": "No data",
                "average_score": 0,
                "recent_scores": [],
                "improvement": None,
                "consistency": "Unknown"
            }
        
        # Extract scores by subject
        subject_scores = {}
        for quiz in quiz_history:
            if "subject" in quiz:
                subject = quiz["subject"]
                if subject not in subject_scores:
                    subject_scores[subject] = []
                if "score" in quiz:
                    subject_scores[subject].append(quiz["score"])
        
        # Calculate metrics
        all_scores = []
        for scores in subject_scores.values():
            all_scores.extend(scores)
        
        if not all_scores:
            return {
                "trend": "No data",
                "average_score": 0,
                "recent_scores": [],
                "improvement": None,
                "consistency": "Unknown"
            }
        
        avg_score = statistics.mean(all_scores)
        
        # Calculate trend (comparing first half vs second half)
        mid_point = len(all_scores) // 2
        first_half = all_scores[:mid_point] if mid_point > 0 else [all_scores[0]]
        second_half = all_scores[mid_point:]
        
        trend_direction = "Improving" if statistics.mean(second_half) > statistics.mean(first_half) else "Declining"
        
        # Calculate consistency (standard deviation)
        if len(all_scores) > 1:
            std_dev = statistics.stdev(all_scores)
            consistency = "Consistent" if std_dev < 15 else "Variable"
        else:
            consistency = "Insufficient data"
        
        return {
            "trend": trend_direction,
            "average_score": round(avg_score, 2),
            "recent_scores": all_scores[-5:],  # Last 5 scores
            "improvement": round(statistics.mean(second_half) - statistics.mean(first_half), 2),
            "consistency": consistency,
            "subject_breakdown": {
                subject: {
                    "count": len(scores),
                    "average": round(statistics.mean(scores), 2),
                    "latest": scores[-1] if scores else 0
                }
                for subject, scores in subject_scores.items()
            }
        }
    
    @staticmethod
    def extract_weak_topics_from_history(user_id: str) -> List[Tuple[str, float]]:
        """
        Extract weak topics by analyzing quiz history
        Returns topics associated with low scores
        
        Args:
            user_id: User ID
        
        Returns:
            List of (topic, weakness_score) tuples sorted by weakness
        """
        quiz_history = UserDataAggregator.get_user_quiz_history(user_id, limit=30)
        
        topic_scores = {}
        for quiz in quiz_history:
            if "topics_covered" in quiz and "score" in quiz:
                topics = quiz["topics_covered"]
                score = quiz["score"]
                
                if isinstance(topics, list):
                    for topic in topics:
                        if topic not in topic_scores:
                            topic_scores[topic] = []
                        topic_scores[topic].append(score)
        
        # Calculate weakness score (lower average score = higher weakness)
        weakness_ranking = []
        for topic, scores in topic_scores.items():
            avg_score = statistics.mean(scores)
            weakness_score = 100 - avg_score  # Invert so low scores = high weakness
            weakness_ranking.append((topic, weakness_score))
        
        # Sort by weakness (highest weakness first)
        return sorted(weakness_ranking, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def get_enrolled_subjects(user_id: str) -> List[str]:
        """
        Extract enrolled subjects from quiz history and recommendations
        
        Args:
            user_id: User ID
        
        Returns:
            List of enrolled subjects
        """
        subjects = set()
        
        # From quiz history
        quiz_history = UserDataAggregator.get_user_quiz_history(user_id, limit=50)
        for quiz in quiz_history:
            if "subject" in quiz:
                subjects.add(quiz["subject"])
        
        return sorted(list(subjects))
    
    @staticmethod
    def build_student_profile(user_id: str) -> Dict:
        """
        Build comprehensive student profile from all available data
        This is the key method for predictive analytics
        
        Args:
            user_id: User ID
        
        Returns:
            Comprehensive student profile for analysis
        """
        quiz_history = UserDataAggregator.get_user_quiz_history(user_id)
        
        return {
            "user_id": user_id,
            "enrolled_subjects": UserDataAggregator.get_enrolled_subjects(user_id),
            "quiz_trends": UserDataAggregator.analyze_quiz_trends(user_id),
            "weak_topics": UserDataAggregator.extract_weak_topics_from_history(user_id),
            "study_time_pattern": {
                "average_daily_study_minutes": 90,  # Default value
                "pattern": "Consistent"
            },
            "upcoming_exams": [],
            "recommendation_count": 0,
            "quiz_history_count": len(quiz_history),
            "generated_at": datetime.utcnow().isoformat()
        }
