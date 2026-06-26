from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from app.database.db import db
from app.dependencies.auth_dependencies import get_current_user

router = APIRouter()


class QuizSubmission(BaseModel):
    note_id: str
    total_questions: int
    correct_answers: int
    time_spent_seconds: int
    per_question_time: List[int] = []


@router.post("/submit-quiz")
def submit_quiz_results(
    data: QuizSubmission,
    current_user: dict = Depends(get_current_user)
):
    incorrect_answers = data.total_questions - data.correct_answers

    accuracy = 0.0
    if data.total_questions > 0:
        accuracy = round((data.correct_answers / data.total_questions) * 100, 2)

    attempt_document = {
        "user_id": current_user["user_id"],
        "note_id": data.note_id,
        "attempted_at": datetime.utcnow(),
        "total_questions": data.total_questions,
        "correct_answers": data.correct_answers,
        "incorrect_answers": incorrect_answers,
        "accuracy": accuracy,
        "time_spent_seconds": data.time_spent_seconds,
        "per_question_time": data.per_question_time
    }

    result = db["quiz_attempts"].insert_one(attempt_document)
    return {
        "status": "success",
        "message": "Quiz results submitted successfully!",
        "attempt_id": str(result.inserted_id)
    }


@router.get("/quiz-analytics/{attempt_id}")
def get_specific_quiz_analytics(
    attempt_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        obj_id = ObjectId(attempt_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid attempt ID format")

    attempt = db["quiz_attempts"].find_one({
        "_id": obj_id,
        "user_id": current_user["user_id"]
    })

    if not attempt:
        return {"status": "error", "message": "Quiz attempt not found."}

    attempt["_id"] = str(attempt["_id"])
    attempt["attempted_at"] = str(attempt["attempted_at"])

    return attempt


@router.get("/test-analytics")
def get_dashboard_analytics(current_user: dict = Depends(get_current_user)):

    attempts = list(db["quiz_attempts"].find({"user_id": current_user["user_id"]}))

    if not attempts:
        return {
            "total_quizzes_taken": 0,
            "total_questions_solved": 0,
            "overall_correct": 0,
            "overall_incorrect": 0,
            "average_accuracy": 0.0,
            "average_time_per_quiz_seconds": 0,
            "study_streak": 0,
            "weekly_activity": [],
            "accuracy_trend": [],
            "recent_attempts": []
        }

    total_quizzes = len(attempts)
    total_questions = 0
    total_correct = 0
    total_incorrect = 0
    sum_accuracy = 0.0
    total_time_spent = 0

    for attempt in attempts:
        total_questions += attempt.get("total_questions", 0)
        total_correct += attempt.get("correct_answers", 0)
        total_incorrect += attempt.get("incorrect_answers", 0)
        sum_accuracy += attempt.get("accuracy", 0.0)
        total_time_spent += attempt.get("time_spent_seconds", 0)

        attempt["_id"] = str(attempt["_id"])
        attempt["attempted_at"] = str(attempt["attempted_at"])

    avg_accuracy = round(sum_accuracy / total_quizzes, 2)
    avg_time_per_quiz = round(total_time_spent / total_quizzes)

    # --- Study Streak: consecutive days with quiz attempts ---
    attempt_dates = set()
    for attempt in attempts:
        try:
            dt = datetime.fromisoformat(attempt["attempted_at"])
            attempt_dates.add(dt.date())
        except (ValueError, TypeError):
            pass

    study_streak = 0
    if attempt_dates:
        today = datetime.utcnow().date()
        current_date = today
        # Allow streak to start from today or yesterday
        if current_date not in attempt_dates:
            current_date = today - timedelta(days=1)
        while current_date in attempt_dates:
            study_streak += 1
            current_date -= timedelta(days=1)

    # --- Weekly Activity: last 7 days, count of quizzes per day ---
    today = datetime.utcnow().date()
    weekly_activity = []
    
    # Extract all attempt dates as list to properly count duplicates
    all_attempt_dates = []
    for attempt in attempts:
        try:
            dt = datetime.fromisoformat(attempt["attempted_at"])
            all_attempt_dates.append(dt.date())
        except (ValueError, TypeError):
            pass

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = sum(1 for d in all_attempt_dates if d == day)
        weekly_activity.append({
            "date": str(day),
            "quizzes": count
        })

    # --- Accuracy Trend: last 10 quiz accuracies ---
    sorted_attempts = sorted(
        attempts,
        key=lambda a: a.get("attempted_at", "")
    )
    accuracy_trend = [
        {
            "attempted_at": a["attempted_at"],
            "accuracy": a.get("accuracy", 0.0)
        }
        for a in sorted_attempts[-10:]
    ]

    return {
        "total_quizzes_taken": total_quizzes,
        "total_questions_solved": total_questions,
        "overall_correct": total_correct,
        "overall_incorrect": total_incorrect,
        "average_accuracy": avg_accuracy,
        "average_time_per_quiz_seconds": avg_time_per_quiz,
        "study_streak": study_streak,
        "weekly_activity": weekly_activity,
        "accuracy_trend": accuracy_trend,
        "recent_attempts": attempts[::-1]
    }
