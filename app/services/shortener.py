import random
import string

from app.models.url import Url


def generate_short_code(length=6):
    """
    Generate a unique 6-character alphanumeric short code.
    Uses uppercase, lowercase letters and digits (62 possibilities per character).
    Checks database for uniqueness and retries up to 10 times if collision occurs.
    """
    chars = string.ascii_letters + string.digits
    max_attempts = 10

    for _ in range(max_attempts):
        code = "".join(random.choices(chars, k=length))
        if is_code_available(code):
            return code

    raise ValueError("Failed to generate unique short code after multiple attempts")


def is_code_available(short_code):
    """Check if a short code is available (not already used)."""
    return not Url.select().where(Url.short_code == short_code).exists()
