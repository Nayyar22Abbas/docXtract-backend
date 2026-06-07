"""
Smart Study Recommendation Service using Gemini API
Provides personalized study recommendations based on student data
"""

import google.generativeai as genai
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

# Initialize Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY")))


async def generate_study_recommendation(
    subjects: List[str],
    quiz_scores: Dict[str, int],
    weak_topics: List[str],
    study_time: int,
    upcoming_exams: List[str],
    user_id: Optional[str] = None
) -> Dict:
    """
    Generate personalized study recommendations using Gemini API.
    
    Args:
        subjects: List of subjects enrolled
        quiz_scores: Dictionary of quiz scores per subject
        weak_topics: List of identified weak topics
        study_time: Average daily study time in minutes
        upcoming_exams: List of upcoming exams with dates
        user_id: Optional user ID for tracking recommendations
    
    Returns:
        Dictionary with study recommendations
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
You are an AI academic advisor inside a student study companion application.

Your task is to generate personalized study recommendations.

Student Data:
- Subjects enrolled: {subjects}
- Recent quiz scores per subject: {quiz_scores}
- Weak topics: {weak_topics}
- Average study time per day (minutes): {study_time}
- Upcoming exams: {upcoming_exams}

Instructions:
1. Identify which subject needs the most focus.
2. Suggest the next topic the student should study.
3. Recommend daily study duration for the next 7 days.
4. If any quiz score is below 50%, strongly recommend revision.
5. Keep response structured in JSON format only.

Return JSON in this exact format only, with no additional text:

{{
  "priority_subject": "",
  "recommended_topic": "",
  "recommended_daily_study_minutes": "",
  "reasoning": "",
  "motivation_message": ""
}}

Do not include any explanations outside the JSON.
"""
    
    try:
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        result_text = response.text.strip()
        
        # Try to find JSON block if wrapped in code blocks
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        
        # Parse JSON response
        recommendation = json.loads(result_text)
        
        # Add metadata
        recommendation["generated_at"] = datetime.utcnow().isoformat()
        recommendation["user_id"] = user_id
        
        return {
            "success": True,
            "recommendation": recommendation,
            "status": "Generated successfully"
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse recommendation: {str(e)}",
            "raw_response": response.text if response else None,
            "status": "JSON parsing error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "Error generating recommendation"
        }


async def get_detailed_topic_guidance(
    subject: str,
    topic: str,
    weak_areas: List[str],
    study_time_available: int
) -> Dict:
    """
    Generate detailed study guidance for a specific topic.
    
    Args:
        subject: Subject name
        topic: Specific topic to study
        weak_areas: Specific areas of weakness within the topic
        study_time_available: Available study time in minutes
    
    Returns:
        Dictionary with detailed study guidance
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
You are an expert tutor providing detailed study guidance.

Study Plan Request:
- Subject: {subject}
- Topic: {topic}
- Weak areas within topic: {weak_areas}
- Available study time: {study_time_available} minutes

Provide a structured study plan in JSON format:

{{
  "topic": "",
  "duration_minutes": "",
  "learning_objectives": [],
  "study_steps": [
    {{
      "step": 1,
      "duration": "",
      "activity": "",
      "description": ""
    }}
  ],
  "key_concepts": [],
  "practice_exercises": [],
  "common_mistakes": [],
  "resources": []
}}

Return only valid JSON with no additional text.
"""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Try to find JSON block if wrapped in code blocks
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        
        guidance = json.loads(result_text)
        
        return {
            "success": True,
            "guidance": guidance,
            "status": "Guidance generated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "Error generating guidance"
        }


async def analyze_progress(
    quiz_scores: Dict[str, int],
    previous_scores: Optional[Dict[str, int]] = None
) -> Dict:
    """
    Analyze student progress and provide insights.
    
    Args:
        quiz_scores: Current quiz scores
        previous_scores: Previous quiz scores for comparison
    
    Returns:
        Dictionary with progress analysis
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    comparison = ""
    if previous_scores:
        comparison = f"\nPrevious scores: {previous_scores}\nCurrent scores: {quiz_scores}"
    else:
        comparison = f"\nCurrent scores: {quiz_scores}"
    
    prompt = f"""
Analyze the following quiz score data and provide structured feedback:

{comparison}

Provide analysis in JSON format:

{{
  "overall_performance": "",
  "improvements": [],
  "areas_of_concern": [],
  "performance_trend": "",
  "next_steps": []
}}

Return only valid JSON with no additional text.
"""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Try to find JSON block
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        
        analysis = json.loads(result_text)
        
        return {
            "success": True,
            "analysis": analysis,
            "status": "Analysis completed successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "Error analyzing progress"
        }
