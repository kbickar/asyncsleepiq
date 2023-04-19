"""Actuator representation for SleepIQ API."""
from __future__ import annotations

from typing import Any

from ..actuator import SleepIQActuator


class SleepIQFuzionActuator(SleepIQActuator):
    """Actuator representation for SleepIQ API."""

    async def set_position(self, position: int, slow_speed: bool = False) -> None:
        """Set the position of an actuator through the API."""
        if position < 0 or position > 100:
            raise ValueError("Invalid position, must be between 0 and 100")
        if position == self.position:
            return
        args = [self.side_full.lower(), self.actuator_full.lower(), str(position)]
        await self._api.bamkey(self.bed_id, "SetActuatorTargetPosition", args)

    async def update(self, data: dict[str, Any]) -> None:
        """Update the position of an actuator from the API."""
        args = [self.side_full.lower(), self.actuator_full.lower()]
        result = await self._api.bamkey(self.bed_id, "GetActuatorPosition", args)
        self.position = int(result)
