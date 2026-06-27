import uuid
from app.models.user import User
from app.models.invitation import UserInvitation
from app.core.security import hash_password, verify_password


def validate_invitation(db, token: str):
    return db.query(UserInvitation).filter(
        UserInvitation.token == token,
        UserInvitation.status == "PENDING"
    ).first()


def create_user_from_invitation(db, invitation: UserInvitation, password: str):

    user = User(
        email=invitation.email,
        role=invitation.role,
        password_hash=hash_password(password),
        must_change_password=False
    )

    invitation.status = "USED"

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user