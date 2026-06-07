"""
Study Recommendation API Routes
Endpoints for generating personalized study recommendations using Gemini
Integrates with user quiz history and stored data for predictive analytics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from Services.recommendation_service import (
    generate_study_recommendation,
    get_detailed_topic_guidance,
    analyze_progress
)
from Services.user_data_aggregator import UserDataAggregator
from config.db import recommendations_conn
from datetime import datetime

recommendation_router = APIRouter()


# Request Models
class RecommendationRequest(BaseModel):
    subjects: List[str]
    quiz_scores: Dict[str, int]
    weak_topics: List[str]
    study_time: int
    upcoming_exams: List[str]
    user_id: Optional[str] = None


class AutoRecommendationRequest(BaseModel):
    user_id: str
    include_analysis: bool = True


class TopicGuidanceRequest(BaseModel):
    subject: str
    topic: str
    weak_areas: List[str]
    study_time_available: int
    user_id: Optional[str] = None


class ProgressAnalysisRequest(BaseModel):
    quiz_scores: Dict[str, int]
    previous_scores: Optional[Dict[str, int]] = None
    user_id: Optional[str] = None


# Endpoints

@recommendation_router.post("/api/study-recommendation")
async def get_study_recommendation(data: RecommendationRequest):
    """
    Generate personalized study recommendations based on student data.
    """
    try:
        result = await generate_study_recommendation(
            subjects=data.subjects,
            quiz_scores=data.quiz_scores,
            weak_topics=data.weak_topics,
            study_time=data.study_time,
            upcoming_exams=data.upcoming_exams,
            user_id=data.user_id
        )
        
        # Store recommendation in MongoDB
        if result["success"] and data.user_id:
            try:
                recommendation_record = {
                    "user_id": data.user_id,
                    "input_data": {
                        "subjects": data.subjects,
                        "quiz_scores": data.quiz_scores,
                        "weak_topics": data.weak_topics,
                        "study_time": data.study_time,
                        "upcoming_exams": data.upcoming_exams
                    },
                    "recommendation": result["recommendation"],
                    "created_at": datetime.utcnow(),
                    "status": "completed"
                }
                recommendations_conn.insert_one(recommendation_record)
            except Exception as db_error:
                print(f"Warning: Failed to store recommendation in DB: {db_error}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendation: {str(e)}")


@recommendation_router.post("/api/auto-recommendation")
async def get_auto_recommendation(data: AutoRecommendationRequest):
    """
    Generate recommendation using auto-aggregated user data from database (Predictive Analytics).
    
    This endpoint demonstrates true predictive analytics:
    ✓ Pulls historical data from MongoDB
    ✓ Analyzes patterns and trends
    ✓ Makes forward-looking predictions
    ✓ Tracks changes over time
    """
    try:
        # Get aggregated user data from MongoDB
        aggregator = UserDataAggregator()
        student_profile = aggregator.build_student_profile(data.user_id)
        
        # Check if user has quiz history
        if not student_profile["quiz_history_count"]:
            raise HTTPException(
                status_code=400,
                detail="No quiz history found for user. Please take some quizzes first."
            )
        
        # Extract recommendation data from aggregated profile
        subjects = student_profile["enrolled_subjects"]
        
        # Get latest quiz scores by subject
        quiz_scores = {}
        if student_profile["quiz_trends"]["subject_breakdown"]:
            for subject, metrics in student_profile["quiz_trends"]["subject_breakdown"].items():
                quiz_scores[subject] = int(metrics["latest"])
        
        # Get weak topics (top identified weak areas)
        weak_topics = [topic for topic, _ in student_profile["weak_topics"][:3]]
        
        # Get average study time
        study_time = int(student_profile["study_time_pattern"]["average_daily_study_minutes"])
        
        # Get upcoming exams
        upcoming_exams = student_profile["upcoming_exams"]
        
        # Generate recommendation using aggregated data
        result = await generate_study_recommendation(
            subjects=subjects,
            quiz_scores=quiz_scores,
            weak_topics=weak_topics,
            study_time=study_time,
            upcoming_exams=upcoming_exams,
            user_id=data.user_id
        )
        
        # Store recommendation in MongoDB
        if result["success"] and data.user_id:
            try:
                recommendation_record = {
                    "user_id": data.user_id,
                    "input_data": {
                        "subjects": subjects,
                        "quiz_scores": quiz_scores,
                        "weak_topics": weak_topics,
                        "study_time": study_time,
                        "upcoming_exams": upcoming_exams,
                        "auto_generated": True,
                        "source": "predictive_analysis"
                    },
                    "recommendation": result["recommendation"],
                    "created_at": datetime.utcnow(),
                    "status": "completed"
                }
                recommendations_conn.insert_one(recommendation_record)
            except Exception as db_error:
                print(f"Warning: Failed to store recommendation in DB: {db_error}")
        
        # Enhance response with predictive insights
        response = result.copy()
        response["data_source"] = "MongoDB (Auto-Aggregated from User History)"
        response["predictive_insights"] = {
            "quiz_trend": student_profile["quiz_trends"]["trend"],
            "average_quiz_score": student_profile["quiz_trends"]["average_score"],
            "score_improvement": student_profile["quiz_trends"]["improvement"],
            "study_consistency": student_profile["quiz_trends"]["consistency"],
            "quizzes_analyzed": student_profile["quiz_history_count"],
            "previous_recommendations_analyzed": student_profile["recommendation_count"],
            "subjects_enrolled": len(subjects),
            "weak_areas_identified": len(student_profile["weak_topics"])
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating auto-recommendation: {str(e)}")


@recommendation_router.get("/api/student-profile/{user_id}")
async def get_student_profile(user_id: str):
    """
    Get comprehensive student profile with predictive analytics insights.
    """
    try:
        aggregator = UserDataAggregator()
        profile = aggregator.build_student_profile(user_id)
        
        return {
            "success": True,
            "student_profile": profile,
            "status": "Profile retrieved successfully",
            "insights": {
                "data_points_analyzed": profile["quiz_history_count"],
                "prediction_confidence": "High" if profile["quiz_history_count"] >= 5 else "Medium" if profile["quiz_history_count"] >= 3 else "Low",
                "trend_analysis": "Available" if profile["quiz_history_count"] >= 3 else "Insufficient data",
                "weak_areas_identified": len(profile["weak_topics"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving student profile: {str(e)}")


@recommendation_router.post("/api/topic-guidance")
async def get_topic_guidance(data: TopicGuidanceRequest):
    """
    Generate detailed study guidance for a specific topic.
    """
    try:
        result = await get_detailed_topic_guidance(
            subject=data.subject,
            topic=data.topic,
            weak_areas=data.weak_areas,
            study_time_available=data.study_time_available
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating guidance: {str(e)}")


@recommendation_router.post("/api/progress-analysis")
async def get_progress_analysis(data: ProgressAnalysisRequest):
    """
    Analyze student progress and provide insights.
    """
    try:
        result = await analyze_progress(
            quiz_scores=data.quiz_scores,
            previous_scores=data.previous_scores
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing progress: {str(e)}")


@recommendation_router.get("/api/recommendation-history/{user_id}")
async def get_recommendation_history(user_id: str):
    """
    Retrieve recommendation history for a user.
    """
    try:
        records = list(recommendations_conn.find(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            limit=10
        ))
        
        # Convert ObjectId to string
        for record in records:
            record["_id"] = str(record["_id"])
            record["created_at"] = record["created_at"].isoformat()
        
        return {
            "success": True,
            "user_id": user_id,
            "count": len(records),
            "recommendations": records,
            "status": "History retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")
