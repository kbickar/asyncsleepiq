"""Foundation object from SleepIQ API."""
from __future__ import annotations

from typing import Any

from .actuator import SleepIQActuator
from .api import SleepIQAPI
from .consts import (
    BED_LIGHTS,
    BED_PRESETS,
    FOUNDATION_TYPES,
    MASSAGE_MODE,
    MASSAGE_SPEED,
)
from .light import SleepIQLight


class SleepIQFoundation:
    """Foundation object from SleepIQ API."""

    def __init__(self, api: SleepIQAPI, bed_id: str) -> None:
        """Initialize foundation object."""
        self._api = api
        self.bed_id = bed_id
        self.lights: list[SleepIQLight] = []
        self.features: dict[str, Any] = {}
        self.type = ""
        self.actuators: list[SleepIQActuator] = []
        self.is_moving = False
        self.preset = ""

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)}, actuators: {len(self.actuators)})"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)}, actuators: {len(self.actuators)})"

    async def init_lights(self) -> None:
        """Initialize list of lights available on foundation."""
        for light in BED_LIGHTS:
            exists = await self._api.check(
                f"bed/{self.bed_id}/foundation/outlet", params={"outletId": light}
            )
            if exists:
                self.lights.append(SleepIQLight(self._api, self.bed_id, light))
        await self.update_lights()

    async def update_lights(self) -> None:
        """Update light states from API."""
        for light in self.lights:
            await light.update()

    async def init_actuators(self) -> None:
        """Initialize list of actuators available on foundation."""
        if not self.type:
            return
        data = await self._api.get(f"bed/{self.bed_id}/foundation/status")
        self.is_moving = data["fsIsMoving"]

        if self.type in ["single", "easternKing"]:
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, None, 0),
                SleepIQActuator(self._api, self.bed_id, None, 1),
            ]
        elif self.type == "splitHead":
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, 0, 0),
                SleepIQActuator(self._api, self.bed_id, 1, 0),
                SleepIQActuator(self._api, self.bed_id, None, 1),
            ]
        else:
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, 0, 0),
                SleepIQActuator(self._api, self.bed_id, 1, 0),
                SleepIQActuator(self._api, self.bed_id, 0, 1),
                SleepIQActuator(self._api, self.bed_id, 1, 1),
            ]

        for actuator in self.actuators:
            await actuator.update(data)

    async def update_actuators(self) -> None:
        """Update actuator states from API."""
        if not self.type:
            return
        data = await self._api.get(f"bed/{self.bed_id}/foundation/status")
        self.is_moving = data["fsIsMoving"]
        for actuator in self.actuators:
            await actuator.update(data)

    async def fetch_features(self) -> None:
        """Update list of features available for foundation from API."""
        have_foundation = await self._api.check(
            "bed/" + self.bed_id + "/foundation/system"
        )
        if not have_foundation:
            self.type = ""
            return

        fs = await self._api.get("bed/" + self.bed_id + "/foundation/system")
        features_flags = fs.get("fsBoardFeatures", 0)
        self.features["boardIsASingle"] = bool(features_flags & (1 << 0))
        self.features["hasMassageAndLight"] = bool(features_flags & (1 << 1))
        self.features["hasFootControl"] = bool(features_flags & (1 << 2))
        self.features["hasFootWarming"] = bool(features_flags & (1 << 3))
        self.features["hasUnderbedLight"] = bool(features_flags & (1 << 4))
        type_num = int(fs.get("fsBedType", -1))
        if type_num < 0 or type_num > len(FOUNDATION_TYPES) - 1:
            self.type = ""
        else:
            self.type = FOUNDATION_TYPES[type_num]

        self.features["leftUnderbedLightPMW"] = fs.get("fsLeftUnderbedLightPWM")
        self.features["rightUnderbedLightPMW"] = fs.get("fsRightUnderbedLightPWM")

        if "hasMassageAndLight" in self.features:
            self.features["hasUnderbedLight"] = True
        if "split" in self.type:
            self.features["boardIsASingle"] = False

    async def stop_motion(self, side: str) -> None:
        """Stop motion on L or R side of bed."""
        data = {"footMotion": 1, "headMotion": 1, "massageMotion": 1, "side": side}
        await self._api.put("bed/" + self.bed_id + "/foundation/motion", data)

    async def set_preset(
        self, side: str, preset: int, slow_speed: bool = False
    ) -> None:
        """Set foundation preset."""
        #
        # preset 1-6
        # slowSpeed False=fast, True=slow
        #
        if preset not in BED_PRESETS:
            raise ValueError("Invalid preset")

        data = {"preset": preset, "side": side, "speed": 1 if slow_speed else 0}
        await self._api.put("bed/" + self.bed_id + "/foundation/preset", data)

    async def set_foundation_massage(
        self, side: str, foot_speed: int, head_speed: int, timer: int = 0, mode: int = 0
    ) -> None:
        """Set massage mode."""
        #
        # foot_speed 0-3
        # head_speed 0-3
        # mode 0-3
        #
        if mode not in MASSAGE_MODE:
            raise ValueError("Invalid mode")
        if mode != 0:
            foot_speed = 0
            head_speed = 0
        if not all(speed in MASSAGE_SPEED for speed in (foot_speed, head_speed)):
            raise ValueError("Invalid head or foot speed")

        data = {
            "footMassageMotor": foot_speed,
            "headMassageMotor": head_speed,
            "massageTimer": timer,
            "massageWaveMode": mode,
            "side": side,
        }
        await self._api.put("bed/" + self.bed_id + "/foundation/adjustment", data)
