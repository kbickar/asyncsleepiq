"""Tests for classic SleepIQ foundation massage state."""
import asyncio
from unittest.mock import Mock, call

import pytest

from asyncsleepiq import Mode, Side, SleepIQFoundation, SleepIQMassage, Speed
from asyncsleepiq.api import SleepIQAPI

MASSAGE_URL = "bed/test-bed/foundation/massage"
STATUS_URL = "bed/test-bed/foundation/status"


@pytest.fixture
def massage_response():
    """Return the two-side response recorded in issue #40."""
    return {
        "leftSide": {
            "footMassageMotorSpeed": 1,
            "headMassageMotorSpeed": 0,
            "waveMode": 0,
            "massageTimer": 12,
            "massageMotorStatus": 1,
        },
        "rightSide": {
            "footMassageMotorSpeed": 0,
            "headMassageMotorSpeed": 0,
            "waveMode": 1,
            "massageTimer": 57,
            "massageMotorStatus": 0,
        },
    }


def test_foundation_polls_both_sides_with_one_get_per_refresh(massage_response):
    api = Mock(spec=SleepIQAPI)
    api.check.side_effect = lambda url, **kwargs: url == MASSAGE_URL
    api.get.side_effect = {
        MASSAGE_URL: massage_response,
        STATUS_URL: {
            "fsRightHeadPosition": "00",
            "fsRightFootPosition": "00",
            "fsCurrentPositionPresetRight": 0,
        },
    }.__getitem__
    foundation = SleepIQFoundation(api, "test-bed")
    foundation.features["hasMassageAndLight"] = True
    foundation.type = "single"

    async def refresh():
        await foundation.init_features()
        assert api.get.await_args_list == [call(MASSAGE_URL), call(STATUS_URL)]
        left, right = foundation.massages
        assert isinstance(left, SleepIQMassage)
        assert left.side is Side.LEFT
        assert left.is_on is True
        assert left.foot_speed is Speed.LOW
        assert left.head_speed is Speed.OFF
        assert left.mode is Mode.OFF
        assert left.timer == 12
        assert right.side is Side.RIGHT
        assert right.is_on is False
        assert right.foot_speed is Speed.OFF
        assert right.head_speed is Speed.OFF
        assert right.mode is Mode.SOOTHE
        assert right.timer == 57
        assert str(left) == "SleepIQMassage[Left]: On, foot=LOW, head=OFF, mode=OFF, timer=12"
        assert repr(left) == str(left)

        massage_response["leftSide"]["massageTimer"] = 11
        massage_response["rightSide"]["headMassageMotorSpeed"] = 3
        await foundation.update_foundation_status()
        assert left.timer == 11
        assert right.head_speed is Speed.HIGH

    asyncio.run(refresh())
    assert api.check.await_args_list.count(call(MASSAGE_URL)) == 1
    assert api.get.await_args_list == [
        call(MASSAGE_URL),
        call(STATUS_URL),
        call(MASSAGE_URL),
        call(STATUS_URL),
    ]
    api.put.assert_not_awaited()


@pytest.mark.parametrize("value", [-1, 99, None])
def test_unexpected_enumeration_values_fall_back_to_off(massage_response, value):
    left = SleepIQMassage(Side.LEFT)
    massage_response["leftSide"].update(
        footMassageMotorSpeed=value, headMassageMotorSpeed=value, waveMode=value
    )
    asyncio.run(left.update(massage_response))
    assert left.foot_speed is Speed.OFF
    assert left.head_speed is Speed.OFF
    assert left.mode is Mode.OFF
    assert left.is_on is True
    assert left.timer == 12


@pytest.mark.parametrize("advertised", [False, True])
def test_unsupported_massage_is_not_polled(advertised):
    api = Mock(spec=SleepIQAPI)
    api.check.return_value = False
    foundation = SleepIQFoundation(api, "test-bed")
    foundation.features["hasMassageAndLight"] = advertised

    async def refresh():
        await foundation.init_features()
        await foundation.update_foundation_status()
        await foundation.update_foundation_status()

    asyncio.run(refresh())
    assert foundation.massages == []
    assert api.check.await_args_list.count(call(MASSAGE_URL)) == int(advertised)
    api.get.assert_not_awaited()
    api.put.assert_not_awaited()
