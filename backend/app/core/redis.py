import logging
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages connections to Redis for blacklists, OTP codes, and rate limiting.
    Provides in-memory fallback for local development if Redis is offline.
    """
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client: Optional[aioredis.Redis] = None
        self._fallback_db = {}  # In-memory fallback dictionary
        self._is_online = False

    async def connect(self) -> None:
        """Initializes connection to the Redis server."""
        try:
            self._client = aioredis.from_url(self.redis_url, decode_responses=True)
            # Test connectivity
            await self._client.ping()
            self._is_online = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            self._is_online = False
            logger.warning(
                f"Could not connect to Redis at {self.redis_url}: {str(e)}. "
                "Falling back to local in-memory storage."
            )

    @property
    def client(self) -> aioredis.Redis:
        """Returns the Redis client. Connects if not already initialized."""
        if self._client is None and not self._is_online:
            # We can't await inside property, but connection check will handle it.
            pass
        return self._client

    async def _safe_run(self, func, *args, **kwargs):
        """Runs a Redis command. Falls back to in-memory db on failure."""
        if not self._is_online or self._client is None:
            return self._run_fallback(func.__name__, *args, **kwargs)
        try:
            return await func(*args, **kwargs)
        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            logger.error(f"Redis connection failed during {func.__name__}: {str(e)}. Using fallback database.")
            self._is_online = False
            return self._run_fallback(func.__name__, *args, **kwargs)

    def _run_fallback(self, command: str, *args, **kwargs):
        """Standard key-value fallback handlers simulating basic Redis actions."""
        # Simple local in-memory simulation
        import time
        now = time.time()
        
        # Cleanup expired items first
        expired_keys = [
            k for k, v in self._fallback_db.items() 
            if v.get("expires") is not None and v["expires"] < now
        ]
        for k in expired_keys:
            del self._fallback_db[k]

        if command in ("get", "get_otp"):
            key = args[0]
            val = self._fallback_db.get(key)
            return val["value"] if val else None

        elif command in ("set", "set_otp", "blacklist_token"):
            key = args[0]
            val = args[1]
            expire = kwargs.get("ex") or args[2] if len(args) > 2 else None
            self._fallback_db[key] = {
                "value": str(val),
                "expires": now + expire if expire else None
            }
            return True

        elif command == "delete":
            key = args[0]
            if key in self._fallback_db:
                del self._fallback_db[key]
                return 1
            return 0

        elif command == "exists":
            key = args[0]
            return 1 if key in self._fallback_db else 0

        elif command == "incrby":
            key = args[0]
            amount = args[1] if len(args) > 1 else 1
            val = self._fallback_db.get(key)
            new_val = int(val["value"]) + amount if val else amount
            self._fallback_db[key] = {
                "value": str(new_val),
                "expires": now + 900  # Default 15 minutes failure TTL
            }
            return new_val

        return None

    # Blacklist APIs
    async def blacklist_token(self, jti: str, ttl_seconds: int) -> None:
        """Blacklists an access token by JTI with remaining time-to-live."""
        key = f"blacklist:{jti}"
        logger.info(f"Blacklisting token {jti} for {ttl_seconds}s")
        if self._is_online and self.client:
            await self._safe_run(self.client.set, key, "true", ex=ttl_seconds)
        else:
            self._run_fallback("set", key, "true", ttl_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Checks if a JTI has been blacklisted."""
        key = f"blacklist:{jti}"
        if self._is_online and self.client:
            exists = await self._safe_run(self.client.exists, key)
            return bool(exists)
        else:
            return bool(self._run_fallback("exists", key))

    # OTP APIs
    async def set_otp(self, email: str, otp: str, expire_seconds: int = 300) -> None:
        """Stores OTP code in Redis under the user's email."""
        key = f"otp:{email}"
        if self._is_online and self.client:
            await self._safe_run(self.client.set, key, otp, ex=expire_seconds)
        else:
            self._run_fallback("set", key, otp, expire_seconds)

    async def get_otp(self, email: str) -> Optional[str]:
        """Fetches stored OTP code for verification."""
        key = f"otp:{email}"
        if self._is_online and self.client:
            return await self._safe_run(self.client.get, key)
        else:
            return self._run_fallback("get", key)

    async def delete_otp(self, email: str) -> None:
        """Deletes OTP code once verified."""
        key = f"otp:{email}"
        if self._is_online and self.client:
            await self._safe_run(self.client.delete, key)
        else:
            self._run_fallback("delete", key)

    # Brute-force & Lockout APIs
    async def increment_login_failures(self, email: str, expire_seconds: int = 900) -> int:
        """Increments failed login attempts for brute-force protection."""
        key = f"login_failures:{email}"
        if self._is_online and self.client:
            count = await self._safe_run(self.client.incrby, key, 1)
            # Ensure TTL is set on first failure
            if count == 1:
                await self._safe_run(self.client.expire, key, expire_seconds)
            return count
        else:
            return self._run_fallback("incrby", key, 1)

    async def reset_login_failures(self, email: str) -> None:
        """Resets login failures on successful authentication."""
        key = f"login_failures:{email}"
        lock_key = f"lockout:{email}"
        if self._is_online and self.client:
            await self._safe_run(self.client.delete, key)
            await self._safe_run(self.client.delete, lock_key)
        else:
            self._run_fallback("delete", key)
            self._run_fallback("delete", lock_key)

    async def lock_account(self, email: str, lock_seconds: int = 900) -> None:
        """Locks an account from logging in for a specific lockout period."""
        key = f"lockout:{email}"
        if self._is_online and self.client:
            await self._safe_run(self.client.set, key, "locked", ex=lock_seconds)
        else:
            self._run_fallback("set", key, "locked", lock_seconds)

    async def is_account_locked(self, email: str) -> bool:
        """Checks if user account is locked due to consecutive authentication failures."""
        key = f"lockout:{email}"
        if self._is_online and self.client:
            exists = await self._safe_run(self.client.exists, key)
            return bool(exists)
        else:
            return bool(self._run_fallback("exists", key))

    # General Cache APIs
    async def get_cache(self, key: str) -> Optional[str]:
        """Retrieves cached content."""
        if self._is_online and self.client:
            return await self._safe_run(self.client.get, key)
        else:
            return self._run_fallback("get", key)

    async def set_cache(self, key: str, value: str, expire_seconds: int = 3600) -> None:
        """Stores cached content with expiration."""
        if self._is_online and self.client:
            await self._safe_run(self.client.set, key, value, ex=expire_seconds)
        else:
            self._run_fallback("set", key, value, expire_seconds)

    async def delete_cache(self, key: str) -> None:
        """Deletes cached content."""
        if self._is_online and self.client:
            await self._safe_run(self.client.delete, key)
        else:
            self._run_fallback("delete", key)


# Global Redis manager instance
redis_manager = RedisManager()
