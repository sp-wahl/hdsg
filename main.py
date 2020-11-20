#! /usr/bin/env python3

from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import HTMLResponse, FileResponse

app = FastAPI()


class Voter(BaseModel):
    number: str
    name: str
    voted: bool
    ballot_box_id: Optional[str] = None
    running_number: Optional[int] = None
    timestamp: Optional[str] = None
    user: Optional[str] = None


class HasVotedMetadata(BaseModel):
    ballot_box_id: str
    running_number: int


FAKE_DB = {
    '2456789': Voter(number='2456789', name='Werner Wusel', voted=False)
}


@app.get("/", response_class=HTMLResponse)
async def root():
    return (Path(__file__).parent / 'html/index.html').read_text()


@app.get("/bootstrap.min.css",)
async def css():
    return FileResponse(Path(__file__).parent / 'html/bootstrap.min.css')


@app.get("/number/{number}", response_model=Voter)
async def check_number(number: str):
    if number in FAKE_DB:
        return FAKE_DB[number]
    else:
        raise HTTPException(status_code=404, detail="Person not found")


@app.post("/number/{number}")
async def mark_as_voted(number: str, meta: HasVotedMetadata):
    if number in FAKE_DB:
        raise HTTPException(status_code=403, detail="Person alredy voted")
    else:
        raise HTTPException(status_code=404, detail="Person not found")


if __name__ == '__main__':
    uvicorn.run(app)
