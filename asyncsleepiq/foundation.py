"""Foundation object from SleepIQ API."""
from __future__ import annotations

from typing import Any

from .actuator import SleepIQActuator
from .api import SleepIQAPI
from .consts import (
    BED_LIGHTS,
    FOUNDATION_TYPES,
    End,
    Mode,
    Side,
    Speed,
)
from .light import SleepIQLight
from .foot_warmer import SleepIQFootWarmer
from .preset import SleepIQPreset
from .core_climate import SleepIQCoreClimate


class SleepIQFoundation:
    """Foundation object from SleepIQ API."""

    def __init__(self, api: SleepIQAPI, bed_id: str) -> None:
        """Initialize foundation object."""
        self._api = api
        self.bed_id = bed_id
        self.lights: list[SleepIQLight] = []
        self.foot_warmers: list[SleepIQFootWarmer] = []
        self.core_climates: list[SleepIQCoreClimate] = []
        self.features: dict[str, bool] = {
            "boardIsASingle": False,
            "hasMassageAndLight": False,
            "hasFootControl": False,
            "hasFootWarming": False,
            "hasUnderbedLight": False,
            "leftUnderbedLightPMW": False,
            "rightUnderbedLightPMW": False,
        }
        self.type = ""
        self.actuators: list[SleepIQActuator] = []
        self.presets: list[SleepIQPreset] = []

    def __str__(self) -> str:
        """Return string representation."""
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)}, actuators: {len(self.actuators)}, presets: {len(self.presets)})"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SleepIQFoundation[{self.type}](lights: {len(self.lights)}, features: {len(self.features)}, actuators: {len(self.actuators)}, presets: {len(self.presets)})"

    async def init_features(self) -> None:
        """Initialize all foundation features."""
        await self.init_lights()
        await self.init_foot_warmers()

        if not self.type:
            return

        data = await self._api.get(f"bed/{self.bed_id}/foundation/status")
        await self.init_actuators(data)
        await self.init_presets(data)

    async def update_foundation_status(self) -> None:
        """Update all foundation data from API."""
        await self.update_lights()
        await self.update_foot_warmers()

        if not self.type:
            return

        data = await self._api.get(f"bed/{self.bed_id}/foundation/status")

        await self.update_actuators(data)
        await self.update_presets(data)

    async def init_foot_warmers(self) -> None:
        if not self.features["hasFootWarming"]:
            return

        for side in [Side.LEFT, Side.RIGHT]:
            self.foot_warmers.append(SleepIQFootWarmer(self._api, self.bed_id, side, 0, 0))

    async def update_foot_warmers(self) -> None:
        if not self.features["hasFootWarming"]:
            return

        data = await self._api.get(f"bed/{self.bed_id}/foundation/footwarming")
        for foot_warmer in self.foot_warmers:
            await foot_warmer.update(data)

    async def init_lights(self) -> None:
        """Initialize list of lights available on foundation."""
        for light in BED_LIGHTS:
            exists = await self._api.check(f"bed/{self.bed_id}/foundation/outlet", params={"outletId": light})
            if exists:
                self.lights.append(SleepIQLight(self._api, self.bed_id, light))
        await self.update_lights()

    async def update_lights(self) -> None:
        """Update light states from API."""
        for light in self.lights:
            await light.update()

    async def init_actuators(self, data: dict[str, Any]) -> None:
        """Initialize list of actuators available on foundation."""

        if self.type in ["single", "easternKing"]:
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, Side.NONE, End.HEAD),
                SleepIQActuator(self._api, self.bed_id, Side.NONE, End.FOOT),
            ]
            self.presets = [SleepIQPreset(self._api, self.bed_id, Side.NONE)]
        elif self.type == "splitHead":
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, Side.LEFT, End.HEAD),
                SleepIQActuator(self._api, self.bed_id, Side.RIGHT, End.HEAD),
                SleepIQActuator(self._api, self.bed_id, Side.NONE, End.FOOT),
            ]
        else:
            self.actuators = [
                SleepIQActuator(self._api, self.bed_id, Side.LEFT, End.HEAD),
                SleepIQActuator(self._api, self.bed_id, Side.RIGHT, End.HEAD),
                SleepIQActuator(self._api, self.bed_id, Side.LEFT, End.FOOT),
                SleepIQActuator(self._api, self.bed_id, Side.RIGHT, End.FOOT),
            ]

        await self.update_actuators(data)

    async def init_presets(self, data: dict[str, Any]) -> None:
        """Initialize list of presets available on foundation."""
        if self.type in ["single", "easternKing"]:
            self.presets = [SleepIQPreset(self._api, self.bed_id, Side.NONE)]
        else:
            self.presets = [
                SleepIQPreset(self._api, self.bed_id, Side.LEFT),
                SleepIQPreset(self._api, self.bed_id, Side.RIGHT),
            ]

        await self.update_presets(data)

    async def update_actuators(self, data: dict[str, Any]) -> None:
        """Update actuator states from API."""
        for actuator in self.actuators:
            await actuator.update(data)

    async def update_presets(self, data: dict[str, Any]) -> None:
        """Update actuator states from API."""
        for preset in self.presets:
            await preset.update(data)

    async def fetch_features(self) -> None:
        """Update list of features available for foundation from API."""
        have_foundation = await self._api.check("bed/" + self.bed_id + "/foundation/system")
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

        self.features["leftUnderbedLightPMW"] = bool(fs.get("fsLeftUnderbedLightPWM", False))
        self.features["rightUnderbedLightPMW"] = bool(fs.get("fsRightUnderbedLightPWM", False))

        if self.features["hasMassageAndLight"]:
            self.features["hasUnderbedLight"] = True
        if "split" in self.type:
            self.features["boardIsASingle"] = False

    async def stop_motion(self, side: str) -> None:
        """Stop motion on L or R side of bed."""
        data = {"footMotion": 1, "headMotion": 1, "massageMotion": 1, "side": side}
        await self._api.put("bed/" + self.bed_id + "/foundation/motion", data)

    async def set_foundation_massage(
        self, side: str, foot_speed: Speed, head_speed: Speed, timer: int = 0, mode: Mode = Mode.OFF
    ) -> None:
        """Set massage mode."""
        if mode != Mode.OFF:
            foot_speed = Speed.OFF
            head_speed = Speed.OFF

        data = {
            "footMassageMotor": foot_speed,
            "headMassageMotor": head_speed,
            "massageTimer": timer,
            "massageWaveMode": mode,
            "side": side,
        }
        await self._api.put("bed/" + self.bed_id + "/foundation/adjustment", data)
