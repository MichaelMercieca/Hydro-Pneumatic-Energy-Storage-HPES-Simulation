"""
Defines the (immutable) parameters for the HPES simulation.
"""

from dataclasses import dataclass


ATMOSPHERIC_PRESSURE_PA = 101_325.0


@dataclass(frozen=True)
class PCSParameters:
    """
    Define fixed parameters and initial conditions for the PCS model.

    Pressures are represented internally as absolute pressures in pascals.
    Air is modelled as an ideal gas with constant thermophysical properties.

    Parameters
    ----------
    total_volume_m3 : float
        Total internal PCS volume [m^3].
    initial_gas_volume_m3 : float
        Gas volume at the start of the simulation [m^3].
    initial_absolute_pressure_pa : float
        Initial absolute gas pressure [Pa].
    initial_temperature_k : float
        Initial spatially lumped gas temperature [K].
    heat_transfer_coefficient_w_m2_k : float
        Lumped gas-to-surroundings heat-transfer coefficient [W/(m^2 K)].
    heat_transfer_area_m2 : float
        Effective heat-transfer area [m^2].
    """
    total_volume_m3: float
    initial_gas_volume_m3: float
    initial_absolute_pressure_pa: float
    initial_temperature_k: float

    heat_transfer_coefficient_w_m2_k: float
    heat_transfer_area_m2: float
    
    minimum_absolute_pressure_pa: float = 80e5 + ATMOSPHERIC_PRESSURE_PA
    maximum_absolute_pressure_pa: float = 200e5 + ATMOSPHERIC_PRESSURE_PA

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

        if self.minimum_absolute_pressure_pa <= 0:
            raise ValueError("minimum_pressure_pa must be greater than 0.")

        if self.maximum_absolute_pressure_pa <= self.minimum_absolute_pressure_pa:
            raise ValueError(
                "maximum_pressure_pa must be greater than minimum_pressure_pa."
            )

        if not (
            self.minimum_absolute_pressure_pa
            <= self.initial_absolute_pressure_pa
            <= self.maximum_absolute_pressure_pa
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
    """Define constant environmental conditions for a simulation run."""
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
    """Define numerical time settings for a simulation run."""
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
