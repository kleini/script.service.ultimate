# streaming_providers/base/utils/jwt_utils.py
"""
Generic JWT utilities.

Only the parts that are the same for every JWT live here: decoding the payload
and reading standard claims. Provider-specific claim mapping stays with the
provider (e.g. magenta2's JWTParser).
"""

import base64
import json
from typing import Any, Dict, Optional

from .logger import logger


def decode_claims(jwt_token: str) -> Optional[Dict[str, Any]]:
    """
    Extract raw claims dictionary without mapping

    Args:
        jwt_token: JWT token string

    Returns:
        Dictionary of raw claims or None
    """
    try:
        parts = jwt_token.split(".")
        if len(parts) != 3:
            return None

        payload_b64 = parts[1]
        padding = len(payload_b64) % 4
        if padding:
            payload_b64 += "=" * (4 - padding)

        payload_json = base64.b64decode(payload_b64).decode("utf-8")
        return json.loads(payload_json)

    except Exception as e:
        logger.debug(f"Failed to extract raw JWT claims: {e}")
        return None


def get_expiry(jwt_token: str) -> Optional[float]:
    """
    Extract expiry from any JWT token

    Args:
        jwt_token: JWT token string

    Returns:
        Expiry as Unix timestamp or None
    """
    try:
        claims = decode_claims(jwt_token)
        if claims and "exp" in claims:
            return float(claims["exp"])
    except Exception as e:
        logger.debug(f"Failed to extract expiry from JWT: {e}")
    return None
