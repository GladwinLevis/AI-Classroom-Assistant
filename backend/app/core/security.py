import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AuthException, PermissionDeniedException, ValidationException
from app.core.database import get_db
from app.core.redis import redis_manager
from app.models.user import User, UserRole

# Password context setup (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme config
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Common weak passwords list to prevent weak password usage
COMMON_PASSWORDS = {
    "password", "password123", "12345678", "123456789", "qwerty", "admin123", 
    "classroom", "assistant", "classroom123", "student123", "teacher123",
    "welcome123", "letmein123"
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks plain text password against database hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates bcrypt hash of password string."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> None:
    """
    Validates password strength criteria:
    - Minimum length of 8 characters
    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one digit
    - Must contain at least one special character
    - Must not be in the list of common/weak passwords
    """
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long.")
    
    if password.lower() in COMMON_PASSWORDS:
        raise ValidationException("Password is too common or weak. Please select a stronger password.")

    if not re.search(r"[A-Z]", password):
        raise ValidationException("Password must contain at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise ValidationException("Password must contain at least one lowercase letter.")

    if not re.search(r"\d", password):
        raise ValidationException("Password must contain at least one numeric digit.")

    if not re.search(r"[ !@#$%^&*()_+=\-\[\]{};':\",./<>?|\\`~]", password):
        raise ValidationException("Password must contain at least one special character.")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates signed JWT Access Token with unique JTI."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": jti
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates signed JWT Refresh Token with unique JTI."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": jti
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token.
    Raises AuthException on invalid signatures, expirations, or blacklist.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        jti = payload.get("jti")
        if jti and await redis_manager.is_token_blacklisted(jti):
            raise AuthException("Token has been blacklisted (logged out).")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthException("Token has expired. Please login again.")
    except JWTError as e:
        raise AuthException(f"Token is invalid or tampered: {str(e)}")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """
    FastAPI dependency yielding current user UUID from authentication token.
    """
    payload = await decode_token(token)
    
    # Ensure it's an access token
    if payload.get("type") != "access":
        raise AuthException("Invalid token type. Expected access token.")
        
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise AuthException("Token is missing user identifier.")
    try:
        return UUID(user_id)
    except ValueError:
        raise AuthException("Token contains invalid user identifier format.")


async def get_current_user(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency returning the current logged-in User profile from the DB.
    """
    # Fetch user along with roles
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .filter(User.id == current_user_id, User.is_deleted == False)
    )
    user = result.scalars().first()
    if not user:
        raise AuthException("User associated with this token does not exist.")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency ensuring the logged-in User is active.
    """
    if not current_user.is_active:
        raise PermissionDeniedException("User account is disabled.")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    FastAPI dependency ensuring the logged-in User is verified.
    """
    if not current_user.is_verified:
        raise PermissionDeniedException("Email verification is required to perform this action.")
    return current_user


class RoleChecker:
    """
    Role-based authentication verification helper.
    Ensures user belongs to one of the allowed roles.
    """
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # Check if the user has any of the allowed roles
        user_roles = [r.name for r in current_user.roles]
        
        # Check matching
        has_role = False
        for allowed_role in self.allowed_roles:
            if allowed_role.value in user_roles:
                has_role = True
                break
                
        if not has_role:
            raise PermissionDeniedException(
                f"Required role permission missing. Allowed roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user
