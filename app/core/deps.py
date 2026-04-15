from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.security import decode_token
from app.db.database import get_pool
from app.db.models import UserInDB

# HTTPBearer extracts the token from the Authorization: Bearer <token> header.
# auto_error=True means FastAPI returns 403 automatically if the header is missing.
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserInDB:
    """FastAPI dependency. Add to any route that requires authentication:

    @router.get("/me")
    async def me(user: UserInDB = Depends(get_current_user)):
        ...

    Validates the JWT, then fetches the user from the database to confirm
    they still exist and are active. The DB lookup is intentional — a deleted
    or deactivated user with a valid token should still be rejected.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND is_active = TRUE",
            user_id,
        )
    if row is None:
        raise credentials_exception

    return UserInDB(**dict(row))
