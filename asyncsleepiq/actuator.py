"""Actuator representation for SleepIQ API."""
from __future__ import annotations

from typing import Any

from .api import SleepIQAPI
from .consts import ACTUATORS_FULL, SIDES_FULL, SIDES_SHORT, End, Side


class SleepIQActuator:
    """Actuator representation for SleepIQ API."""

    def __init__(
        self, api: SleepIQAPI, bed_id: str, side: Side, actuator: End
    ) -> None:
        """Initialize actuator object."""
        self._api = api
        self.bed_id = bed_id
        self.side = side
        self.side_full = SIDES_FULL[side]
        self.actuator = actuator
        self.actuator_full = ACTUATORS_FULL[actuator]
        self.position = 0

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQActuator[{self.actuator_full} {self.side}], position={self.position}"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQActuator[{self.actuator_full} {self.side}], position={self.position}"

    async def set_position(self, position: int, slow_speed: bool = False) -> None:
        """Set the position of an actuator through the API."""
        if position < 0 or position > 100:
            raise ValueError("Invalid position, must be between 0 and 100")
        if position == self.position:
            return
        data = {
            "position": position,
            "side": SIDES_SHORT[self.side],
            "actuator": self.actuator,
            "speed": 1 if slow_speed else 0,
        }
        await self._api.put(f"bed/{self.bed_id}/foundation/adjustment/micro", data)

    async def update(self, data: dict[str, Any]) -> None:
        """Update the position of an actuator from the API."""
        # The API reports position in hex, but is set with an integer.
        # We'll always show position with an integer value.
        self.position = int(data[f"fs{self.side_full}{self.actuator_full}Position"], 16)
