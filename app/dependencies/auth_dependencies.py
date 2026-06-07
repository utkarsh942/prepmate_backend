from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer

from app.utils.jwt_handler import verify_access_token

security = HTTPBearer()


def get_current_user(

    credentials = Security(security)

):

    token = credentials.credentials

    payload = verify_access_token(token)

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload