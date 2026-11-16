"""Massage state and control from the SleepIQ API."""
from __future__ import annotations

from typing import Any

from .api import SleepIQAPI
from .consts import SIDES_FULL, Mode, Side, Speed

def _speed(value: Any) -> Speed:
    try:
        return Speed(value)
    except ValueError:
        return Speed.OFF


def _mode(value: Any) -> Mode:
    try:
        return Mode(value)
    except ValueError:
        return Mode.OFF


class SleepIQMassage:
    """Massage state and control for one side of a bed."""

    max_massage_time = 60

    def __init__(self, api: SleepIQAPI, bed_id: str, side: Side) -> None:
        """Initialize the massage state."""
        self._api = api
        self.bed_id = bed_id
        self.side = side
        self.is_on = False
        self.foot_speed = Speed.OFF
        self.head_speed = Speed.OFF
        self.mode = Mode.OFF
        self.timer = 0

    def __str__(self) -> str:
        """Return the current massage state for debugging."""
        return (f"SleepIQMassage[{SIDES_FULL[self.side]}]: "
                f"{'On' if self.is_on else 'Off'}, foot={self.foot_speed.name}, "
                f"head={self.head_speed.name}, mode={self.mode.name}, timer={self.timer}")

    __repr__ = __str__

    async def update(self, data: dict[str, Any]) -> None:
        """Read this side's state and remaining minutes from the bed response."""
        side_data = data.get(f"{SIDES_FULL[self.side].lower()}Side")
        if not isinstance(side_data, dict):
            return

        # massageMotorStatus is a bit field: 1 head motor, 2 foot motor (both
        # while a pattern runs), 4 the cool-down after a long run.
        status = side_data.get("massageMotorStatus")
        self.is_on = type(status) is int and status & 3 != 0
        self.foot_speed = _speed(side_data.get("footMassageMotorSpeed"))
        self.head_speed = _speed(side_data.get("headMassageMotorSpeed"))
        self.mode = _mode(side_data.get("waveMode"))
        timer = side_data.get("massageTimer")
        self.timer = timer if type(timer) is int and timer >= 0 else 0

    async def set_speed(
        self,
        foot_speed: Speed | None = None,
        head_speed: Speed | None = None,
        timer: int | None = None,
    ) -> None:
        """Set the foot and head motor speeds through the API.

        A speed left as None keeps its current value. Without a timer, a
        running motor gets the current timer or the 60 minute maximum, since
        the bed clears an unused timer and nothing else would stop the motor.
        """
        foot = self.foot_speed if foot_speed is None else foot_speed
        head = self.head_speed if head_speed is None else head_speed
        running = foot != Speed.OFF or head != Speed.OFF
        if timer is None:
            timer = (self.timer or self.max_massage_time) if running else 0
        self._check_timer(timer)

        await self._adjust(
            {"footMassageMotor": foot, "headMassageMotor": head, "massageTimer": timer}
        )
        self.foot_speed = foot
        self.head_speed = head
        self.timer = timer
        if running:
            self.mode = Mode.OFF
        self.is_on = running or self.mode != Mode.OFF

    async def set_timer(self, timer: int) -> None:
        """Set the minutes left on this side's massage through the API."""
        self._check_timer(timer)
        await self._adjust({"massageTimer": timer})
        self.timer = timer

    async def set_mode(self, mode: Mode, timer: int | None = None) -> None:
        """Start a Full Body pattern, or stop it with Mode.OFF, through the API.

        The request carries the mode and, when given, the timer, and never the
        motor speeds: a request that also sends both speeds as OFF stops the
        pattern it starts. Without a timer the bed keeps a running pattern's
        timer, and a pattern started from idle runs until the bed's own limit.
        """
        if mode == Mode.OFF:
            await self._adjust({"massageWaveMode": mode})
            self.mode = mode
            self.timer = 0
            self.is_on = self.foot_speed != Speed.OFF or self.head_speed != Speed.OFF
            return

        data: dict[str, Any] = {"massageWaveMode": mode}
        if timer is not None:
            self._check_timer(timer)
            data["massageTimer"] = timer
        await self._adjust(data)
        self.mode = mode
        self.foot_speed = Speed.OFF
        self.head_speed = Speed.OFF
        if timer is not None:
            self.timer = timer
        self.is_on = True

    async def turn_off(self) -> None:
        """Stop both motors through the API."""
        await self.set_speed(Speed.OFF, Speed.OFF, 0)

    async def set_massage(
        self, foot_speed: Speed, head_speed: Speed, timer: int = 0, mode: Mode = Mode.OFF
    ) -> None:
        """Set speeds, timer and mode, as SleepIQFoundation.set_foundation_massage does.

        A mode other than OFF starts that pattern through set_mode and ignores
        the speeds. Otherwise this sends the request set_foundation_massage has
        always sent.
        """
        if mode != Mode.OFF:
            await self.set_mode(mode, timer)
            return

        await self._adjust(
            {
                "footMassageMotor": foot_speed,
                "headMassageMotor": head_speed,
                "massageTimer": timer,
                "massageWaveMode": mode,
            }
        )
        self.foot_speed = foot_speed
        self.head_speed = head_speed
        self.timer = timer
        self.mode = mode
        self.is_on = foot_speed != Speed.OFF or head_speed != Speed.OFF

    async def _adjust(self, data: dict[str, Any]) -> None:
        """Send a partial adjustment for this side, as the SleepIQ app does."""
        await self._api.put(
            f"bed/{self.bed_id}/foundation/adjustment", {**data, "side": self.side.value}
        )

    def _check_timer(self, timer: int) -> None:
        if type(timer) is not int or timer < 0 or timer > self.max_massage_time:
            raise ValueError(f"Invalid Time, must be between 0 and {self.max_massage_time}")
