"""Dynamic state definitions for the HPES simulation."""

from dataclasses import dataclass
from enum import Enum, auto


class OperatingMode(Enum):
    """Represent the commanded operating mode of the HPES system."""
    IDLE = auto()
    CHARGING = auto()
    DISCHARGING = auto()


@dataclass(frozen=True)
class HPESState:
    """
    Represent the dynamic thermodynamic state of the PCS at one instant.

    (Pressure and liquid volume are not stored because they are derived
    from the independent state variables and fixed model parameters.)
    """
    
    time_s: float
    gas_volume_m3: float
    gas_temperature_k: float
