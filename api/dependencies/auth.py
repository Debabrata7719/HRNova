"""Auth Dependency - JWT token verification for protected endpoints"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from src.config import get_settings

_settings = get_settings()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and return the current user payload.
    Raises HTTPException 401 if token is missing, invalid, or expired.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            _settings.SECRET_KEY,
            algorithms=[_settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
