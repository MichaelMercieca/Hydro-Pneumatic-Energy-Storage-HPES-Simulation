import pytest
from hpes_sim.state import HPESState, OperatingMode
from dataclasses import FrozenInstanceError


def test_hpes_state_stores_dynamic_state():
    state = HPESState(
        time_s=10.0,
        gas_volume_m3=2000.0,
        gas_temperature_k=290.0,
    )

    assert state.time_s == 10.0
    assert state.gas_volume_m3 == 2000.0
    assert state.gas_temperature_k == 290.0


def test_operating_modes_are_distinct():
    assert OperatingMode.IDLE is not OperatingMode.CHARGING
    assert OperatingMode.CHARGING is not OperatingMode.DISCHARGING


def test_hpes_state_is_immutable():
    state = HPESState(
        time_s=0.0,
        gas_volume_m3=3000.0,
        gas_temperature_k=287.15,
    )

    with pytest.raises(FrozenInstanceError):
        state.time_s = 1.0

