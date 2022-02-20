from .consts import ACTUATORS, ACTUATORS_FULL, SIDES, SIDES_FULL

class SleepIQActuator:
    def __init__(self, api, bed_id, side, actuator):
        self._api = api
        self.bed_id = bed_id
        self.side = SIDES[side] if side else None
        self.side_full = SIDES_FULL[side] if side else None
        self.actuator = ACTUATORS[actuator]
        self.actuator_full = ACTUATORS_FULL[actuator]
        self.position = 0

    def __str__(self):
        return f"SleepIQActuator[{self.actuator_full} {self.side_full}], position={self.position}"
    def __repr__(self):
        return f"SleepIQActuator[{self.actuator_full} {self.side_full}], position={self.position}"

    async def set_position(self, position, slowSpeed=False):
        if position < 0 or position > 100:
            raise ValueError("Invalid position, must be between 0 and 100")
        if position == self.position:
            return
        data = {"position": position, "side": self.side if self.side else "R", "actuator": self.actuator, "speed": 1 if slowSpeed else 0}
        await self._api.put(f"bed/{self.bed_id}/foundation/adjustment/micro", data)

    async def update(self, data):
        # For non-split actuators, it doesn't matter which side we get the
        # value from, it'll always be the same for either
        side_full = self.side_full if self.side_full else "Right"

        # The API reports position in hex, but is set with an integer.
        # We'll always show position with an integer value.
        self.position = int(data[f"fs{side_full}{self.actuator_full}Position"], 16)