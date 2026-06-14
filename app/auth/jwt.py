import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from config.app import Settings


settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def generate_api_key() -> str:
    return f"tsq_{secrets.token_hex(32)}"


def create_admin_user():
    """Create default admin user if no users exist."""
    from app.database.connection import SessionLocal

    db = SessionLocal()
    try:
        from app.database.models import User

        if db.query(User).count() == 0:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True,
                api_key=generate_api_key(),
            )
            db.add(admin)
            db.commit()
            print("Default admin user created: admin / admin123")
            print(f"  API Key: {admin.api_key}")
    finally:
        db.close()
