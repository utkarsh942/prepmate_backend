from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.db import db
from app.utils.jwt_handler import create_access_token
import httpx

router = APIRouter()


class GoogleLoginRequest(BaseModel):
    token: str


@router.post("/google-login")
async def google_login(data: GoogleLoginRequest):
    """
    Verify Google ID token and create/login user.
    Frontend sends the credential token from Google Identity Services.
    """
    # Verify token with Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={data.token}"
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_data = resp.json()
    email = google_data.get("email")
    name = google_data.get("name", "")

    if not email:
        raise HTTPException(status_code=401, detail="Google token missing email")

    # Check if user already exists
    existing_user = db["users"].find_one({"email": email})

    if existing_user:
        user_id = str(existing_user["_id"])
    else:
        # Create new user from Google data
        new_user = {
            "full_name": name,
            "email": email,
            "password": "",  # No password for Google users
            "age": 0,
            "phone_number": "",
            "auth_provider": "google",
        }
        result = db["users"].insert_one(new_user)
        user_id = str(result.inserted_id)

    # Generate JWT
    token = create_access_token({"user_id": user_id})

    return {
        "access_token": token,
        "message": "Google login successful",
        "user": {
            "full_name": name,
            "email": email,
        }
    }
