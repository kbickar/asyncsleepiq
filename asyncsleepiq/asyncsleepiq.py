"""AsyncSleepIQ class connects to the SleepIQ API and provides bed information."""
from __future__ import annotations

from aiohttp import ClientSession

from .api import SleepIQAPI
from .bed import SleepIQBed
from .consts import LOGIN_KEY


class AsyncSleepIQ(SleepIQAPI):
    """Representation of SleepIQ API object."""

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        login_method: int = LOGIN_KEY,
        client_session: ClientSession | None = None,
    ) -> None:
        """Initialize AsyncSleepIQ."""
        super().__init__(email, password, login_method, client_session)
        self.beds: dict[str, SleepIQBed] = {}

    # initialize beds and sleepers from API
    async def init_beds(self) -> None:
        """Initialize bed and sleeper objects from API data."""
        data = await self.get("bed")

        # get beds
        self.beds = {bed["bedId"]: SleepIQBed(self, bed) for bed in data["beds"]}

        # get sleepers and assign to beds
        data = await self.get("sleeper")
        for sleeper_data in data["sleepers"]:
            if sleeper_data["bedId"] not in self.beds:
                continue
            sleeper = self.beds[sleeper_data["bedId"]].sleepers[sleeper_data["side"]]
            sleeper.name = sleeper_data["firstName"]
            sleeper.active = sleeper_data["active"]

        # init foundations
        for bed in self.beds.values():
            await bed.foundation.fetch_features()
            await bed.foundation.init_features()

    # update statuses of sleepers/beds
    async def fetch_bed_statuses(self) -> None:
        """Update bed/sleeper statuses from API."""
        data = await self.get("bed/familyStatus")
        for bed_status in data["beds"]:
            if bed_status["bedId"] not in self.beds:
                continue
            for sleeper in self.beds[bed_status["bedId"]].sleepers:
                sleeper_data = bed_status.get(sleeper.side_full.lower() + "Side")
                if sleeper_data:
                    sleeper.in_bed = sleeper_data["isInBed"]
                    sleeper.pressure = sleeper_data["pressure"]
                    sleeper.sleep_number = sleeper_data["sleepNumber"]
