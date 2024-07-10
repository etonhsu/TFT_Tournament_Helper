from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_database_session
from app.models.db_models import Tournament as db_tournament, User as db_user
from app.models.models import Tournament

router = APIRouter()


@router.get('/tournament/{tournament_id}/{tournament_name}', response_model=Tournament)
async def get_tournament(tournament_id: int, tournament_name: str):
    with get_database_session() as db:
        tournament = db.query(db_tournament).filter(db_tournament.id == tournament_id).first()
        if not tournament or tournament.name != tournament_name:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

        organizers = db.query(db_user).join(db_tournament.organizers).filter(db_tournament.id == tournament_id).all()
        organizer_usernames = [organizer.username for organizer in organizers]

        return Tournament(
            id=tournament.id,
            name=tournament.name,
            sheets_link=tournament.sheets_link,
            form_link=tournament.form_link,
            organizers=organizer_usernames
        )
