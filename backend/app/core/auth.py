import hashlib, hmac, secrets
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, AuthSession

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}:{digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, digest_hex = encoded.split(":", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False

def create_session(user: User, db: Session) -> str:
    token = secrets.token_urlsafe(48)
    db.add(AuthSession(token=token, user_id=user.id)); db.commit()
    return token

def current_user(x_user_token: str | None = Header(default=None, alias="X-User-Token"), db: Session = Depends(get_db)) -> User:
    if not x_user_token:
        raise HTTPException(401, "Authentication required")
    session = db.query(AuthSession).filter(AuthSession.token == x_user_token).first()
    if not session:
        raise HTTPException(401, "Invalid or expired session")
    return session.user

def require_role(role: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(403, f"{role.title()} access required")
        return user
    return dependency
