"""Control logic for HPES operation."""

from dataclasses import dataclass

from hpes_sim.state import OperatingMode


@dataclass(frozen=True)
class ControlCommand:
    mode: OperatingMode
    electrical_power_w: float


def determine_control_command(
    renewable_power_w: float,
    target_power_w: float,
) -> ControlCommand:
    """Determine HPES operating mode and requested electrical power."""
    power_difference_w = renewable_power_w - target_power_w

    match power_difference_w:
        case n if n > 0:
            operating_mode = OperatingMode.CHARGING
        case n if n < 0:
            operating_mode = OperatingMode.DISCHARGING
        case _:
            operating_mode = OperatingMode.IDLE

    return ControlCommand(
        mode=operating_mode,
        electrical_power_w=abs(power_difference_w),
    )