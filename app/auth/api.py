from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.auth.schemas import (
    UserCreate, UserUpdate, UserResponse,
    LoginRequest, TokenResponse, ApiKeyResponse,
)
from app.auth.jwt import (
    hash_password, verify_password, create_access_token,
    generate_api_key, create_admin_user,
)
from app.auth.dependencies import require_admin, require_auth, get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.on_event("startup")
def bootstrap_admin():
    """Create default admin on first run."""
    create_admin_user()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive a JWT token."""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact an administrator.",
        )

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(require_auth)):
    """Get current authenticated user's profile."""
    return current_user


@router.post("/api-key", response_model=ApiKeyResponse)
def regenerate_api_key(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Generate or regenerate your API key."""
    current_user.api_key = generate_api_key()
    db.commit()
    return ApiKeyResponse(api_key=current_user.api_key)


# ── Admin-only user management ──

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: list all users."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: create a new user."""
    if db.query(User).filter(
        (User.username == body.username) | (User.email == body.email)
    ).first():
        raise HTTPException(409, "Username or email already exists")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin: update a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    update_data = body.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin: delete a user (cannot delete yourself)."""
    if current_user.id == user_id:
        raise HTTPException(400, "Cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()
