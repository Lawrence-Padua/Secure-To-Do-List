from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import timedelta
from database import SessionLocal, engine, Base
import auth, models, schemas, crud
from auth import router as auth_router 
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import get_current_user
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ToDo API with Authentication")
app.include_router(auth_router)



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="FastAPI app with JWT authentication",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
# ---------------------------
# Dependencies
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_admin_user(current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

# ---------------------------
# Home
# ---------------------------
@app.get("/")
def home():
    return {"message": "✅ To-Do API is running!"}

# ---------------------------
# Auth Endpoints
# ---------------------------
@app.post("/auth/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return auth.register(db, user.name, user.email, user.password, user.phone_number, user.role)

@app.post("/auth/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = auth.create_token(
       data={"sub": user.email},
        expires_delta=timedelta(minutes=auth.EXPIRE_MINUTES)
    )
    return auth.Token(access_token=access_token, token_type="bearer", user_role=user.role)

# ---------------------------
# User Endpoints
# ---------------------------

@app.get("/users/me", response_model=schemas.UserResponse)
def read_own_profile(current_user : str = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/me", response_model=schemas.UserResponse)
def update_own_profile(name: str = None, phone_number: str = None,
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    if name:
        current_user.name = name
    if phone_number:
        current_user.phone_number = phone_number
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/users/me/change-password")
def change_password(current_password: str, new_password: str,
                    db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.get_current_user)):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not pwd_context.verify(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = pwd_context.hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}

# ---------------------------
# Todo Endpoints (Non-Admin)
# ---------------------------
@app.get("/todos", response_model=list[schemas.ToDoResponse])
def get_user_todos(db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_todos_by_user(db, current_user.id)

@app.post("/todos", response_model=schemas.ToDoResponse)
def create_todo(todo: schemas.ToDoCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_todo_for_user(db, todo.title, todo.description, current_user.id)

@app.put("/todos/{todo_id}", response_model=schemas.ToDoResponse)
def update_todo(todo_id: int, completed: bool,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    todo = crud.update_todo_status(db, todo_id, completed, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found or not yours")
    return todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    todo = crud.delete_todo(db, todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found or not yours")
    return {"message": "Todo deleted successfully"}

# ---------------------------
# Admin Endpoints
# ---------------------------
@app.get("/admin/todos", response_model=list[schemas.ToDoResponse])
def get_all_todos(db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    return db.query(models.ToDo).all()

@app.delete("/admin/todos/{todo_id}")
def admin_delete_todo(todo_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    todo = db.query(models.ToDo).filter(models.ToDo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}

@app.get("/admin/users", response_model=list[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    return db.query(models.User).all()

@app.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
