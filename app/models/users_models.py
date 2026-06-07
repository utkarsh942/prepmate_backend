
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):

    full_name: str
    email: EmailStr
    password: str
    age: int
    phone_number: str

    college: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = None