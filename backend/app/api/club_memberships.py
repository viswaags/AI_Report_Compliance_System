from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.dependencies import get_db
from app.models.club import Club
from app.models.club_membership import ClubMembership
from app.models.user import User, UserRole
from app.schemas.user import AssignMembershipRequest
from app.schemas.user import BulkAssignMembershipRequest
from app.services.notification_service import (
    NotificationService
)
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/club-memberships", tags=["Club Memberships"])


def _role_value(role: UserRole | str) -> str:
    return role.value if isinstance(role, UserRole) else role


def _has_active_club_membership(
    db: Session,
    user_id: int,
    club_id: int,
    role: UserRole
) -> bool:
    return db.query(ClubMembership).filter(
        ClubMembership.user_id == user_id,
        ClubMembership.club_id == club_id,
        ClubMembership.role == role,
        ClubMembership.is_active == True
    ).first() is not None


def _ensure_membership_permission(
    db: Session,
    current_user: User,
    requested_role: UserRole,
    club_id: int
) -> None:
    current_role = _role_value(current_user.role)

    if current_role == UserRole.ADMIN.value:
        if requested_role == UserRole.CLUB_COORDINATOR:
            return
    elif current_role == UserRole.CLUB_COORDINATOR.value:
        if requested_role in {
            UserRole.FACULTY_REPRESENTATIVE,
            UserRole.STUDENT_REPRESENTATIVE,
        } and _has_active_club_membership(
            db=db,
            user_id=current_user.id,
            club_id=club_id,
            role=UserRole.CLUB_COORDINATOR
        ):
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions to assign this club membership"
    )


@router.post("/")
def assign_membership(
    membership: AssignMembershipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
        ])
    )
):
    _ensure_membership_permission(
        db=db,
        current_user=current_user,
        requested_role=membership.role,
        club_id=membership.club_id
    )

    user = db.query(User).filter(User.id == membership.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign membership to inactive user"
        )

    if _role_value(user.role) != membership.role.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership role must match user role"
        )

    club = db.query(Club).filter(Club.id == membership.club_id).first()
    if club is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )

    existing_membership = db.query(ClubMembership).filter(
        ClubMembership.user_id == membership.user_id,
        ClubMembership.club_id == membership.club_id
    ).first()

    if existing_membership:
        existing_membership.role = membership.role
        existing_membership.is_active = True
        db.commit()
        db.refresh(existing_membership)
        return existing_membership

    db_membership = ClubMembership(
        user_id=membership.user_id,
        club_id=membership.club_id,
        role=membership.role,
        is_active=True
    )

    db.add(db_membership)
    db.commit()
    db.refresh(db_membership)

    NotificationService.create_notification(
        db=db,
        user_id=user.id,
        title="Club Assignment",
        message=(
            f"You have been assigned "
            f"to club '{club.club_name}' "
            f"as {membership.role.value}."
        ),
        notification_type="MEMBERSHIP"
    )

    return db_membership

@router.post("/bulk-assign")
def bulk_assign_membership(
    membership: BulkAssignMembershipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role([
            UserRole.ADMIN,
            UserRole.CLUB_COORDINATOR,
        ])
    )
):
    user = db.query(User).filter(
        User.id == membership.user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign membership to inactive user"
        )

    if _role_value(user.role) != membership.role.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership role must match user role"
        )

    created_memberships = []

    for club_id in membership.club_ids:

        _ensure_membership_permission(
            db=db,
            current_user=current_user,
            requested_role=membership.role,
            club_id=club_id
        )

        club = db.query(Club).filter(
            Club.id == club_id
        ).first()

        if club is None:
            continue

        existing_membership = db.query(
            ClubMembership
        ).filter(
            ClubMembership.user_id == membership.user_id,
            ClubMembership.club_id == club_id
        ).first()

        if existing_membership:
            existing_membership.role = membership.role
            existing_membership.is_active = True

            created_memberships.append({
                "club_id": club_id,
                "status": "updated"
            })

        else:
            db_membership = ClubMembership(
                user_id=membership.user_id,
                club_id=club_id,
                role=membership.role,
                is_active=True
            )

            db.add(db_membership)

            created_memberships.append({
                "club_id": club_id,
                "status": "created"
            })

        NotificationService.create_notification(
            db=db,
            user_id=user.id,
            title="Club Assignment",
            message=(
                f"You have been assigned "
                f"to club '{club.club_name}' "
                f"as {membership.role.value}."
            ),
            notification_type="MEMBERSHIP"
        )

    db.commit()

    return {
        "message": "Bulk assignment completed",
        "assignments": created_memberships
    }

@router.get("/my-memberships")
def my_memberships(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(
            ClubMembership
        )
        .filter(
            ClubMembership.user_id ==
            current_user.id,

            ClubMembership.is_active ==
            True
        )
        .all()
    )

@router.get("/")
def get_memberships(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN
        )
    )
):

    return (
        db.query(
            ClubMembership
        )
        .all()
    )

@router.get("/club/{club_id}")
def memberships_by_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    return (
        db.query(
            ClubMembership
        )
        .filter(
            ClubMembership.club_id ==
            club_id,

            ClubMembership.is_active ==
            True
        )
        .all()
    )