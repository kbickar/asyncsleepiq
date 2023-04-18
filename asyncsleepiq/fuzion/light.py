"""Light representation for SleepIQ API."""
from __future__ import annotations

from ..light import SleepIQLight


class SleepIQFuzionLight(SleepIQLight):
    """Light representation for SleepIQ API."""

    async def turn_on(self) -> None:
        """Turn on light through API."""
        await self.set_light(True)
        self.is_on = True

    async def turn_off(self) -> None:
        """Turn off light through API."""
        await self.set_light(False)
        self.is_on = False

    async def set_light(self, setting: bool) -> None:
        """Set light state through API."""
        arg = "high" if setting else "off"
        await self._api.bamkey(self.bed_id, "SetUnderbedLightSettings", args=[arg, "0"])

    async def update(self) -> None:
        """Update light state from API."""
        result = await self._api.bamkey(self.bed_id, "GetUnderbedLightSettings")
        state, num = result.split()
        self.is_on = state != "off"
