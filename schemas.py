from pydantic import BaseModel, EmailStr
from typing import Optional

# ---------------------------
# User Schemas
# ---------------------------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    role: Optional[str] = "user"

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: Optional[str]
    role: str

    class Config:
        orm_mode = True

# ---------------------------
# ToDo Schemas
# ---------------------------
class ToDoBase(BaseModel):
    title: str
    description: Optional[str] = None

class ToDoCreate(ToDoBase):
    pass

class ToDoResponse(ToDoBase):
    id: int
    user_id: int
    completed: bool

    class Config:
       from_attributes = True

