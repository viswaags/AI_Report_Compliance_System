from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.auth.security import verify_password
from app.auth.security import hash_password
from app.database.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginResponse
from app.auth.dependencies import get_current_user, require_role
from app.schemas.password import ChangePasswordRequest, ResetPasswordRequest
from app.schemas.password import (
    ForgotPasswordRequest
)

from app.services.password_reset_service import (
    PasswordResetService
)

from app.services.email_service import (
    EmailService
)
from app.schemas.password import (
    AdminResetPasswordRequest
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    role = user.role.value if isinstance(user.role, UserRole) else user.role

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=role,
        must_change_password=
            user.must_change_password
    )

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    if not verify_password(
        request.old_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )

    current_user.password_hash = hash_password(
        request.new_password
    )

    current_user.must_change_password = False

    db.commit()

    return {
        "message": "Password changed successfully"
    }

@router.post("/admin-reset-password/{user_id}")
def reset_password(
    user_id: int,
    request: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password_hash = hash_password(
        request.new_password
    )

    user.must_change_password = True

    db.commit()

    return {
        "message": "Password reset successfully"
    }

@router.post(
    "/forgot-password"
)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.email ==
            request.email
        )
        .first()
    )

    if not user:
        return {
            "message":
            "If account exists, reset link sent"
        }

    reset_token = (
        PasswordResetService
        .create_token(
            db,
            user.id
        )
    )

    EmailService.send_email(
        recipients=[user.email],
        subject="Password Reset",
        body=(
            "Use the following token to reset your password.\n\n"
            f"{reset_token.token}\n\n"
            "This token expires in 1 hour."
        )
    )

    return {
        "message":
        "Reset token sent"
    }

@router.post(
    "/reset-password"
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    reset_token = (
        PasswordResetService
        .validate_token(
            db,
            request.token
        )
    )

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )

    user = (
        db.query(User)
        .filter(
            User.id ==
            reset_token.user_id
        )
        .first()
    )

    user.password_hash = (
        hash_password(
            request.new_password
        )
    )

    user.must_change_password = False

    db.commit()

    return {
        "message":
        "Password reset successful"
    }

@router.get("/me")
def me(
    current_user: User = Depends(
        get_current_user
    )
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": (
            current_user.role.value
            if isinstance(
                current_user.role,
                UserRole
            )
            else current_user.role
        ),
        "must_change_password":
            current_user.must_change_password,
        "is_active":
            current_user.is_active
    }