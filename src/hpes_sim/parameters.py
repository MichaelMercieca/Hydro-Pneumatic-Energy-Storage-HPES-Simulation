"""
Defines the parameters for the simulation.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class PCSParameters:
    total_volume_m3: float
    initial_gas_volume_m3: float
    initial_pressure_pa: float
    initial_temperature_k: float

    heat_transfer_coefficient_w_m2_k: float
    heat_transfer_area_m2: float
    
    minimum_pressure_pa: float = 80e5
    maximum_pressure_pa: float = 200e5

    specific_gas_constant_j_kg_k: float = 287.05
    specific_heat_cv_j_kg_k: float = 718.0

    def __post_init__(self) -> None:
        if self.total_volume_m3 <= 0:
            raise ValueError("total_volume_m3 must be greater than 0.")

        if not 0 < self.initial_gas_volume_m3 <= self.total_volume_m3:
            raise ValueError(
                "initial_gas_volume_m3 must be greater than 0 and "
                "no greater than total_volume_m3."
            )

        if self.minimum_pressure_pa <= 0:
            raise ValueError("minimum_pressure_pa must be greater than 0.")

        if self.maximum_pressure_pa <= self.minimum_pressure_pa:
            raise ValueError(
                "maximum_pressure_pa must be greater than minimum_pressure_pa."
            )

        if not (
            self.minimum_pressure_pa
            <= self.initial_pressure_pa
            <= self.maximum_pressure_pa
        ):
            raise ValueError(
                "initial_pressure_pa must lie between the minimum and maximum "
                "operating pressures."
            )

        if self.initial_temperature_k <= 0:
            raise ValueError("initial_temperature_k must be greater than 0 K.")

        if self.specific_gas_constant_j_kg_k <= 0:
            raise ValueError(
                "specific_gas_constant_j_kg_k must be greater than 0."
            )

        if self.specific_heat_cv_j_kg_k <= 0:
            raise ValueError(
                "specific_heat_cv_j_kg_k must be greater than 0."
            )

        if self.heat_transfer_coefficient_w_m2_k < 0:
            raise ValueError(
                "heat_transfer_coefficient_w_m2_k cannot be negative."
            )

        if self.heat_transfer_area_m2 <= 0:
            raise ValueError(
                "heat_transfer_area_m2 must be greater than 0."
            )

@dataclass(frozen=True)
class EnvironmentParameters:
    seawater_temperature_k: float
    seawater_density_kg_m3: float = 1025.0
    gravitational_acceleration_m_s2: float = 9.80665
    atmospheric_pressure_pa: float = 101_325.0
    
    def __post_init__(self) -> None:
        if self.seawater_temperature_k <= 0:
            raise ValueError("seawater_temperature_k must be greater than 0 K.")

        if self.seawater_density_kg_m3 <= 0:
            raise ValueError("seawater_density_kg_m3 must be greater than 0.")

        if self.gravitational_acceleration_m_s2 <= 0:
            raise ValueError(
                "gravitational_acceleration_m_s2 must be greater than 0."
            )

        if self.atmospheric_pressure_pa <= 0:
            raise ValueError("atmospheric_pressure_pa must be greater than 0.")

@dataclass(frozen=True)
class SimulationSettings:
    time_step_s: float
    duration_s: float

    def __post_init__(self) -> None:
        if self.time_step_s <= 0:
            raise ValueError("time_step_s must be greater than 0.")

        if self.duration_s <= 0:
            raise ValueError("duration_s must be greater than 0.")

        if self.time_step_s > self.duration_s:
            raise ValueError(
                "time_step_s cannot exceed duration_s."
            )
