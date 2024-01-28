"""Foundation for Core Climate for SleepIQ API."""
from __future__ import annotations

from typing import Any

from .api import SleepIQAPI

from .consts import SIDES_FULL, CoreTemps, Side


class SleepIQCoreClimate:
    """
        CoreClimate representation for SleepIQ API.
        Controls heating and cooling.
    """

    max_core_climate_time = 600

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side, timer: int, temperature: int) -> None:
        """Initialize CoreClimate object."""
        self._api = api
        self.bed_id = bed_id
        self.side = side
        self.is_on = (temperature > 0)
        self.timer = timer
        self.temperature = temperature

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQCoreClimate[{self.side}]: {'On' if self.is_on else 'Off'}, {self.timer}, {CoreTemps(self.temperature).name}"
    __repr__ = __str__

    async def turn_on(self, temperature: CoreTemps, time: int)  -> None:
        """Turn on core climate mode through API."""
        await self.set_mode(temperature, time)

    async def turn_off(self) -> None:
        """Turn off core climate mode through API."""
        # The API requires a valid time value even if we're turning the climate off
        await self.set_mode(CoreTemps.OFF, 1)
