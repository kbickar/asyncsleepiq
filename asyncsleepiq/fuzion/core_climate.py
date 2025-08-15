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

    max_core_climate_time = 600
    _set_mode_key = "SetHeidiMode"
    _get_mode_key = "GetHeidiMode"

    async def set_mode(self, temperature: CoreTemps, time: int) -> None:
        """Set core climate state through API."""
        if time <= 0 or time > self.max_core_climate_time:
            raise ValueError(f"Invalid Time, must be between 0 and {self.max_core_climate_time}")

        args = [SIDES_FULL[self.side].lower(), temperature.name.lower(), str(time)]
        await self._api.bamkey(self.bed_id, self._set_mode_key, args)
        await self.update({})

    async def update(self, data: dict[str, Any]) -> None:
        """Update the core climate data through the API."""
        args = [SIDES_FULL[self.side].lower()]
        data = await self._api.bamkey(self.bed_id, self._get_mode_key, args)
        data = data.split()
        self.temperature = CoreTemps[data[0].upper()]
        self.is_on = self.temperature > 0
        self.timer = int(data[1]) if self.is_on else 0


class SleepIQFuzionClimateCoolCoreClimate(SleepIQFuzionCoreClimate):
    """Core Climate representation for ClimateCool beds."""

    _set_mode_key = "SetClimateMode"
    _get_mode_key = "GetClimateMode"

