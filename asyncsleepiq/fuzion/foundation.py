"""Foundation object from SleepIQ API."""
from __future__ import annotations

from typing import Any

from ..consts import (
    NO_PRESET,
    PRESET_FAV,
    PRESET_FLAT,
    PRESET_READ,
    PRESET_SNORE,
    PRESET_TV,
    PRESET_ZERO_G,
    End,
    Mode,
    Side,
    Speed,
)
from ..foundation import SleepIQFoundation
from .preset import SleepIQFuzionPreset
from .actuator import SleepIQFuzionActuator
from .light import SleepIQFuzionLight

FEATURE_NAMES = [
    "bedType", # Not sure what best to call this, but there's one flag at the start of the list that's (from testing) always "dual".
    "pressureControlEnabledFlag",
    "articulationEnableFlag",
    "underbedLightEnableFlag",
    "rapidSleepSettingEnableFlag",
    "thermalControlEnabledFlag",
    "rightHeadActuator",
    "rightFootActuator",
    "leftHeadActuator",
    "leftFootActuator",
    "flatPreset",
    "favoritePreset",
    "snorePreset",
    "zeroGravityPreset",
    "watchTvPreset",
    "readPreset",
]


class SleepIQFuzionFoundation(SleepIQFoundation):
    """Foundation object from SleepIQ API."""

    async def init_features(self) -> None:
        """Initialize all foundation features."""
        if self.features["underbedLightEnableFlag"]:
            await self.init_lights()
        if self.features["articulationEnableFlag"]:
            await self.init_actuators()
        await self.init_presets({})

    async def update_foundation_status(self) -> None:
        """Update all foundation data from API."""
        await self.update_lights()
        await self.update_actuators({})
        await self.update_presets({})

    async def init_lights(self) -> None:
        """Initialize list of lights available on foundation."""
        self.lights.append(SleepIQFuzionLight(self._api, self.bed_id, 1))

    async def init_actuators(self) -> None:
        """Initialize list of actuators available on foundation."""
        if self.features["rightHeadActuator"]:
            self.actuators.append(SleepIQFuzionActuator(self._api, self.bed_id, Side.RIGHT, End.HEAD))
        if self.features["rightFootActuator"]:
            self.actuators.append(SleepIQFuzionActuator(self._api, self.bed_id, Side.RIGHT, End.FOOT))
        if self.features["leftHeadActuator"]:
            self.actuators.append(SleepIQFuzionActuator(self._api, self.bed_id, Side.LEFT, End.HEAD))
        if self.features["leftFootActuator"]:
            self.actuators.append(SleepIQFuzionActuator(self._api, self.bed_id, Side.LEFT, End.FOOT))

        await self.update_actuators([])

    async def init_presets(self, data: dict[str, Any]) -> None:
        """Initialize list of presets available on foundation."""
        options = [NO_PRESET]
        if self.features["flatPreset"]:
            options.append(PRESET_FLAT)
        if self.features["favoritePreset"]:
            options.append(PRESET_FAV)
        if self.features["snorePreset"]:
            options.append(PRESET_SNORE)
        if self.features["zeroGravityPreset"]:
            options.append(PRESET_ZERO_G)
        if self.features["watchTvPreset"]:
            options.append(PRESET_TV)
        if self.features["readPreset"]:
            options.append(PRESET_READ)

        if self.type in ["single", "easternKing"]:
            self.presets = [SleepIQFuzionPreset(self._api, self.bed_id, Side.NONE, options)]
        else:
            self.presets = [
                SleepIQFuzionPreset(self._api, self.bed_id, Side.LEFT, options),
                SleepIQFuzionPreset(self._api, self.bed_id, Side.RIGHT, options),
            ]

        await self.update_presets({})

    async def fetch_features(self) -> None:
        """Update list of features available for foundation from API."""
        vals = await self._api.bamkey(self.bed_id, "GetSystemConfiguration")
        for k, v in zip(FEATURE_NAMES, vals.split()):
            if v == "no":
                v = False
            elif v == "yes":
                v = True
            self.features[k] = v

    async def stop_motion(self, side: str) -> None:
        """Stop motion on L or R side of bed."""
        await self._api.bamkey(self.bed_id, "HaltAllActuators")

    async def set_foundation_massage(
        self, side: str, foot_speed: Speed, head_speed: Speed, timer: int = 0, mode: Mode = Mode.OFF
    ) -> None:
        """Set massage mode."""
        pass
