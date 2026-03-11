"""Sleeper representation for SleepIQ API."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .api import SleepIQAPI
from .consts import SIDES_FULL, SIDES_SHORT, Side


@dataclass
class SleepData:
    """Sleep data for a single night.

    Contains both aggregate averages and primary session values.
    The primary session is the longest session recorded for the night.
    Note: API field availability varies by bed model/firmware version.
    """
    # Session timing (from primary/longest session)
    start_date: str | None = None  # Session start timestamp (ISO 8601)
    end_date: str | None = None    # Session end timestamp (ISO 8601)

    # Duration
    duration: int | None = None       # Time in bed for primary session (seconds)
    session_count: int | None = None  # Total number of sleep sessions recorded

    # Sleep quality scores
    sleep_score: int | None = None  # SleepIQ score (0-100) - primary session

    # Vital signs (from primary session)
    heart_rate: int | None = None        # Heart rate (bpm)
    respiratory_rate: int | None = None  # Respiratory rate (breaths/min)
    hrv: int | None = None               # Heart rate variability (ms)

    # Sleep breakdown (seconds, from primary session)
    restful: int | None = None            # Time spent restful
    restless: int | None = None           # Time spent restless
    out_of_bed: int | None = None         # Time spent out of bed
    fall_asleep_period: int | None = None # Time to fall asleep


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

        Retrieves sleep metrics for the given date from the primary (longest)
        sleep session recorded that night.

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
            "includeSlices": "false",
        }

        data = await self.api.get("sleepData", params=params)

        if not data:
            return None

        sleep_data = SleepData()

        # Count total sessions across all days returned
        all_sessions = []
        for day in data.get("sleepData", []):
            all_sessions.extend(day.get("sessions", []))
        sleep_data.session_count = len(all_sessions) or None

        # Find the primary (longest) session
        primary_session = None
        for session in all_sessions:
            if session.get("longest"):
                primary_session = session
                break
        # Fallback: pick the session with the greatest totalSleepSessionTime
        if primary_session is None and all_sessions:
            primary_session = max(
                all_sessions,
                key=lambda s: s.get("totalSleepSessionTime", 0),
            )

        if primary_session:
            # Timing
            sleep_data.start_date = primary_session.get("startDate")
            sleep_data.end_date = primary_session.get("endDate")

            # Duration: use session-level inBed (time physically in bed, seconds).
            # Note: the top-level aggregate field is inBedTotal/inBedAvg, not inBed,
            # so data.get("inBed") always returns None — use the session field instead.
            sleep_data.duration = primary_session.get("inBed")

            # Sleep quality
            sleep_data.sleep_score = primary_session.get("sleepQuotient")

            # Vital signs
            hr = primary_session.get("avgHeartRate")
            sleep_data.heart_rate = hr if hr and hr > 0 else None
            sleep_data.respiratory_rate = primary_session.get("avgRespirationRate")
            sleep_data.hrv = primary_session.get("hrv")

            # Sleep breakdown
            sleep_data.restful = primary_session.get("restful")
            sleep_data.restless = primary_session.get("restless")
            sleep_data.out_of_bed = primary_session.get("outOfBed")
            fap = primary_session.get("fallAsleepPeriod")
            sleep_data.fall_asleep_period = fap if fap and fap >= 0 else None
        else:
            # No session data — fall back to top-level aggregates
            sleep_data.sleep_score = (
                data.get("avgSleepIQ") or data.get("sleepIQAvg")
            )
            sleep_data.heart_rate = (
                data.get("avgHeartRate") or data.get("heartRateAvg")
            )
            sleep_data.respiratory_rate = (
                data.get("avgRespirationRate") or data.get("respirationRateAvg")
            )
            sleep_data.duration = data.get("inBedTotal") or data.get("inBedAvg")

        return sleep_data

    async def fetch_sleep_data(self) -> None:
        """Fetch sleep data for the most recent night and store in sleeper.sleep_data.

        Updates the sleeper's sleep_data attribute with data from the most recent
        completed sleep session (yesterday).

        Updated fields in sleeper.sleep_data:
            start_date: Session start timestamp (ISO 8601)
            end_date: Session end timestamp (ISO 8601)
            duration: Time in bed for primary session (seconds)
            session_count: Total number of sessions recorded
            sleep_score: SleepIQ score (0-100)
            heart_rate: Heart rate (bpm)
            respiratory_rate: Respiratory rate (breaths/min)
            hrv: Heart rate variability (ms)
            restful: Time spent restful (seconds)
            restless: Time spent restless (seconds)
            out_of_bed: Time spent out of bed (seconds)
            fall_asleep_period: Time to fall asleep (seconds)
        """
        yesterday = datetime.now() - timedelta(days=1)
        sleep_data = await self.get_sleep_data(yesterday)

        if sleep_data:
            self.sleep_data = sleep_data
