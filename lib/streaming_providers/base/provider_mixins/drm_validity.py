"""Provider DRM-validity mixin: lets a provider retire its own cached DRM configs."""

from typing import List


class ProviderDrmValidityMixin:
    def drm_configs_expired(self, drm_configs: List) -> bool:
        """
        Report whether cached DRM configs have become unusable while still
        inside their cache entry's lifetime.

        The DRM config cache ages entries from the moment they were stored,
        but a license token carried inside a config expires at a wall-clock
        time the provider chose. The two clocks are unrelated, so a config
        stored shortly before its token runs out stays cached after it has
        become worthless, and every license request made from it is answered
        with HTTP 401 until the entry ages out.

        A provider that can read the expiry of its own token overrides this
        and returns True once the token is spent; the DRM pipeline then drops
        the entry and resolves again instead of handing out a dead config.

        Args:
            drm_configs: the configs currently held in the cache.

        Returns:
            True to discard the cache entry, False to keep it. Providers that
            cannot tell say nothing, which is the default.
        """
        return False
