from hpes_sim.controller import (
    determine_control_command, 
    ControlCommand
)
from hpes_sim.state import OperatingMode


def test_surplus_power_requests_charging():
    command = determine_control_command(
        renewable_power_w=8_000_000.0,
        target_power_w=6_000_000.0,
    )

    assert command == ControlCommand(
        mode=OperatingMode.CHARGING,
        electrical_power_w=2_000_000.0,
    )


def test_power_deficit_requests_discharging():
    command = determine_control_command(
        renewable_power_w=4_000_000.0,
        target_power_w=6_000_000.0,
    )

    assert command == ControlCommand(
        mode=OperatingMode.DISCHARGING,
        electrical_power_w=2_000_000.0,
    )


def test_matching_power_requests_idle():
    command = determine_control_command(
        renewable_power_w=6_000_000.0,
        target_power_w=6_000_000.0,
    )

    assert command == ControlCommand(
        mode=OperatingMode.IDLE,
        electrical_power_w=0.0,
    )
