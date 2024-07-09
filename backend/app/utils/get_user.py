from fastapi import HTTPException, Depends
from app.db.database import get_database_session
from app.models.db_models import User as db_user
from app.core.token import verify_token, oauth2_scheme
from app.models.models import UserProfile


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserProfile:
    try:
        username = verify_token(token, credentials_exception=HTTPException(status_code=401, detail="Invalid token"))
        with get_database_session() as db:
            user = db.query(db_user).filter(db_user.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))