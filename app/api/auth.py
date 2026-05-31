from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.services.selection import get_or_create_settings
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


from app.core.dependencies import get_current_user
from app.schemas.user import UserOut

@router.get("/me", response_model=UserOut, summary="Get current user info")
def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return user


@router.post("/login", response_model=TokenResponse, summary="Account login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username, User.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    site_settings = get_or_create_settings(db)
    expires_minutes = site_settings.jwt_expire_minutes
    token = create_access_token(subject=str(user.id), expires_minutes=expires_minutes)
    return TokenResponse(access_token=token, expires_in_minutes=expires_minutes)


@router.post("/change-password", response_model=UserOut, summary="Change current user password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")

    user.hashed_password = get_password_hash(payload.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user
