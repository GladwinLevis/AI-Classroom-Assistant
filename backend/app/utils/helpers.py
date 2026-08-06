from datetime import datetime, timezone
import string
import random


def get_utc_now() -> datetime:
    """Helper to return standardized timezone aware UTC datetime."""
    return datetime.now(timezone.utc)


def generate_random_string(length: int = 16) -> str:
    """Generates a secure random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))
