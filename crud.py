from sqlalchemy.orm import Session
from models import ToDo

def get_todos_by_user(db: Session, user_id: int):
    return db.query(ToDo).filter(ToDo.user_id == user_id).all()

def create_todo_for_user(db: Session, title: str, description: str, user_id: int):
    new_todo = ToDo(title=title, description=description, user_id=user_id)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

def update_todo_status(db: Session, todo_id: int, completed: bool, user_id: int):
    todo = db.query(ToDo).filter(ToDo.id == todo_id, ToDo.user_id == user_id).first()
    if todo:
        todo.completed = completed
        db.commit()
        db.refresh(todo)
    return todo

def delete_todo(db: Session, todo_id: int, user_id: int):
    todo = db.query(ToDo).filter(ToDo.id == todo_id, ToDo.user_id == user_id).first()
    if todo:
        db.delete(todo)
        db.commit()
    return todo
