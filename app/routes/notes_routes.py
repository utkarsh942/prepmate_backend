from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    Query

)
from datetime import datetime
from app.database.db import db
from app.dependencies.auth_dependencies import (
    get_current_user
)
from fastapi.responses import Response
from bson import ObjectId
from app.utils.pdf_extractor import (
    extract_text_from_pdf
)
from app.utils.quiz_generator import (
    generate_quiz
)
from app.utils.summary_generator import generate_summary
from app.utils.flashcard_generator import generate_flashcards

router = APIRouter()
@router.post("/upload-notes")
async def upload_note(
    title : str = Form(),
    description : str = Form(),
    subject : str = Form(),
    file : UploadFile = File(),
    current_user: dict= Depends(get_current_user)
):
    file_data = await file.read()
    extracted_text = ""
    if file.content_type == "application/pdf":
        extracted_text = extract_text_from_pdf(
            file_data
        )
    note_document = {
        "title" : title,
        "description" : description,
        "subject" : subject,
        "filename" : file.filename,
        "content_type" : file.content_type,
         "uploaded_by": current_user["user_id"],
          "file_data" : file_data,
        "uploaded_at": datetime.utcnow(),

        "file_size": len(file_data),
        "extracted_text": extracted_text
    }
    db["notes"].insert_one(note_document)
    return {
          "message": "Note uploaded successfully"
    }
@router.get("/get-notes")
def get_notes(
    page: int = Query(1, description="Page number starting from 1"),
    limit: int = Query(10, description="Number of notes per page"),
    sort: str = Query("latest", description="Sort by 'latest' or 'oldest'"),
    current_user: dict = Depends(get_current_user)
):
    # 1. Calculate how many notes to skip based on current page
    # If page=1 and limit=10 -> skip = 0
    # If page=2 and limit=10 -> skip = 10
    skip = (page - 1) * limit

    # 2. Set sorting order (-1 for descending/newest first, 1 for ascending)
    sort_order = -1
    if sort == "oldest":
        sort_order = 1

    # 3. Query MongoDB with sort, skip, and limit
    notes = list(
        db["notes"]
        .find({"uploaded_by": current_user["user_id"]})
        .sort("uploaded_at", sort_order)
        .skip(skip)
        .limit(limit)
    )

    # 4. Clean up the response formatting
    for note in notes:
        note["_id"] = str(note["_id"])
        note["uploaded_at"] = str(note["uploaded_at"])
        if "file_data" in note:
            del note["file_data"]

    return notes
@router.get("/download-note/{note_id}")
def download_note(

    note_id: str,

    current_user: dict = Depends(get_current_user)

):

    note = db["notes"].find_one({

        "_id": ObjectId(note_id),

        "uploaded_by": current_user["user_id"]

    })

    if not note:

        return {
            "message": "Note not found"
        }

    return Response(

        content=note["file_data"],

        media_type=note["content_type"],

        headers={

            "Content-Disposition":
            f"attachment; filename={note['filename']}"

        }

    )
@router.delete("/delete-note/{note_id}")
def delete_note(
    note_id : str,
    current_user: dict = Depends(get_current_user)
):
    result = db["notes"].delete_one({
        "_id": ObjectId(note_id),
        "uploaded_by": current_user["user_id"]
    })

    if result.deleted_count == 0:
        return {
            "message": "Note not found"
        }
    
    return {
        "message": "Note deleted successfully"
    }
@router.put("/update-note/{note_id}")
def update_note(

    note_id: str,

    title: str = Form(),

    description: str = Form(),

    subject: str = Form(),

    current_user: dict = Depends(get_current_user)

):

    result = db["notes"].update_one(

        {

            "_id": ObjectId(note_id),

            "uploaded_by": current_user["user_id"]

        },

        {

            "$set": {

                "title": title,

                "description": description,

                "subject": subject

            }

        }

    )

    if result.matched_count == 0:

        return {
            "message": "Note not found"
        }

    return {

        "message": "Note updated successfully"

    }
@router.get("/search-notes")
def search_notes(

    query: str,

    current_user: dict = Depends(get_current_user)

):

    notes = list(

        db["notes"].find({

            "uploaded_by": current_user["user_id"],

            "$or": [

                {

                    "title": {

                        "$regex": query,

                        "$options": "i"

                    }

                },

                {

                    "subject": {

                        "$regex": query,

                        "$options": "i"

                    }

                }

            ]

        })

    )

    for note in notes:

        note["_id"] = str(note["_id"])

        note["uploaded_at"] = str(note["uploaded_at"])

        if "file_data" in note:

            del note["file_data"]

    return notes

