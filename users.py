from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserResponse
from auth import get_current_user  # ✅ Import from your auth.py

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_logged_in_user(
    current_user: User = Depends(get_current_user),  # ✅ Token validation happens here
    db: Session = Depends(get_db)
):
    return current_user
