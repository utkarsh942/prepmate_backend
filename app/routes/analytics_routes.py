from fastapi import APIRouter, Depends
from datetime import datetime
from app.database.db import db
from app.dependencies.auth_dependencies import get_current_user

router = APIRouter()

@router.post("/submit-quiz")
def submit_quiz_results(
    note_id : str,
    total_questions : int,
    correct_answers : int,
    time_spent_seconds: int,
    per_question_time: list[int], 
    current_user: dict = Depends(get_current_user)
):
    incorrect_answers = total_questions - correct_answers

    accuracy = 0.0
    if(total_questions> 0):
        accuracy = round((correct_answers/total_questions)*100,2)

    attempt_document = {
            "user_id": current_user["user_id"],
            "note_id": note_id,
            "attempted_at": datetime.utcnow(),
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "accuracy": accuracy,
            "time_spent_seconds": time_spent_seconds,
            "per_question_time": per_question_time
        }

    result = db["quiz_attempts"].insert_one(attempt_document)
    return {
        "status": "success",
        "message": "Quiz results submitted successfully!",
        "attempt_id": str(result.inserted_id)
    }

from bson import ObjectId

@router.get("/quiz-analytics/{attempt_id}")
def get_specific_quiz_analytics(
    attempt_id: str,
    current_user: dict = Depends(get_current_user)
):
    attempt = db["quiz_attempts"].find_one({
        "_id": ObjectId(attempt_id),
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

    return {
        "total_quizzes_taken": total_quizzes,
        "total_questions_solved": total_questions,
        "overall_correct": total_correct,
        "overall_incorrect": total_incorrect,
        "average_accuracy": avg_accuracy,
        "average_time_per_quiz_seconds": avg_time_per_quiz,
        "recent_attempts": attempts[::-1] 
    }

