"""Sleeper representation for SleepIQ API."""
from __future__ import annotations

from .api import SleepIQAPI


class SleepIQSleeper:
    """Sleeper representation for SleepIQ API."""

    def __init__(
        self, api: SleepIQAPI, bed_id: str, sleeper_id: str, side: str
    ) -> None:
        """Initialize sleeper object."""
        self.api = api
        self.bed_id = bed_id
        self.sleeper_id = sleeper_id
        self.side = side[0]
        self.side_full = side
        self.active = False
        self.name = ""

        self.in_bed = False
        self.pressure = 0
        self.sleep_number = 0
        self.fav_sleep_number = 0

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQSleeper[{self.side}]({self.name}, in_bed={self.in_bed}, sn={self.sleep_number})"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQSleeper[{self.side}]({self.name}, in_bed={self.in_bed}, sn={self.sleep_number})"

    async def calibrate(self) -> None:
        """Calibrate or "baseline" bed."""
        await self.api.put("sleeper/" + self.sleeper_id + "/calibrate")

    async def set_sleepnumber(self, setting: int) -> None:
        """Set sleep number 5-100 (multiple of 5)."""
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting / 5)) * 5
        data = {"sleepNumber": setting, "side": self.side}
        await self.api.put("bed/" + self.bed_id + "/sleepNumber", data)

    async def set_favsleepnumber(self, setting: int) -> None:
        """Set favorite sleep number 5-100 (multiple of 5)."""
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting / 5)) * 5
        data = {"side": self.side, "sleepNumberFavorite": setting}
        await self.api.put("bed/" + self.bed_id + "/sleepNumberFavorite", data)
        await self.fetch_favsleepnumber()

    async def fetch_favsleepnumber(self) -> None:
        """Update fav_sleep_number from API."""
        json = await self.api.get("bed/" + self.bed_id + "/sleepNumberFavorite")
        self.fav_sleep_number = json["sleepNumberFavorite" + self.side_full]
