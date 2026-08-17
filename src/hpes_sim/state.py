from dataclasses import dataclass
from enum import Enum, auto


class OperatingMode(Enum):
    IDLE = auto()
    CHARGING = auto()
    DISCHARGING = auto()


@dataclass(frozen=True)
class HPESState:
    time_s: float
    gas_volume_m3: float
    gas_temperature_k: float
