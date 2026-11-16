"""Tests for classic SleepIQ foundation massage state."""
import asyncio
from unittest.mock import Mock, call

import pytest

from asyncsleepiq import Mode, Side, SleepIQFoundation, SleepIQMassage, Speed
from asyncsleepiq.api import SleepIQAPI

MASSAGE_URL = "bed/test-bed/foundation/massage"
STATUS_URL = "bed/test-bed/foundation/status"
ADJUST_URL = "bed/test-bed/foundation/adjustment"


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
    left = SleepIQMassage(Mock(spec=SleepIQAPI), "test-bed", Side.LEFT)
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


def _side(api, massage_response, side=Side.RIGHT):
    """Return one side read from the recorded response."""
    massage = SleepIQMassage(api, "test-bed", side)
    asyncio.run(massage.update(massage_response))
    return massage


def test_speed_write_sends_only_the_motor_fields_and_arms_a_timer(massage_response):
    api = Mock(spec=SleepIQAPI)
    massage_response["rightSide"]["massageTimer"] = 0
    right = _side(api, massage_response)
    assert right.mode is Mode.SOOTHE

    asyncio.run(right.set_speed(foot_speed=Speed.MEDIUM))

    api.put.assert_awaited_once_with(
        ADJUST_URL,
        {"footMassageMotor": Speed.MEDIUM, "headMassageMotor": Speed.OFF, "massageTimer": 60, "side": "R"},
    )
    assert right.foot_speed is Speed.MEDIUM
    assert right.head_speed is Speed.OFF
    assert right.timer == 60
    assert right.mode is Mode.OFF
    assert right.is_on is True


def test_speed_write_keeps_a_running_timer_and_the_other_motor(massage_response):
    api = Mock(spec=SleepIQAPI)
    left = _side(api, massage_response, Side.LEFT)

    asyncio.run(left.set_speed(head_speed=Speed.HIGH))

    api.put.assert_awaited_once_with(
        ADJUST_URL,
        {"footMassageMotor": Speed.LOW, "headMassageMotor": Speed.HIGH, "massageTimer": 12, "side": "L"},
    )
    assert (left.foot_speed, left.head_speed, left.timer) == (Speed.LOW, Speed.HIGH, 12)


def test_turn_off_stops_both_motors_and_clears_the_timer(massage_response):
    api = Mock(spec=SleepIQAPI)
    left = _side(api, massage_response, Side.LEFT)

    asyncio.run(left.turn_off())

    api.put.assert_awaited_once_with(
        ADJUST_URL,
        {"footMassageMotor": Speed.OFF, "headMassageMotor": Speed.OFF, "massageTimer": 0, "side": "L"},
    )
    assert (left.foot_speed, left.head_speed, left.timer, left.is_on) == (Speed.OFF, Speed.OFF, 0, False)


def test_timer_write_sends_only_the_timer(massage_response):
    api = Mock(spec=SleepIQAPI)
    left = _side(api, massage_response, Side.LEFT)

    asyncio.run(left.set_timer(30))

    api.put.assert_awaited_once_with(ADJUST_URL, {"massageTimer": 30, "side": "L"})
    assert left.timer == 30
    assert left.foot_speed is Speed.LOW


@pytest.mark.parametrize("timer", [-1, 61, 1.5, None])
def test_out_of_range_timer_is_refused_before_any_request(massage_response, timer):
    api = Mock(spec=SleepIQAPI)
    left = _side(api, massage_response, Side.LEFT)

    with pytest.raises(ValueError):
        asyncio.run(left.set_timer(timer))
    with pytest.raises(ValueError):
        asyncio.run(left.set_speed(Speed.LOW, timer=-1 if timer is None else timer))

    api.put.assert_not_awaited()
    assert left.timer == 12


def test_rejected_write_leaves_the_state_alone(massage_response):
    api = Mock(spec=SleepIQAPI)
    api.put.side_effect = RuntimeError("rejected")
    left = _side(api, massage_response, Side.LEFT)

    with pytest.raises(RuntimeError):
        asyncio.run(left.set_speed(Speed.HIGH, Speed.HIGH))

    assert (left.foot_speed, left.head_speed, left.timer) == (Speed.LOW, Speed.OFF, 12)


@pytest.mark.parametrize(
    ("args", "body", "foot", "head", "timer", "mode"),
    [
        (
            (),
            {"footMassageMotor": Speed.LOW, "headMassageMotor": Speed.HIGH, "massageTimer": 0,
             "massageWaveMode": Mode.OFF, "side": "R"},
            Speed.LOW, Speed.HIGH, 0, Mode.OFF,
        ),
        (
            (30, Mode.WAVE),
            {"massageWaveMode": Mode.WAVE, "massageTimer": 30, "side": "R"},
            Speed.OFF, Speed.OFF, 30, Mode.WAVE,
        ),
    ],
)
def test_legacy_massage_control_goes_through_the_side_object(massage_response, args, body, foot, head, timer, mode):
    api = Mock(spec=SleepIQAPI)
    api.check.return_value = True
    api.get.return_value = massage_response
    foundation = SleepIQFoundation(api, "test-bed")
    foundation.features["hasMassageAndLight"] = True

    async def control():
        await foundation.init_massages()
        await foundation.set_foundation_massage("R", Speed.LOW, Speed.HIGH, *args)

    asyncio.run(control())
    api.put.assert_awaited_once_with(ADJUST_URL, body)
    right = foundation.massages[1]
    assert (right.foot_speed, right.head_speed, right.timer, right.mode) == (foot, head, timer, mode)


def test_pattern_write_sends_the_mode_and_timer_without_speeds(massage_response):
    api = Mock(spec=SleepIQAPI)
    left = _side(api, massage_response, Side.LEFT)
    assert left.foot_speed is Speed.LOW

    asyncio.run(left.set_mode(Mode.REVITILIZE, 20))

    api.put.assert_awaited_once_with(
        ADJUST_URL, {"massageWaveMode": Mode.REVITILIZE, "massageTimer": 20, "side": "L"}
    )
    assert (left.mode, left.foot_speed, left.head_speed, left.timer, left.is_on) == (
        Mode.REVITILIZE, Speed.OFF, Speed.OFF, 20, True
    )


def test_pattern_write_without_a_timer_leaves_the_bed_timer_alone(massage_response):
    api = Mock(spec=SleepIQAPI)
    right = _side(api, massage_response)

    asyncio.run(right.set_mode(Mode.WAVE))

    api.put.assert_awaited_once_with(ADJUST_URL, {"massageWaveMode": Mode.WAVE, "side": "R"})
    assert (right.mode, right.timer) == (Mode.WAVE, 57)


def test_pattern_off_sends_only_the_mode(massage_response):
    api = Mock(spec=SleepIQAPI)
    right = _side(api, massage_response)

    asyncio.run(right.set_mode(Mode.OFF))

    api.put.assert_awaited_once_with(ADJUST_URL, {"massageWaveMode": Mode.OFF, "side": "R"})
    assert (right.mode, right.timer, right.is_on) == (Mode.OFF, 0, False)


def test_pattern_timer_out_of_range_is_refused_before_any_request(massage_response):
    api = Mock(spec=SleepIQAPI)
    right = _side(api, massage_response)

    with pytest.raises(ValueError):
        asyncio.run(right.set_mode(Mode.SOOTHE, 61))

    api.put.assert_not_awaited()
    assert right.mode is Mode.SOOTHE and right.timer == 57
