from fastapi import APIRouter
from app.database.db import db
from app.models.users_models import User
from bson import ObjectId
from app.utils.hash import (
    hash_password,
    verify_password
)
from app.models.login_model import LoginModel
from app.utils.jwt_handler import create_access_token
from fastapi import APIRouter , Header
from app.utils.jwt_handler import verify_access_token
from fastapi import Depends

from app.dependencies.auth_dependencies import (
    get_current_user
)
router = APIRouter()
@router.post("/create-user")
def create_user(user : User):
    user_data = user.model_dump()

    hashed_password = hash_password(
         user_data["password"]
    )
    user_data["password"] = hashed_password
    db["users"].insert_one(user_data)
    return{
        "message": "User created successfully"
    }
@router.get("/get-users")
def get_user():
    users = list(db["users"].find())

    for user in users:
           user["_id"] = str(user["_id"])

    return users
@router.get("/get-user/{user_id}")
def get_user(user_id: str):

    user = db["users"].find_one(
        {"_id": ObjectId(user_id)}
    )

    user["_id"] = str(user["_id"])

    return user
@router.put("/update-user/{user_id}")
def update_user(user_id: str, user: User):

    updated_data = user.model_dump()

    db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updated_data}
    )

    return {
        "message": "User updated successfully"
    }
@router.delete("/delete-user/{user_id}")
def delete_user(user_id: str):

    db["users"].delete_one(
        {"_id": ObjectId(user_id)}
    )

    return {
        "message": "User deleted successfully"
    }
@router.post("/login")
def login(data : LoginModel):
     
     user = db["users"].find_one({
          "email" : data.email
     })

     if not user :
          return {
                "message": "User not found"
          }
     is_correct_password = verify_password(
          data.password,
          user["password"]
     )
    
     if not is_correct_password:
          return{
                "message": "Invalid password"
          }
     
     token = create_access_token({
          "user_id" : str(user["_id"])
    })
     
     return {
          "access_token": token,
        "message": "Login successful"
     }
@router.get("/profile")
def get_profile(
    current_user = Depends(get_current_user)
):

    return {
        "message": "Protected route accessed",
        "user": current_user
    }