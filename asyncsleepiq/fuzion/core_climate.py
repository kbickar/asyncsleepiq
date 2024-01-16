"""Foundation for Core Climate for Fuzion SleepIQ API."""
from __future__ import annotations

from typing import Any

from ..api import SleepIQAPI

from ..core_climate import SleepIQCoreClimate

from ..consts import SIDES_FULL, CoreTemps, Side


class SleepIQFuzionCoreClimate(SleepIQCoreClimate):
    """
        CoreClimate (Also known as Heidi) representation for SleepIQ Fuzion API.
        Heidi is the name of the climate calls in the SleepIQ API.
        Controls heating and cooling.
    """

    async def set_mode(self, temperature: CoreTemps, time: int) -> None:
        """Set core climate state through API."""
        if time <= 0 or time > 360:
            raise ValueError("Invalid Time, must be between 0 and 360")

        args = [SIDES_FULL[self.side].lower(), temperature.name.lower(), str(time)]
        await self._api.bamkey(self.bed_id, "SetHeidiMode", args)
        await self.update({})

    async def update(self, data: dict[str, Any]) -> None:
        """Update the core climate data through the API."""
        args = [SIDES_FULL[self.side].lower()]
        self.preset = await self._api.bamkey(self.bed_id, "GetHeidiMode", args)

