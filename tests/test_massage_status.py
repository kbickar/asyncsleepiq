"""Tests for reading massageMotorStatus as motor bits."""
import asyncio
from unittest.mock import Mock

import pytest

from asyncsleepiq import SleepIQFoundation
from asyncsleepiq.api import SleepIQAPI


def _left_side(status):
    """Return the left side read from a response carrying the given status."""
    api = Mock(spec=SleepIQAPI)
    api.check.return_value = True
    api.get.return_value = {
        "leftSide": {
            "footMassageMotorSpeed": 0,
            "headMassageMotorSpeed": 0,
            "waveMode": 0,
            "massageTimer": 0,
            "massageMotorStatus": status,
        },
        "rightSide": {},
    }
    foundation = SleepIQFoundation(api, "test-bed")
    foundation.features["hasMassageAndLight"] = True
    asyncio.run(foundation.init_massages())
    return foundation.massages[0]


@pytest.mark.parametrize(
    ("status", "is_on"),
    [(0, False), (1, True), (2, True), (3, True), (4, False), (6, True), (None, False), ("2", False)],
)
def test_motor_status_bits_decide_is_on(status, is_on):
    assert _left_side(status).is_on is is_on
