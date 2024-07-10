from datetime import date, datetime
from typing import List
from pydantic import BaseModel


class Tournament(BaseModel):
    id: int
    name: str
    sheets_link: str
    form_link: str
    sign_up_deadline: datetime
    start_date: date
    end_date: date
    organizers: List[str]

    class Config:
        orm_mode: True


class TournamentCreateRequest(BaseModel):
    name: str
    sign_up_deadline: datetime
    start_date: date
    end_date: date


class User(BaseModel):
    id: int
    username: str
    password: str
    email: str
    tournaments: List[int]  # List of tournament IDs

    class Config:
        orm_mode: True


class UserProfile(BaseModel):
    username: str
    email: str
    tournaments: List[Tournament]


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str

