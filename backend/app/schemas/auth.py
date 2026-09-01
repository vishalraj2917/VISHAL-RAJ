import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name")
    email: EmailStr = Field(..., description="Valid Email Address")
    password: str = Field(..., min_length=8, max_length=128, description="Secure Password")
    confirm_password: Optional[str] = Field(None, description="Password Confirmation")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered Email Address")
    password: str = Field(..., description="User Password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserResponse(BaseModel):
    id: int
    name: Optional[str] = None
    username: str
    email: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Existing password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_new_password: Optional[str] = Field(None, description="Confirm new password")
