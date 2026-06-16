from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.auth.security import hash_password
from app.database.dependencies import get_db
from app.models.user import User, UserRole
from app.schemas.user import CreateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


def _role_value(role: UserRole | str) -> str:
    return role.value if isinstance(role, UserRole) else role


def _ensure_user_can_create_role(current_user: User, requested_role: UserRole) -> None:
    current_role = _role_value(current_user.role)

    if current_role == UserRole.ADMIN.value:
        allowed_roles = {UserRole.CLUB_COORDINATOR}
    elif current_role == UserRole.CLUB_COORDINATOR.value:
        allowed_roles = {
            UserRole.FACULTY_REPRESENTATIVE,
            UserRole.STUDENT_REPRESENTATIVE,
        }
    else:
        allowed_roles = set()

    if requested_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create this user role"
        )


@router.post("/", response_model=UserResponse)
def create_user(
    user: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
        ])
    )
):
    _ensure_user_can_create_role(current_user, user.role)

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role,
        is_active=True
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    return db.query(User).all()


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False
    db.commit()
    db.refresh(user)

    return user
