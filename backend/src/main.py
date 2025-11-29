from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from db.lib.core import (
    create_user, delete_user,
    create_university, add_university_to_user
)

app = FastAPI(title="Teduco API", version="0.1.0")


#  Schemas
class UserIn(BaseModel):
    fname: str
    lname: str
    email: str
    password: str
    birth_date: str | None = None


class UniversityIn(BaseModel):
    name: str
    country: str


#  Routes
@app.post("/users", status_code=201)
def api_create_user(data: UserIn):
    user = create_user(
        fname=data.fname,
        lname=data.lname,
        email=data.email,
        password=data.password,
        birth_date=data.birth_date,
    )
    return {"user_id": user.user_id}


@app.delete("/users/{user_id}", status_code=204)
def api_delete_user(user_id: int):
    delete_user(user_id)
    return


@app.post("/universities", status_code=201)
def api_create_university(data: UniversityIn):
    uni = create_university(data.name, data.country)
    return {"university_id": uni.university_id}


@app.post("/users/{user_id}/universities/{uni_id}", status_code=204)
def api_add_uni_to_user(user_id: int, uni_id: int):
    add_university_to_user(user_id, uni_id)
    return
