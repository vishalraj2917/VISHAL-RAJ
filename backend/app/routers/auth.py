import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    AuthTokenResponse,
    UserUpdateRequest,
    ChangePasswordRequest,
)
from app.utils.security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    get_current_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Authentication & Users"]
)


@router.post(
    "/auth/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Registers a new user, hashes password securely, stores user in PostgreSQL, and returns authentication token.",
)
def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    # 1. Password confirmation check
    if request.confirm_password and request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password confirmation does not match."
        )

    # 2. Password strength validation
    try:
        validate_password_strength(request.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    # 3. Check for existing email or username
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    # Username derivation from email or name
    base_username = request.email.split("@")[0]
    username = base_username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1

    # 4. Hash password and save User
    new_user = User(
        name=request.name,
        username=username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        is_active=True,
        last_login=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 5. Generate JWT token
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post(
    "/auth/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate & Login User",
    description="Validates email and password, updates last login, and returns JWT Bearer token.",
)
def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been disabled."
        )

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout User",
    description="Stateless logout endpoint acknowledging session termination for client token disposal.",
)
def logout_user():
    return {
        "success": True,
        "message": "Successfully logged out. Client token discarded."
    }


@router.get(
    "/auth/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
)
def get_auth_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


@router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Profile",
)
def get_user_profile(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


@router.put(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
)
def update_user_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.name is not None:
        current_user.name = request.name

    if request.email is not None and request.email != current_user.email:
        # Verify unique email
        existing = db.query(User).filter(User.email == request.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists."
            )
        current_user.email = request.email

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post(
    "/users/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change User Password",
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Verify existing password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )

    # 2. Confirmation check
    if request.confirm_new_password and request.new_password != request.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password confirmation does not match."
        )

    # 3. Strength validation
    try:
        validate_password_strength(request.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    # 4. Update hash
    current_user.hashed_password = get_password_hash(request.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "message": "Password changed successfully."
    }
