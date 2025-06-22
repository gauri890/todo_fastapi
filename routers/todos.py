
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException,Path, status
import models
from models import Todos
from database import engine, SessionLocal
from pydantic import BaseModel, Field
from .auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title:str = Field(min_length=3)
    description:str = Field(max_length = 100)
    priority:int = Field(gt=0,lt=6)
    complete:bool

@router.get("/")
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_specific_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todo_data =  (db.query(Todos).filter(Todos.id == todo_id)\
                  .filter(Todos.owner_id == user.get('id')).first())
    if todo_data:
        return todo_data
    raise HTTPException(status_code=404, detail = f" {todo_id} is not there")

@router.post("/todo/create-todo", status_code = status.HTTP_201_CREATED)
async def create_todo(user: user_dependency,
                      db: db_dependency, todo: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todo_model = Todos(**todo.model_dump(), owner_id = user.get('id'))
    db.add(todo_model)
    db.commit()
    return {"message" : "success"}

@router.put("/todo/update-new-todo/{todo_id}", status_code = status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency,todo:TodoRequest, todo_id:int = Path(gt=0)):
    #todo_model = Todos(**todo.model_dump())
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todo_model_db = (db.query(Todos).filter(todo_id == Todos.id)\
                     .filter(Todos.owner_id == user.get('id')).first())
    if todo_model_db is None:
        raise HTTPException(status_code=404,detail=f" {todo_id} nor found in db")
    todo_model_db.title = todo.title
    todo_model_db.description = todo.description
    todo_model_db.priority = todo.priority
    todo_model_db.complete = todo.complete

    db.add(todo_model_db)
    db.commit()
    return {"message": "success"}


@router.delete("/todo/delete-todo/{todo_id}")
async def delete_todo(user: user_dependency, db: db_dependency,todo_id:int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    todo_model = (db.query(Todos).filter(todo_id == Todos.id)\
                  .filter(Todos.owner_id == user.get('id')).first())
    if todo_model is None:
        raise HTTPException(status_code=404,detail="{todo_id} not found")
    (db.query(Todos).filter(todo_id==Todos.id)\
     .filter(Todos.owner_id == user.get('id')).delete())
    db.commit()
    return {"message": "success"}

@router.get("/ping")
async def ping():
    return {"message": "FastAPI is working"}










