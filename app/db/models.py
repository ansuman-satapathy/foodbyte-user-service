import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator



class UserRole(str, Enum):
    customer = "customer"
    restaurant = "restaurant"
    admin = "admin"


# ── Request bodies ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.customer

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateUserRequest(BaseModel):
    name: str | None = None


class AddressCreate(BaseModel):
    label: str = "Home"
    address: str
    is_default: bool = False


class AddressResponse(BaseModel):
    id: uuid.UUID
    label: str
    address: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Response bodies ───────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Internal representation ───────────────────────────────────────────────────

class UserInDB(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    password_hash: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
