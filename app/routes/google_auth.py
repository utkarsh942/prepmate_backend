from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.database.db import db
from app.utils.jwt_handler import create_access_token
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class GoogleLoginRequest(BaseModel):
    token: str


@router.post("/google-login")
async def google_login(data: GoogleLoginRequest):
    """
    Verify Google ID token and create/login user.
    Frontend sends the credential token from Google Identity Services.
    """
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "")

        if not client_id:
            raise HTTPException(
                status_code=500,
                detail="Google Client ID not configured on server"
            )

        # Verify the token using Google's official library
        idinfo = id_token.verify_oauth2_token(
            data.token,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=10
        )

        email = idinfo.get("email")
        name = idinfo.get("name", idinfo.get("given_name", ""))
        email_verified = idinfo.get("email_verified", False)

        if not email:
            raise HTTPException(status_code=401, detail="Google token missing email")

        if not email_verified:
            raise HTTPException(status_code=401, detail="Google email not verified")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception:
        # Fallback: try the tokeninfo endpoint if google-auth library fails
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={data.token}"
                )

            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")

            idinfo = resp.json()
            email = idinfo.get("email")
            name = idinfo.get("name", idinfo.get("given_name", ""))

            if not email:
                raise HTTPException(status_code=401, detail="Google token missing email")
        except HTTPException:
            raise
        except Exception as fallback_err:
            raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(fallback_err)}")

    # Check if user already exists
    existing_user = db["users"].find_one({"email": email})

    if existing_user:
        user_id = str(existing_user["_id"])
        # Update name if it was empty before
        if not existing_user.get("full_name") and name:
            db["users"].update_one(
                {"_id": existing_user["_id"]},
                {"$set": {"full_name": name}}
            )
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
        "user_id": user_id,
        "message": "Google login successful",
        "user": {
            "full_name": name,
            "email": email,
        }
    }
