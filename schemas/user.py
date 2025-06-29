from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    user_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True