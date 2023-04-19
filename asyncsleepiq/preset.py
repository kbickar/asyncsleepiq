"""Foundation preset setting from SleepIQ API."""
from __future__ import annotations

from typing import Any
from .api import SleepIQAPI
from .consts import BED_PRESETS, NO_PRESET, SIDES_FULL, SIDES_SHORT, Side


class SleepIQPreset:
    """Foundation preset setting from SleepIQ API."""

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side) -> None:
        """Initialize preset setting."""
        self._api = api
        self.bed_id = bed_id
        self.side = side
        self.side_full = SIDES_FULL[side]
        self.preset = ""
        self.options = list(BED_PRESETS)

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQPreset[{self.side}](preset={self.preset})"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQPreset[{self.side}](preset={self.preset})"

    async def set_preset(self, preset: str, slow_speed: bool = False) -> None:
        """Set foundation preset."""
        #
        # preset 1-6
        # slowSpeed False=fast, True=slow
        #
        if preset == NO_PRESET:
            return
        if preset not in self.options:
            raise ValueError("Invalid preset")
        data = {"preset": BED_PRESETS[preset], "side": SIDES_SHORT[self.side], "speed": 1 if slow_speed else 0}
        await self._api.put("bed/" + self.bed_id + "/foundation/preset", data)

    async def update(self, data: dict[str, Any]) -> None:
        """Update the position of an actuator from the API."""
        self.preset = data[f"fsCurrentPositionPreset{self.side_full}"]
