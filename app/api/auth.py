from fastapi import APIRouter, HTTPException, status
from asyncpg import UniqueViolationError
from app.db.database import get_pool
from app.db.models import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(body: RegisterRequest):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, name, password_hash, role)
                VALUES ($1, $2, $3, $4)
                RETURNING id, email, name, role, is_active, created_at
                """,
                body.email,
                body.name,
                hash_password(body.password),
                body.role.value,
            )
        except UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

    user = UserResponse(**dict(row))
    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            body.email,
        )

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    if row is None:
        raise invalid_credentials

    if not verify_password(body.password, row["password_hash"]):
        raise invalid_credentials

    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user = UserResponse(**dict(row))
    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token, user=user)
