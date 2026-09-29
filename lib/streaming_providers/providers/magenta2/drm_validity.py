# streaming_providers/providers/magenta2/drm_validity.py
"""Magenta2 DRM-validity mixin: retire cached configs whose license token is spent."""

import time
import urllib.parse
from typing import List

from ...base.utils.logger import logger
from .token_utils import JWTParser

# The license server URL carries the entitlement JWT as a query parameter.
_TOKEN_QUERY_PARAM = "token"

# Treat a token that is seconds from expiring as already expired: the config is
# handed to Kodi first and only then used to fetch a license, so a token that
# survives the cache lookup but not the license request buys nothing.
_EXPIRY_MARGIN_SECONDS = 60


class Magenta2DrmValidityMixin:
    """Lets the DRM cache notice that a magenta2 license token has run out.

    theplatform mints one entitlement token per day: iat and exp fall on local
    midnight rather than being issued per request, so the token's remaining
    life shrinks as the day goes on while the cache TTL stays a fixed hour. A
    config resolved at 23:30 is therefore cached with a token that dies at
    00:00 and would be served until 00:30, and every license request made from
    it in that window is answered with HTTP 401.
    """

    def drm_configs_expired(self, drm_configs: List) -> bool:
        deadline = time.time() + _EXPIRY_MARGIN_SECONDS

        for config in drm_configs or []:
            license_config = getattr(config, "license", None)
            server_url = getattr(license_config, "server_url", None)
            if not server_url:
                continue

            query = urllib.parse.parse_qs(urllib.parse.urlparse(server_url).query)
            token = query.get(_TOKEN_QUERY_PARAM)
            if not token:
                continue

            # extract_raw_claims() rather than parse(): this is an entitlement
            # token, not a persona token, so the claim mapping in parse() finds
            # nothing to map and warns about it on every check.
            claims = JWTParser.extract_raw_claims(token[0]) or {}
            expiry = claims.get("exp")
            if expiry is None:
                # Not a JWT, or no exp claim: nothing to judge it by, so leave
                # the entry alone rather than discarding a config that may be
                # perfectly good.
                continue

            if float(expiry) <= deadline:
                remaining = float(expiry) - time.time()
                when = (
                    f"expired {-remaining:.0f}s ago" if remaining < 0
                    else f"expires in {remaining:.0f}s, inside the {_EXPIRY_MARGIN_SECONDS}s margin"
                )
                logger.info(
                    f"magenta2: license token for {getattr(config, 'system', '?')} {when}, "
                    f"discarding cached DRM config"
                )
                return True

        return False
