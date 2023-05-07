"""Sleeper representation for SleepIQ API."""
from __future__ import annotations

from ..consts import SIDES_FULL
from ..sleeper import SleepIQSleeper


class SleepIQFuzionSleeper(SleepIQSleeper):
    """Sleeper representation for SleepIQ API."""

    async def update(self) -> None:
        """Updates sleeper with latest data."""
        await self.fetch_sleepnumber()

    async def set_sleepnumber(self, setting: int) -> None:
        """Set sleep number 5-100 (multiple of 5)."""
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting / 5)) * 5
        args = [SIDES_FULL[self.side].lower(), str(setting)]
        await self.api.bamkey(self.bed_id, "StartSleepNumberAdjustment", args=args)

    async def fetch_sleepnumber(self) -> None:
        """Update fav_sleep_number from API."""
        args = [SIDES_FULL[self.side].lower()]
        result = await self.api.bamkey(self.bed_id, "GetSleepNumberControls", args=args)
        is_updating, ambient_number, user_number = result.split()
        self.sleep_number = int(user_number)

    async def set_favsleepnumber(self, setting: int) -> None:
        """Set favorite sleep number 5-100 (multiple of 5)."""
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting / 5)) * 5
        args = [SIDES_FULL[self.side].lower(), str(setting)]
        await self.api.bamkey(self.bed_id, "SetFavoriteSleepNumber", args=args)
        await self.fetch_favsleepnumber()

    async def fetch_favsleepnumber(self) -> None:
        """Update fav_sleep_number from API."""
        args = [SIDES_FULL[self.side].lower()]
        result = await self.api.bamkey(self.bed_id, "GetFavoriteSleepNumber", args=args)
        self.fav_sleep_number = int(result)
