#! /usr/bin/env python3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette import status
from starlette.responses import HTMLResponse, FileResponse

SECRET_KEY = "1883eb9a04f787018d99ff7dceb4ade9af17cf91d70593336e13a40630dd18c5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 18 * 60

fake_users_db = {
    "user": {
        "username": "user",
        "hashed_password": "$2b$12$Y6RC4UvB1BxaGYplOEz2j.UH.npri0.U1W.nwkYmu9AXwn0P77tjC",
    },
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$FnGYehrndqa2Yx6gkaY6Zevbl3I4Xvg4Q9.qn0KvQX/xa5nPwp86.",
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class Voter(BaseModel):
    number: str
    name: str
    voted: bool
    notes: Optional[str] = None
    ballot_box_id: Optional[str] = None
    running_number: Optional[int] = None
    timestamp: Optional[str] = None
    user: Optional[str] = None


class HasVotedMetadata(BaseModel):
    ballot_box_id: str
    running_number: int


FAKE_DB = {
    '2475974': Voter(number='2475974', name='Werner Wusel', voted=False),
    '123456789': Voter(number='123456789', name='Greta Weinrich', voted=False, notes='Zweitschrift'),
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.get("/", response_class=HTMLResponse)
async def root():
    return (Path(__file__).parent / 'html/index.html').read_text()


@app.get("/bootstrap.min.css", )
async def css():
    return FileResponse(Path(__file__).parent / 'html/bootstrap.min.css')


@app.get("/number/{number}", response_model=Voter)
async def check_number(number: str, current_user: User = Depends(get_current_user)):
    if number in FAKE_DB:
        return FAKE_DB[number]
    else:
        raise HTTPException(status_code=404, detail="Person not found")


@app.post("/number/{number}")
async def mark_as_voted(number: str, meta: HasVotedMetadata, current_user: User = Depends(get_current_user)):
    if number in FAKE_DB:
        raise HTTPException(status_code=403, detail="Person alredy voted")
    else:
        raise HTTPException(status_code=404, detail="Person not found")


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


if __name__ == '__main__':
    uvicorn.run(app)
