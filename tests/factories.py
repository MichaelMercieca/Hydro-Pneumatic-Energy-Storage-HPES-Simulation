"""
Holds configurable constructors to be used throughout the tests.
Makes test modules more readable.     
"""

from hpes_sim.parameters import (
    EnvironmentParameters, PCSParameters, SimulationSettings
)
from hpes_sim.state import HPESState


def make_valid_pcs_parameters(**overrides):
    """
    Creates valid defaults for `PCSParameters`, overriding selected 
    values via keyword arguments to reduce boilerplate during tests.
    
    Uses a factory design patter for creating objects. 
    """
    values = {
        "total_volume_m3": 4080.0,
        "initial_gas_volume_m3": 3000.0,
        "initial_absolute_pressure_pa": 8.5e6,
        "initial_temperature_k": 287.15,
        "heat_transfer_coefficient_w_m2_k": 10.0,
        "heat_transfer_area_m2": 500.0,
    }
    
    values.update(overrides)    # Updates defaults with overriden values
    
    return PCSParameters(**values)  # Repacks key-value pairs into kwargs for `PCSParameters`


def make_valid_hpes_state(**overrides):
    values =  {
        "time_s": 0.0,
        "gas_volume_m3": 3000.0,
        "gas_temperature_k": 287.15,
    }
    values.update(overrides)    
    
    return HPESState(**values)


def make_valid_environment_parameters(**overrides):
    values = {
        "atmospheric_pressure_pa": 101.325e3,
        "gravitational_acceleration_m_s2": 9.81,
        "seawater_density_kg_m3": 1.025,
        "seawater_temperature_k": 297.15,
    }
    values.update(overrides)    
    
    return EnvironmentParameters(**values)


def make_valid_simulation_settings(**overrides):
    values = {
        "time_step_s": 1.0,
        "duration_s": 100.0,
    }
    values.update(overrides)
    
    return SimulationSettings(**values)
