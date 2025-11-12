from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import User
from database import get_db

# ✅ Add your schema imports here
from schemas import UserCreate, UserResponse

SECRET_KEY = "955d9098e89e52271fd8ce81d72ce7ee8f773558bf410eec9957d2198a425de6"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: str

# ✅ Create router for this file
router = APIRouter(prefix="/auth", tags=["Auth"])


# ✅ ROUTE: User Registration (this is what Swagger will call)
@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return register(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password,
        phone_number=user.phone_number,
        role=user.role
    )


def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user : str = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def register(db: Session, name: str, email: str, password: str, phone_number: str = None, role: str = "user"):
    hasher = PasswordHash.recommended()
    password_hash = hasher.hash(password)
    new_user = User(name=name, email=email, password_hash=password_hash, phone_number=phone_number, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    hasher = PasswordHash.recommended()
    if not hasher.verify(password, user.password_hash):
        return False
    return user
