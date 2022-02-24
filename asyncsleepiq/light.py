"""Light representation for SleepIQ API."""
from __future__ import annotations

from .api import SleepIQAPI


class SleepIQLight:
    """Light representation for SleepIQ API."""

    def __init__(self, api: SleepIQAPI, bed_id: str, outlet_id: int) -> None:
        """Initialize light object."""
        self._api = api
        self.bed_id = bed_id
        self.is_on = False
        self.outlet_id = outlet_id

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQLight[{self.outlet_id}]: {'On' if self.is_on else 'Off'}"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQLight[{self.outlet_id}]: {'On' if self.is_on else 'Off'}"

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
        data = {"outletId": self.outlet_id, "setting": 1 if setting else 0}
        await self._api.put(f"bed/{self.bed_id}/foundation/outlet", data)

    async def update(self) -> None:
        """Update light state from API."""
        params = {"outletId": self.outlet_id}
        status = await self._api.get(
            f"bed/{self.bed_id}/foundation/outlet", params=params
        )
        self.is_on = status["setting"] == 1
