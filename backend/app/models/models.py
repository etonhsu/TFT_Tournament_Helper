from typing import List
from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    password: str
    tournaments: List[int]  # List of tournament IDs

    class Config:
        orm_mode: True


class Tournament(BaseModel):
    id: int
    name: str
    link: str
    organizers: List[int]  # List of user IDs

    class Config:
        orm_mode: True


class UserProfile(BaseModel):
    username: str
    tournaments: List[Tournament]

