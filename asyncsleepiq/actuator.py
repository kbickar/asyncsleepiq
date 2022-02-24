"""Actuator representation for SleepIQ API."""
from __future__ import annotations

from typing import Any

from .api import SleepIQAPI
from .consts import ACTUATORS, ACTUATORS_FULL, SIDES, SIDES_FULL


class SleepIQActuator:
    """Actuator representation for SleepIQ API."""

    def __init__(
        self, api: SleepIQAPI, bed_id: str, side: int | None, actuator: int
    ) -> None:
        """Initialize actuator object."""
        self._api = api
        self.bed_id = bed_id
        self.side = SIDES[side] if side else None
        self.side_full = SIDES_FULL[side] if side else None
        self.actuator = ACTUATORS[actuator]
        self.actuator_full = ACTUATORS_FULL[actuator]
        self.position = 0

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQActuator[{self.actuator_full} {self.side_full}], position={self.position}"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQActuator[{self.actuator_full} {self.side_full}], position={self.position}"

    async def set_position(self, position: int, slow_speed: bool = False) -> None:
        """Set the position of an actuator through the API."""
        if position < 0 or position > 100:
            raise ValueError("Invalid position, must be between 0 and 100")
        if position == self.position:
            return
        data = {
            "position": position,
            "side": self.side if self.side else "R",
            "actuator": self.actuator,
            "speed": 1 if slow_speed else 0,
        }
        await self._api.put(f"bed/{self.bed_id}/foundation/adjustment/micro", data)

    async def update(self, data: dict[str, Any]) -> None:
        """Update the position of an actuator from the API."""
        # For non-split actuators, it doesn't matter which side we get the
        # value from, it'll always be the same for either
        side_full = self.side_full if self.side_full else "Right"

        # The API reports position in hex, but is set with an integer.
        # We'll always show position with an integer value.
        self.position = int(data[f"fs{side_full}{self.actuator_full}Position"], 16)
