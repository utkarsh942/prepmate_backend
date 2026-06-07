from pydantic import BaseModel
from typing import Optional

class Note(BaseModel):
    title : str
    description : Optional[str] = None
    subject : str