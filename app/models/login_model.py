from pydantic import BaseModel, EmailStr


class LoginModel(BaseModel):

    email: EmailStr
    password: str
