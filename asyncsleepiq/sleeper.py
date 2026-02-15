"""Sleeper representation for SleepIQ API."""
from __future__ import annotations

from .api import SleepIQAPI
from .consts import SIDES_FULL, SIDES_SHORT, Side


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

        # Sleep health metrics - aggregate averages across all sessions
        self.sleep_duration: int | None = None  # Total time in bed (seconds)
        self.sleep_score: int | None = None  # Average SleepIQ score (0-100)
        self.heart_rate: int | None = None  # Average heart rate (bpm)
        self.respiratory_rate: int | None = None  # Average respiratory rate (breaths/min)

        # Most recent session values (from last sleep session)
        self.sleep_score_recent: int | None = None  # Most recent session's SleepIQ score
        self.heart_rate_recent: int | None = None  # Most recent session's heart rate (bpm)
        self.respiratory_rate_recent: int | None = None  # Most recent session's respiratory rate (breaths/min)
        self.hrv: int | None = None  # Heart rate variability (ms) - may not be available for all beds

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

    async def fetch_sleep_data(self, date: str | None = None) -> None:
        """Fetch sleep health data for this sleeper.

        Retrieves sleep metrics including duration, aggregate averages across all sessions,
        and most recent session values for a specific date.

        Args:
            date: Date string in format "YYYY-MM-DDTHH:MM:SS".
                  If None, fetches data for yesterday (the most recent completed sleep session).

        Updates (Aggregate Averages):
            sleep_duration: Total time in bed across all sessions (seconds)
            sleep_score: Average SleepIQ score across all sessions (0-100)
            heart_rate: Average heart rate across all sessions (bpm)
            respiratory_rate: Average respiratory rate across all sessions (breaths/min)

        Updates (Most Recent Session):
            sleep_score_recent: SleepIQ score from most recent/longest session (0-100)
            heart_rate_recent: Heart rate from most recent/longest session (bpm)
            respiratory_rate_recent: Respiratory rate from most recent/longest session (breaths/min)
            hrv: Heart rate variability from most recent/longest session (ms)

        Note:
            The SleepIQ API is inconsistent across bed models/firmware versions.
            Field names vary (avgSleepIQ vs sleepIQAvg, etc.) and some fields like
            hrv may not be present in all responses.
        """
        if date is None:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")

        params = {
            "date": date,
            "interval": "D1",
            "sleeper": self.sleeper_id,
            "includeSlices": "true"
        }

        data = await self.api.get("sleepData", params=params)

        if data:
            # NOTE: totalSleepSessionTime is always 0, use inBed instead for duration
            self.sleep_duration = data.get("inBed")

            # Handle API field name variations across bed models/firmware
            # Some return avgSleepIQ, others sleepIQAvg, etc.
            self.sleep_score = data.get("avgSleepIQ") or data.get("sleepIQAvg")
            self.heart_rate = data.get("avgHeartRate") or data.get("heartRateAvg")
            self.respiratory_rate = data.get("avgRespirationRate") or data.get("respirationRateAvg")

            # Extract most recent session values
            if data.get("sleepData") and len(data["sleepData"]) > 0:
                # Get the last day's data (most recent)
                last_day = data["sleepData"][-1]
                if last_day.get("sessions") and len(last_day["sessions"]) > 0:
                    # Find the longest session (primary sleep session)
                    longest_session = None
                    for session in last_day["sessions"]:
                        if session.get("longest"):
                            longest_session = session
                            break

                    if longest_session:
                        # sleepQuotient is the session-level SleepIQ score
                        self.sleep_score_recent = longest_session.get("sleepQuotient")
                        self.heart_rate_recent = longest_session.get("avgHeartRate")
                        self.respiratory_rate_recent = longest_session.get("avgRespirationRate")
                        self.hrv = longest_session.get("hrv")
