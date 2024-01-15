"""Foundation for Heidi for Fuzion SleepIQ API."""
from __future__ import annotations

from typing import Any

from ..api import SleepIQAPI

from ..consts import SIDES_FULL, HeidiTemps, Side


class SleepIQFuzionHeidi:
    """
        Heidi representation for SleepIQ Fuzion API.
        Heidi is the name of the Climate360 Climate calls in the SleepIQ API.
        Controls heating and cooling.
    """

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side, timer: int, temperature: int) -> None:
        """Initialize heidi object."""
        self._api = api
        self.bed_id = bed_id
        self.side = side
        self.is_on = (temperature > 0)
        self.timer = timer
        self.temperature = temperature


    async def set_heidi_mode(self, temperature: HeidiTemps, time: int) -> None:
        """Set heidi state through API."""
        if time <= 0 or time > 360:
            raise ValueError("Invalid Time, must be between 0 and 360")

        args = [SIDES_FULL[self.side].lower(), temperature.name.lower(), str(time)]
        await self._api.bamkey(self.bed_id, "SetHeidiMode", args)
        await self.update({})

    async def update(self, data: dict[str, Any]) -> None:
        """Update the heidi data through the API."""
        args = [SIDES_FULL[self.side].lower()]
        self.preset = await self._api.bamkey(self.bed_id, "GetHeidiMode", args)

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQHeidi[{self.side}]: {'On' if self.is_on else 'Off'}, {self.timer}, {HeidiTemps(self.temperature).name}"
    __repr__ = __str__

    async def turn_on(self, temperature: HeidiTemps, time: int)  -> None:
        """Turn on heidi mode through API."""
        await self.set_heidi_mode(temperature, time)

    async def turn_off(self) -> None:
        """Turn off heidi mode through API."""
        # The API requires a valid time value even if we're turning the warmer off
        await self.set_heidi_mode(HeidiTemps.OFF, 1)

    def time_key(self):
        return 'heidiTimer' + SIDES_FULL[self.side]

    def temp_key(self, read = False):
        key = 'Status' if read else 'Temp'
        return f'heidi{key}' + SIDES_FULL[self.side]
