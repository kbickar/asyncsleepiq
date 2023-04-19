"""Bed object from SleepIQ API."""
from __future__ import annotations

from typing import Any

from ..api import SleepIQAPI
from ..consts import SIDES_FULL, Side
from ..foundation import SleepIQFoundation
from .foundation import SleepIQFuzionFoundation
from ..sleeper import SleepIQSleeper
from .sleeper import SleepIQFuzionSleeper
from ..bed import SleepIQBed


class SleepIQFuzionBed(SleepIQBed):
    """Fuzion Bed object from SleepIQ API."""

    def __init__(self, api: SleepIQAPI, data: dict[str, Any]) -> None:
        """Initialize bed object."""
        super().__init__(api, data)
        self.sleepers: list[SleepIQSleeper] = [
            SleepIQFuzionSleeper(api, self.id, data[f"sleeper{SIDES_FULL[side]}Id"], side)
            for side in [Side.LEFT, Side.RIGHT]
            if data.get(f"sleeper{SIDES_FULL[side]}Id")
        ]
        self.foundation: SleepIQFoundation = SleepIQFuzionFoundation(api, self.id)

    async def stop_pump(self) -> None:
        """Stop pump."""
        await self._api.bamkey(self.id, "InterruptSleepNumberAdjustment")

    async def fetch_pause_mode(self) -> None:
        """Update paused attribute with data from API."""
        status = await self._api.bamkey(self.id, "GetSleepiqPrivacyState")
        self.paused = status == "paused"

    async def set_pause_mode(self, mode: bool) -> None:
        """Set pause mode in API and locally."""
        arg = "paused" if mode else "active"
        await self._api.bamkey(self.id, "SetSleepiqPrivacyState", args=[arg])
        self.paused = mode
