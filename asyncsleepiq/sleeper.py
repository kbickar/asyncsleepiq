"""Sleeper representation for SleepIQ API."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .api import SleepIQAPI
from .consts import SIDES_FULL, SIDES_SHORT, Side


@dataclass
class SleepData:
    """Sleep data for a single night.

    Contains both aggregate averages and most recent session values.
    Note: API field availability varies by bed model/firmware version.
    """
    # Duration
    duration: int | None = None  # Total time in bed (seconds)

    # Sleep quality scores
    sleep_score: int | None = None  # SleepIQ score (0-100) - aggregate or most recent

    # Vital signs
    heart_rate: int | None = None  # Heart rate (bpm) - aggregate or most recent
    respiratory_rate: int | None = None  # Respiratory rate (breaths/min) - aggregate or most recent
    hrv: int | None = None  # Heart rate variability (ms) - from most recent session


class SleepIQSleeper:
    """Sleeper representation for SleepIQ API."""

    def __init__(
        self, api: SleepIQAPI, bed_id: str, sleeper_id: str, side: Side
    ) -> None:
        """Initialize sleeper object."""
        self.api = api
        self.bed_id = bed_id
        self.sleeper_id = sleeper_id
        self.side = side
        self.side_full = SIDES_FULL[side]
        self.active = False
        self.name = ""

        self.in_bed = False
        self.pressure = 0
        self.sleep_number = 0
        self.fav_sleep_number = 0

        # Sleep health metrics
        self.sleep_data = SleepData()

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQSleeper[{self.side}]({self.name}, in_bed={self.in_bed}, sn={self.sleep_number})"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQSleeper[{self.side}]({self.name}, in_bed={self.in_bed}, sn={self.sleep_number})"
    
    async def update(self) -> None:
        """Updates sleeper with latest data."""
        pass

    async def calibrate(self) -> None:
        """Calibrate or "baseline" bed."""
        await self.api.put("sleeper/" + self.sleeper_id + "/calibrate")

    async def set_sleepnumber(self, setting: int) -> None:
        """Set sleep number 5-100 (multiple of 5)."""
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting / 5)) * 5
        data = {
            "sleepNumber": setting, 
            "side": SIDES_SHORT[self.side],
        }
        await self.api.put("bed/" + self.bed_id + "/sleepNumber", data)

    async def set_favsleepnumber(self, setting: int) -> None:
        """Set favorite sleep number 5-100 (multiple of 5)."""
        if 0 > setting or setting > 100:
            raise ValueError("Invalid SleepNumber, must be between 0 and 100")
        setting = int(round(setting / 5)) * 5
        data = {
            "side": SIDES_SHORT[self.side],
            "sleepNumberFavorite": setting,
        }
        await self.api.put("bed/" + self.bed_id + "/sleepNumberFavorite", data)
        await self.fetch_favsleepnumber()

    async def fetch_favsleepnumber(self) -> None:
        """Update fav_sleep_number from API."""
        json = await self.api.get("bed/" + self.bed_id + "/sleepNumberFavorite")
        self.fav_sleep_number = json["sleepNumberFavorite" + self.side_full]

    async def get_sleep_data(self, date: datetime) -> SleepData | None:
        """Get sleep health data for a specific date.

        Retrieves sleep metrics for the given date, using aggregate averages
        when available, falling back to most recent session values.

        Args:
            date: Date to fetch sleep data for.

        Returns:
            SleepData object with sleep metrics, or None if no data available.

        Note:
            The SleepIQ API is inconsistent across bed models/firmware versions.
            Field names vary (avgSleepIQ vs sleepIQAvg, etc.) and some fields like
            hrv may not be present in all responses.
        """
        date_str = date.strftime("%Y-%m-%dT%H:%M:%S")

        params = {
            "date": date_str,
            "interval": "D1",
            "sleeper": self.sleeper_id,
            "includeSlices": "true"
        }

        data = await self.api.get("sleepData", params=params)

        if not data:
            return None

        sleep_data = SleepData()

        # Get duration - totalSleepSessionTime is always 0, use inBed instead
        sleep_data.duration = data.get("inBed")

        # Get aggregate averages (handle API field name variations)
        # Some return avgSleepIQ, others sleepIQAvg, etc.
        avg_sleep_score = data.get("avgSleepIQ") or data.get("sleepIQAvg")
        avg_heart_rate = data.get("avgHeartRate") or data.get("heartRateAvg")
        avg_respiratory_rate = data.get("avgRespirationRate") or data.get("respirationRateAvg")

        # Try to get most recent session values for better accuracy
        recent_sleep_score = None
        recent_heart_rate = None
        recent_respiratory_rate = None
        recent_hrv = None

        if data.get("sleepData"):
            # Get the last day's data (most recent)
            last_day = data["sleepData"][-1]
            if last_day.get("sessions"):
                # Find the longest session (primary sleep session)
                for session in last_day["sessions"]:
                    if session.get("longest"):
                        recent_sleep_score = session.get("sleepQuotient")
                        recent_heart_rate = session.get("avgHeartRate")
                        recent_respiratory_rate = session.get("avgRespirationRate")
                        recent_hrv = session.get("hrv")
                        break

        # Prefer most recent session values, fall back to aggregates
        sleep_data.sleep_score = recent_sleep_score or avg_sleep_score
        sleep_data.heart_rate = recent_heart_rate or avg_heart_rate
        sleep_data.respiratory_rate = recent_respiratory_rate or avg_respiratory_rate
        sleep_data.hrv = recent_hrv

        return sleep_data

    async def fetch_sleep_data(self) -> None:
        """Fetch sleep data for the most recent night and store in sleeper.sleep_data.

        Updates the sleeper's sleep_data attribute with data from the most recent
        completed sleep session (last_night).

        Updates sleeper.sleep_data with:
            duration: Total time in bed (seconds)
            sleep_score: SleepIQ score (0-100)
            heart_rate: Heart rate (bpm)
            respiratory_rate: Respiratory rate (breaths/min)
            hrv: Heart rate variability (ms)
        """
        last_night = datetime.now()
        sleep_data = await self.get_sleep_data(last_night)

        if sleep_data:
            self.sleep_data = sleep_data
