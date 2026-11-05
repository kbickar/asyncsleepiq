"""Verify that existing foundation requests and controls stay compatible."""
import asyncio
from unittest.mock import Mock, call

import pytest

from asyncsleepiq import FootWarmingTemps, Mode, SleepIQFoundation, Speed
from asyncsleepiq.api import SleepIQAPI
from asyncsleepiq.fuzion.foundation import SleepIQFuzionFoundation

SYSTEM_URL = "bed/test-bed/foundation/system"
STATUS_URL = "bed/test-bed/foundation/status"
OUTLET_URL = "bed/test-bed/foundation/outlet"
WARMER_URL = "bed/test-bed/foundation/footwarming"


def test_classic_foundation_refresh_without_massage():
    api = Mock(spec=SleepIQAPI)
    api.check.side_effect = lambda url, *, params=None: url == SYSTEM_URL or (
        url == OUTLET_URL and params == {"outletId": 1}
    )
    responses = {
        SYSTEM_URL: {"fsBedType": 0, "fsBoardFeatures": 1 << 3},
        OUTLET_URL: {"setting": 1},
        WARMER_URL: {
            "footWarmingStatusLeft": 31,
            "footWarmingTimerLeft": 20,
            "footWarmingStatusRight": 0,
            "footWarmingTimerRight": 0,
        },
        STATUS_URL: {
            "fsRightHeadPosition": "0a",
            "fsRightFootPosition": "05",
            "fsCurrentPositionPresetRight": 4,
        },
    }
    api.get.side_effect = lambda url, **kwargs: responses[url]
    foundation = SleepIQFoundation(api, "test-bed")

    async def refresh():
        await foundation.fetch_features()
        await foundation.init_features()
        await foundation.update_foundation_status()

    asyncio.run(refresh())
    assert api.check.await_args_list == [
        call(SYSTEM_URL),
        *(call(OUTLET_URL, params={"outletId": outlet}) for outlet in (1, 2, 3, 4)),
    ]
    assert api.get.await_args_list == [
        call(SYSTEM_URL),
        call(OUTLET_URL, params={"outletId": 1}),
        call(STATUS_URL),
        call(OUTLET_URL, params={"outletId": 1}),
        call(WARMER_URL),
        call(STATUS_URL),
    ]
    assert foundation.lights[0].is_on
    assert foundation.foot_warmers[0].temperature == FootWarmingTemps.LOW
    assert foundation.foot_warmers[0].timer == 20
    assert [actuator.position for actuator in foundation.actuators] == [10, 5]
    assert foundation.presets[0].preset == 4
    api.put.assert_not_awaited()


def test_fuzion_still_uses_bamkey_and_skips_classic_requests():
    api = Mock(spec=SleepIQAPI)
    api.bamkey.side_effect = lambda bed_id, key, args=None: (
        "dual " + " ".join(["no"] * 15) if key == "GetSystemConfiguration" else "0"
    )
    foundation = SleepIQFuzionFoundation(api, "test-bed")

    async def refresh():
        await foundation.fetch_features()
        await foundation.init_features()
        await foundation.update_foundation_status()
        await foundation.set_foundation_massage("R", Speed.LOW, Speed.HIGH)
        await foundation.stop_motion("R")

    asyncio.run(refresh())
    assert api.bamkey.await_args_list == [
        call("test-bed", "GetSystemConfiguration"),
        call("test-bed", "GetCurrentPreset", ["left"]),
        call("test-bed", "GetCurrentPreset", ["right"]),
        call("test-bed", "GetFootwarmingPresence", args=["left"]),
        call("test-bed", "GetFootwarmingPresence", args=["right"]),
        call("test-bed", "GetHeidiPresence", args=["left"]),
        call("test-bed", "GetClimatePresence", args=["left"]),
        call("test-bed", "GetHeidiPresence", args=["right"]),
        call("test-bed", "GetClimatePresence", args=["right"]),
        call("test-bed", "GetCurrentPreset", ["left"]),
        call("test-bed", "GetCurrentPreset", ["right"]),
        call("test-bed", "HaltAllActuators"),
    ]
    api.check.assert_not_awaited()
    api.get.assert_not_awaited()
    api.put.assert_not_awaited()


@pytest.mark.parametrize(
    ("args", "foot", "head", "timer", "mode"),
    [
        ((), Speed.LOW, Speed.HIGH, 0, Mode.OFF),
        ((30, Mode.WAVE), Speed.OFF, Speed.OFF, 30, Mode.WAVE),
    ],
)
def test_legacy_massage_control_preserves_put_payload(args, foot, head, timer, mode):
    api = Mock(spec=SleepIQAPI)
    foundation = SleepIQFoundation(api, "test-bed")
    asyncio.run(foundation.set_foundation_massage("R", Speed.LOW, Speed.HIGH, *args))
    api.put.assert_awaited_once_with(
        "bed/test-bed/foundation/adjustment",
        {
            "footMassageMotor": foot,
            "headMassageMotor": head,
            "massageTimer": timer,
            "massageWaveMode": mode,
            "side": "R",
        },
    )
    api.check.assert_not_awaited()
    api.get.assert_not_awaited()
