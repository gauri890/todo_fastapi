from http.client import HTTPException
from datetime import timedelta, datetime, timezone
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from models import Users
from passlib.context import CryptContext
from database import SessionLocal
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
#app = FastAPI()

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = "a35b2a7f669a45303a5f5918a906edeaab0df82450ebb79558dc98999078db82"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    email: str
    user_name: str
    first_name: str
    last_name: str
    password: str
    is_active: bool
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username:str, password:str,db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
        #raise HTTPException(status_code=404,detail= f"wrong username {user.username}")
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
        #raise HTTPException(status_code=404, detail=f"wrong password {user.username}")
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="could not validate user.")
        return {"username": username, "id": user_id, "role": user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="could not validate user.")

@router.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(db : db_dependency,user : CreateUserRequest):
    user_model = Users(
        email = user.email,
        username = user.user_name,
        first_name = user.first_name,
        last_name = user.last_name,
        role = user.role,
        hashed_password = bcrypt_context.hash(user.password),
        is_active = True
    )
    db.add(user_model)
    db.commit()
    return {"message":"user added successfully"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db:db_dependency):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="could not validate user.")
        #raise HTTPException(status_code=404,detail= "Invalid Credentials")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}


