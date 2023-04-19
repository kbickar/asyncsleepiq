"""Foundation preset setting from SleepIQ API."""
from __future__ import annotations

from typing import Any

from ..preset import SleepIQPreset
from ..api import SleepIQAPI
from ..consts import (
    NO_PRESET,
    PRESET_FAV,
    PRESET_READ,
    PRESET_TV,
    PRESET_FLAT,
    PRESET_ZERO_G,
    PRESET_SNORE,
    Side,
)

PRESET_VALS = {
    PRESET_FAV: "favorite",
    PRESET_READ: "read",
    PRESET_TV: "watch_tv",
    PRESET_FLAT: "flat",
    PRESET_ZERO_G: "zero_g",
    PRESET_SNORE: "snore",
}


class SleepIQFuzionPreset(SleepIQPreset):
    """Foundation preset setting from SleepIQ API."""

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side, options: list[str]) -> None:
        """Initialize preset setting."""
        super().__init__(api, bed_id, side)
        self.options = options

    async def set_preset(self, preset: str, slow_speed: bool = False) -> None:
        """Set foundation preset."""
        if preset == NO_PRESET:
            return
        if preset not in self.options:
            raise ValueError("Invalid preset")
        args = [self.side_full.lower(), PRESET_VALS[preset]]
        await self._api.bamkey(self.bed_id, "SetTargetPresetWithoutTimer", args)

    async def update(self, data: dict[str, Any]) -> None:
        """Update the position of an actuator from the API."""
        args = [self.side_full.lower()]
        self.preset = await self._api.bamkey(self.bed_id, "GetCurrentPreset", args)
