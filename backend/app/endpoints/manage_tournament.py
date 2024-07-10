from fastapi import APIRouter, HTTPException, Depends, status
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.token import oauth2_scheme
from app.db.database import get_database_session
from app.models.db_models import User as db_user, Tournament as db_tournament, user_tournaments as db_user_tournaments
from app.utils.get_user import get_current_user
from app.utils.google_services import get_google_creds, set_sheet_permissions, set_form_permissions

router = APIRouter()

@router.post('/tournament/{tournament_id}/add/{username}')
async def add_organizer(tournament_id: int, username: str, token: str = Depends(oauth2_scheme)):
    with get_database_session() as db:
        # Get the current user
        current_user = get_current_user(token)

        # Check if the current user is an organizer of the tournament
        tournament = db.query(db_tournament).filter(db_tournament.id == tournament_id).first()
        if not tournament:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

        is_organizer = db.query(db_user_tournaments).filter(
            db_user_tournaments.c.tournament_id == tournament_id,
            db_user_tournaments.c.user_id == current_user.id
        ).first()

        if not is_organizer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an organizer of this tournament")

        # Get the user to be added as organizer
        new_organizer = db.query(db_user).filter(db_user.username == username).first()
        if not new_organizer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if the user is already an organizer
        already_organizer = db.query(db_user_tournaments).filter(
            db_user_tournaments.c.tournament_id == tournament_id,
            db_user_tournaments.c.user_id == new_organizer.id
        ).first()

        if already_organizer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already an organizer")

        # Add the user to the user_tournaments table
        new_user_tournament = db_user_tournaments.insert().values(
            user_id=new_organizer.id,
            tournament_id=tournament_id
        )
        db.execute(new_user_tournament)
        db.commit()

        try:
            secret_name = 'google-sheets-key'  # Secret name in AWS Secrets Manager
            region_name = 'us-west-2'  # AWS region where your secret is stored
            google_creds = get_google_creds(secret_name, region_name)

            # Extract fileId from sheets_link and form_link
            sheet_file_id = tournament.sheets_link.split('/d/')[1].split('/')[0]
            form_file_id = tournament.form_link.split('/d/')[1].split('/')[0]

            set_sheet_permissions(sheet_file_id, google_creds, new_organizer.email)
            set_form_permissions(form_file_id, google_creds, new_organizer.email)
        except HttpError as error:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error granting Google Sheet/Form access: {error}")

        return {
            "message": f"User '{username}' added as organizer successfully and granted editor access to the Google Sheet and Form"}

