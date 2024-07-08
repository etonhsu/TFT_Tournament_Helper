from datetime import datetime, timedelta, timezone
import logging

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.db.database import get_db, get_database_session
from app.models.db_models import User as db_user, user_tournaments, Tournament as db_tournament
from app.models.models import Tournament, User, UserProfile
from app.utils.get_secret import get_secret

# Fetch secrets from AWS Secrets Manager
secrets = get_secret('tft-tournament-keys')
key = secrets.get('secret_key')  # Use 'fallback_secret_key' if 'secret_key' not found
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

logging.basicConfig(level=logging.DEBUG)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=ALGORITHM)
    logging.debug(f"Token created with expiry {expire} and data {to_encode}")
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        logging.debug(f"Decoded payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.ExpiredSignatureError as e:
        logging.error("Token expired: " + str(e))
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.DecodeError as e:
        logging.error("Token decode error: " + str(e))
        raise credentials_exception


def get_user_from_token(token: str = Depends(oauth2_scheme)):
    try:
        username = verify_token(token, credentials_exception=HTTPException(status_code=401, detail="Invalid token"))
        logging.debug(f"Username from token: {username}")

        with get_database_session() as db:
            user = db.query(db_user).filter(db_user.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            logging.debug(f"User record: {user}")

            user_tournaments_query = db.query(user_tournaments).filter(user_tournaments.c.user_id == user.id).all()
            tournaments = []
            for ut in user_tournaments_query:
                tournament = db.query(db_tournament).filter(db_tournament.id == ut.tournament_id).first()
                tournaments.append(
                    Tournament(
                        id=tournament.id,
                        name=tournament.name,
                        link=tournament.link,
                        organizers=[user.id for user in tournament.organizers]
                    )
                )

            user_profile = UserProfile(
                username=user.username,
                tournaments=tournaments,
            )
            logging.debug(f"UserProfile: {user_profile}")
            return user_profile
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")