@router.get("/generate-quiz/{note_id}")
def generate_note_quiz(
    note_id: str,
    num_questions: int = Query(5, description="Number of questions"),
    difficulty: str = Query("medium", description="Difficulty: easy, medium, hard"),
    current_user: dict = Depends(get_current_user)
):
    # Find the note and ensure it belongs to the logged-in user
    note = db["notes"].find_one({
        "_id": ObjectId(note_id),
        "uploaded_by": current_user["user_id"]
    })

    if not note:
        return {"message": "Note not found"}

    # Use cache only when using default settings
    is_default = (num_questions == 5 and difficulty == "medium")
    if is_default and "generated_quiz" in note and note["generated_quiz"]:
        cached = note["generated_quiz"]
        # Handle legacy string format — regenerate if cached data is a string
        if isinstance(cached, list) and len(cached) > 0:
            return {
                "questions": cached,
                "source": "database"
            }

    extracted_text = note.get("extracted_text", "").strip()

    if not extracted_text:
        return {"message": "No extracted text found in this note to generate a quiz."}

    # Truncate text to avoid crashing on massive textbook notes files
    truncated_text = " ".join(extracted_text.split()[:12000])

    try:
        # Call the updated Gemini utility with config
        questions = generate_quiz(truncated_text, num_questions=num_questions, difficulty=difficulty)

        # Cache default quiz results back into MongoDB
        if is_default:
            db["notes"].update_one(
                {"_id": ObjectId(note_id)},
                {"$set": {"generated_quiz": questions}}
            )

        return {
            "questions": questions,
            "source": "generated_now"
        }
    except Exception as e:
        return {"message": f"Quiz Generation Error: {str(e)}"}


@router.get("/generate-summary/{note_id}")
def generate_note_summary(
    note_id: str,
    current_user: dict = Depends(get_current_user)
):
    # 1. Find the note and ensure the user owns it
    note = db["notes"].find_one({
        "_id": ObjectId(note_id),
        "uploaded_by": current_user["user_id"]
    })

    if not note:
        return {"message": "Note not found"}

    # 2. Check if a summary was already generated before to save API tokens
    if "ai_summary" in note and note["ai_summary"]:
        return {
            "summary": note["ai_summary"],
            "source": "database"
        }

    extracted_text = note.get("extracted_text", "").strip()

    if not extracted_text:
        return {"message": "No extracted text found in this note to summarize."}

    # 3. Truncate text slightly to keep the prompt clean and fast
    truncated_text = " ".join(extracted_text.split()[:12000])

    try:
        # 4. Generate the summary using our Gemini utility
        summary = generate_summary(truncated_text)

        # 5. Save the summary inside MongoDB under this note's document
        db["notes"].update_one(
            {"_id": ObjectId(note_id)},
            {"$set": {"ai_summary": summary}}
        )

        return {
            "summary": summary,
            "source": "generated_now"
        }
    except Exception as e:
        return {"message": f"Gemini Error: {str(e)}"}
@router.get("/generate-flashcards/{note_id}")
def generate_note_flashcards(
    note_id: str,
    current_user: dict = Depends(get_current_user)
):
    # 1. Find the note and verify ownership
    note = db["notes"].find_one({
        "_id": ObjectId(note_id),
        "uploaded_by": current_user["user_id"]
    })

    if not note:
        return {"message": "Note not found"}

    # 2. Database Caching: If flashcards already exist, return them directly
    if "flashcards" in note and note["flashcards"]:
        return {
            "flashcards": note["flashcards"],
            "source": "database"
        }

    extracted_text = note.get("extracted_text", "").strip()
    if not extracted_text:
        return {"message": "No extracted text found in this note to generate flashcards."}

    # Truncate text slightly to keep things fast and safe for the prompt
    truncated_text = " ".join(extracted_text.split()[:12000])

    try:
        # 3. Call our new helper function
        flashcards = generate_flashcards(truncated_text)

        # 4. Save the flashcards to MongoDB so we don't hit the API twice
        db["notes"].update_one(
            {"_id": ObjectId(note_id)},
            {"$set": {"flashcards": flashcards}}
        )

        return {
            "flashcards": flashcards,
            "source": "generated_now"
        }
    except Exception as e:
        return {"message": f"Gemini Flashcard Error: {str(e)}"}

    
