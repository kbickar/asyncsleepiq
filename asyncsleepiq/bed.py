"""Bed object from SleepIQ API."""
from __future__ import annotations

from typing import Any

from .api import SleepIQAPI
from .consts import SIDES_FULL
from .foundation import SleepIQFoundation
from .sleeper import SleepIQSleeper


class SleepIQBed:
    """Bed object from SleepIQ API."""

    def __init__(self, api: SleepIQAPI, data: dict[str, Any]) -> None:
        """Initialize bed object."""
        self._api = api

        self.name = data["name"]
        self.id = data["bedId"]
        self.mac_addr = data["macAddress"]
        self.paused = False
        self.sleepers = [
            SleepIQSleeper(api, self.id, data[f"sleeper{side}Id"], side)
            for side in SIDES_FULL
            if data.get(f"sleeper{side}Id")
        ]
        self.foundation = SleepIQFoundation(api, self.id)

        self.model = "Unknown"
        if "model" in data:
            self.model = data["model"]
        elif "components" in data:
            for comp in data["components"]:
                if comp["base"] == "BASE":
                    self.model = comp["model"]
                    break

    def __str__(self) -> str:
        """Return string representation."""
        return (
            f"SleepIQBed({self.name}, model={self.model}, id={self.id}) "
            + str(self.sleepers)
            + " "
            + str(self.foundation)
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SleepIQBed({self.name}, model={self.model}, id={self.id}) "
            + str(self.sleepers)
            + " "
            + str(self.foundation)
        )

    async def calibrate(self) -> None:
        """Calibrate or "baseline" bed."""
        for sleeper in self.sleepers:
            if sleeper.sleeper_id:
                await sleeper.calibrate()
                break

    async def stop_pump(self) -> None:
        """Stop pump."""
        await self._api.put("bed/" + self.id + "/pump/forceIdle")

    async def fetch_pause_mode(self) -> None:
        """Update paused attribute with data from API."""
        json = await self._api.get("bed/" + self.id + "/pauseMode")
        self.paused = json.get("pauseMode", "") == "on"

    async def set_pause_mode(self, mode: bool) -> None:
        """Set pause mode in API and locally."""
        params = {"mode": "on" if mode else "off"}
        await self._api.put("bed/" + self.id + "/pauseMode", params=params)
        self.paused = mode
