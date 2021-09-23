from datetime import timedelta
from typing import Any, Dict, Optional

from jose import jwt

from app.config import HASHING_ALGORITHM, settings


def create_access_token_without_exp(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,  # pylint: disable=unused-argument
) -> str:
    return jwt.encode(data, settings.secret_key, algorithm=HASHING_ALGORITHM)
