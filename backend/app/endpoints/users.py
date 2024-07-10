from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_database_session
from app.models.db_models import User as db_user, Tournament as db_tournament, user_tournaments as db_user_tournaments
from app.models.models import UserProfile, Tournament

router = APIRouter()


@router.get('/users/{username}', response_model=UserProfile)
async def get_user_profile(username: str):
    with get_database_session() as db:
        user = db.query(db_user).filter(db_user.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_tournament_entries = db.query(db_user_tournaments).filter(db_user_tournaments.c.user_id == user.id).all()
        tournaments = []

        for entry in user_tournament_entries:
            tournament = db.query(db_tournament).filter(db_tournament.id == entry.tournament_id).first()
            organizers = db.query(db_user).join(db_tournament.organizers).filter(
                db_tournament.id == tournament.id).all()
            organizer_usernames = [organizer.username for organizer in organizers]
            tournaments.append(Tournament(
                id=tournament.id,
                name=tournament.name,
                sheets_link=tournament.sheets_link,
                form_link=tournament.form_link,
                organizers=organizer_usernames
            ))

        return UserProfile(
            username=user.username,
            email=user.email,
            tournaments=tournaments
        )
