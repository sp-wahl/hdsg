#! /usr/bin/env python3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette import status
from starlette.responses import HTMLResponse, FileResponse

from config import Config
from database import DBHelper, User, Voter, verify_password


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class HasVotedMetadata(BaseModel):
    ballot_box_id: str
    running_number: int


class VoterDict(BaseModel):
    number: str
    name: str
    voted: bool
    notes: Optional[str]
    ballot_box_id: Optional[str] = None
    running_number: Optional[int] = None
    timestamp: Optional[str] = None
    user_id: Optional[str] = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def get_user(username: str) -> Optional[User]:
    with DBHelper() as session:
        user = session.query(User).get(username)
        if user:
            return user


def authenticate_user(username: str, password: str) -> Union[User, bool]:
    user = get_user(username)
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
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.get("/", response_class=HTMLResponse)
async def root():
    return (Path(__file__).parent / "./html/index.html").read_text()


@app.get("/bootstrap.min.css")
async def css():
    return FileResponse(Path(__file__).parent / "html/bootstrap.min.css")


@app.get("/number/{number}", response_model=VoterDict)
async def check_number(number: str, current_user: User = Depends(get_current_user)):
    with DBHelper() as session:
        if voter := session.query(Voter).get(number):
            return voter.__dict__
        else:
            raise HTTPException(status_code=404, detail="Person not found")
    raise HTTPException(status_code=500, detail="no db connection")


@app.post("/number/{number}")
async def mark_as_voted(
    number: str, meta: HasVotedMetadata, current_user: User = Depends(get_current_user)
):
    with DBHelper() as session:
        user = session.query(User).get(current_user.username)
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
        if voter := session.query(Voter).get(number):
            if voter.voted:
                raise HTTPException(status_code=403, detail="Person already voted")
            else:
                voter.voted = True
                voter.ballot_box_id = meta.ballot_box_id
                voter.running_number = meta.running_number
                voter.timestamp = get_current_timestamp()
                voter.user = user
                session.commit()
                return True
        else:
            raise HTTPException(status_code=404, detail="Person not found")
    raise HTTPException(status_code=500, detail="no db connection")


def get_current_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/stats", response_model=dict)
async def stats(current_user: User = Depends(get_current_user)):
    with DBHelper() as session:
        results = session.execute('''SELECT SUBSTR(timestamp, 1, 13) as h, COUNT(*) as c 
                                     FROM voters 
                                     WHERE voted=1 
                                     GROUP BY h 
                                     ORDER BY h ASC''').fetchall()
        return {'marked_as_voted': {result['h']: result['c'] for result in results}}


if __name__ == "__main__":
    uvicorn.run(app)
