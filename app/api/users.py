from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_pool
from app.db.models import (
    UserResponse,
    UpdateUserRequest,
    UserInDB,
    AddressCreate,
    AddressResponse,
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    if body.name is None:
        return await get_me(current_user)

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE users
            SET name = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING id, email, name, role, is_active, created_at
            """,
            body.name.strip(),
            str(current_user.id),
        )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(**dict(row))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name, role, is_active, created_at FROM users WHERE id = $1",
            user_id,
        )

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(**dict(row))


# ── Address Book ──────────────────────────────────────────────────────────


@router.get("/me/addresses", response_model=list[AddressResponse])
async def list_my_addresses(current_user: UserInDB = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_addresses WHERE user_id = $1 ORDER BY is_default DESC, created_at DESC",
            current_user.id,
        )
    return [AddressResponse(**dict(r)) for r in rows]


@router.post(
    "/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED
)
async def add_address(
    body: AddressCreate,
    current_user: UserInDB = Depends(get_current_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            if body.is_default:
                # Reset previous default
                await conn.execute(
                    "UPDATE user_addresses SET is_default = FALSE WHERE user_id = $1",
                    current_user.id,
                )

            row = await conn.fetchrow(
                """
                INSERT INTO user_addresses (user_id, label, address, is_default)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                current_user.id,
                body.label,
                body.address,
                body.is_default,
            )
    return AddressResponse(**dict(row))


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM user_addresses WHERE id = $1 AND user_id = $2",
            address_id,
            current_user.id,
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Address not found")
