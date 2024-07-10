from fastapi import Depends, HTTPException, status, APIRouter

from app.core.token import oauth2_scheme
from app.db.database import get_database_session
from app.models.db_models import Tournament as db_tournament, user_tournaments
from app.models.models import TournamentCreateRequest
from app.utils.get_user import get_current_user
from app.utils.google_services import get_google_creds, create_google_sheet, create_google_form, \
    delete_google_sheet, delete_google_form

router = APIRouter()


@router.post('/create_tournament')
async def create_tournament(request: TournamentCreateRequest, token: str = Depends(oauth2_scheme)):
    secret_name = 'google-sheets-key'
    region_name = 'us-west-2'
    google_creds = get_google_creds(secret_name, region_name)

    user = get_current_user(token)

    sheet_id = None
    form_id = None

    try:
        sheet_id = create_google_sheet(f"Tournament: {request.name}", google_creds, user.email)
        form_id = create_google_form(f"Tournament Sign-Up: {request.name}", google_creds, user.email)

        with get_database_session() as db:
            new_tournament = db_tournament(
                name=request.name,
                sheets_link=f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
                form_link=f"https://docs.google.com/forms/d/{form_id}/edit",
                sign_up_deadline=request.sign_up_deadline,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            db.add(new_tournament)
            db.commit()
            db.refresh(new_tournament)

            new_user_tournament = user_tournaments.insert().values(
                user_id=user.id,
                tournament_id=new_tournament.id
            )
            db.execute(new_user_tournament)
            db.commit()

        return {'sheet_id': sheet_id, 'form_id': form_id}
    except Exception as e:
        if sheet_id:
            delete_google_sheet(sheet_id, google_creds)
        if form_id:
            delete_google_form(form_id, google_creds)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating tournament: {str(e)}")
