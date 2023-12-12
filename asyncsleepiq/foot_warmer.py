"""Foot warmer representation for SleepIQ API."""
from __future__ import annotations

from .api import SleepIQAPI
from .consts import (Side, FootWarmingTemps, SIDES_FULL)

class SleepIQFootWarmer:
    """Foot warmer representation for SleepIQ API."""

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side, timer: int, temperature: int) -> None:
        """Initialize foot warmer object."""
        self._api = api
        self.bed_id = bed_id
        self.side = side
        self.is_on = (temperature > 0)
        self.timer = timer
        self.temperature = temperature

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQFootWarmer[{self.side}]: {'On' if self.is_on else 'Off'}, {self.timer}, {FootWarmingTemps(self.temperature).name}"
    __repr__ = __str__

    async def turn_on(self, temperature: FootWarmingTemps, time: int)  -> None:
       """Turn on foot warmer through API."""
       await self.set_foot_warming(temperature, time)

    async def turn_off(self) -> None:
        """Turn off foot warmer through API."""
        # The API requires a valid time value even if we're turning the warmer off
        await self.set_foot_warming(FootWarmingTemps.OFF, 1)

    async def set_foot_warming(self, temperature: FootWarmingTemps, time: int) -> None:
        """Set foot warmer state through API."""
        if time <= 0 or time > 360:
            raise ValueError("Invalid Time, must be between 0 and 360")

        data = { self.time_key(): time, self.temp_key(): temperature.value}
        await self._api.put(f"bed/{self.bed_id}/foundation/footwarming", data)
        await self.update(data)

    async def update(self, data) -> None:
        # when reading the values the key is footWarmingStatus and when writing the values the key is footWarmingTemp so lookup both
        self.temperature = data.get(self.temp_key(True), data.get(self.temp_key()))
        self.is_on = self.temperature > 0
        self.timer = data.get(self.time_key(), self.timer) if self.is_on else 0

    def time_key(self):
        return 'footWarmingTimer' + SIDES_FULL[self.side]

    def temp_key(self, read = False):
        key = 'Status' if read else 'Temp'
        return f'footWarming{key}' + SIDES_FULL[self.side]
