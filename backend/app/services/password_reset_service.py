import secrets

from datetime import (
    datetime,
    timedelta,
    timezone
)

from app.models.password_reset_token import (
    PasswordResetToken
)


class PasswordResetService:

    @staticmethod
    def create_token(
        db,
        user_id
    ):

        token = secrets.token_urlsafe(
            32
        )

        reset_token = (
            PasswordResetToken(
                user_id=user_id,
                token=token,
                expires_at=
                    datetime.now(
                        timezone.utc
                    )
                    + timedelta(hours=1)
            )
        )

        db.add(reset_token)

        db.commit()

        db.refresh(reset_token)

        return reset_token

    @staticmethod
    def validate_token(
        db,
        token
    ):

        reset_token = (
            db.query(
                PasswordResetToken
            )
            .filter(
                PasswordResetToken.token
                == token,

                PasswordResetToken.is_used
                == False
            )
            .first()
        )

        if not reset_token:
            return None

        if (
            reset_token.expires_at
            < datetime.now(
                timezone.utc
            )
        ):
            return None

        return reset_token
    '''
    @staticmethod
    def mark_used(
        db,
        reset_token
    ):

        reset_token.is_used = True

        db.commit()
    '''