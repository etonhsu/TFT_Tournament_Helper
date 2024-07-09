from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.token import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.database import get_database_session
from app.models.db_models import User as db_user
from app.models.models import UserRegisterRequest

router = APIRouter()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@router.post('/register')
async def register(form_data: UserRegisterRequest):
    with get_database_session() as db:
        username = form_data.username
        email = form_data.email

        user = db.query(db_user).filter((db_user.username == username) | (db_user.email == email)).first()
        if user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username or email already registered')

        hashed_password = pwd_context.hash(form_data.password)
        new_user = db_user(
            username=form_data.username,
            password=hashed_password,
            email=form_data.email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={'sub': form_data.username}, expires_delta=access_token_expires)
        return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_database_session() as db:
        username = form_data.username
        user = db.query(db_user).filter(db_user.username == username).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Username not found. Please register.')

        # Verify password
        if not pwd_context.verify(form_data.password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect password')

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)
        return {'access_token': access_token, 'token_type': 'bearer'}