"""Validated, UI-independent orchestration for the public engineering demo."""

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from hpes_sim.controller import calculate_trailing_average_target_power_w
from hpes_sim.parameters import PCSParameters, ECUParameters, EnvironmentParameters, WindTurbineParameters
from hpes_sim.pcs import calculate_initial_gas_mass_kg
from hpes_sim.simulation import run_simulation
from hpes_sim.state import HPESState
from hpes_sim.wind import calculate_turbine_power_w


@dataclass(frozen=True)
class Design:
    volume_m3: float = 4080.0
    depth_m: float = 55.0
    power_mw: float = 5.0
    wind_rating_mw: float = 10.0
    smoothing_hours: int = 6

    def __post_init__(self):
        for name, low, high in (
            ("volume_m3", 1000, 6000), ("depth_m", 30, 200),
            ("power_mw", 0.5, 10), ("wind_rating_mw", 1, 20),
            ("smoothing_hours", 2, 24),
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be between {low} and {high}.")
        if int(self.smoothing_hours) != self.smoothing_hours:
            raise ValueError("Smoothing window must be a whole number of hours.")


def validate_wind(frame):
    """Require a complete, finite single-point hourly record; never fill gaps."""
    if not {"u100", "v100"}.issubset(frame.columns):
        raise ValueError("Wind data must contain u100 and v100.")
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.hasnans:
        raise ValueError("Wind data must have valid UTC timestamps.")
    if not 1 <= len(frame) <= 365 * 24:
        raise ValueError("Select between 1 and 365 days of hourly wind data.")
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("Wind timestamps must be unique and increasing.")
    if len(frame) > 1 and not (frame.index.to_series().diff().iloc[1:] == pd.Timedelta(hours=1)).all():
        raise ValueError("Wind data contains missing or non-hourly samples.")
    if not np.isfinite(frame[["u100", "v100"]].to_numpy()).all():
        raise ValueError("Wind data contains missing or non-finite values.")


def simulate(frame: pd.DataFrame, design: Design, time_step_s=60):
    """Return interval powers and end-of-interval states, with explicit units."""
    validate_wind(frame)
    if time_step_s not in (30, 60):
        raise ValueError("Supported timesteps are 30 and 60 seconds.")
    scale = design.volume_m3 / 4080.0
    pcs = PCSParameters(
        total_volume_m3=design.volume_m3, initial_gas_volume_m3=3000 * scale,
        initial_absolute_pressure_pa=8.5e6, initial_temperature_k=287.15,
        heat_transfer_coefficient_w_m2_k=10, heat_transfer_area_m2=500 * scale ** (2 / 3),
        minimum_gas_volume_m3=1200 * scale, maximum_gas_volume_m3=3900 * scale,
    )
    ecu = ECUParameters(maximum_charging_power_w=design.power_mw * 1e6,
                        maximum_discharging_power_w=design.power_mw * 1e6)
    env = EnvironmentParameters(design.depth_m, 287.15)
    turbine = WindTurbineParameters(design.wind_rating_mw * 1e6, 3, 11, 25)
    speed = np.hypot(frame.u100, frame.v100)
    hourly = [calculate_turbine_power_w(float(v), turbine) for v in speed]
    target = calculate_trailing_average_target_power_w(hourly, design.smoothing_hours)
    repetitions = 3600 // time_step_s
    wind = np.repeat(hourly, repetitions)
    target = np.repeat(target, repetitions)
    mass = calculate_initial_gas_mass_kg(pcs)
    # Keep only a day of detailed solver objects in memory, carrying state
    # continuously across chunks. Full-year outputs still retain every step.
    grid = np.empty(len(wind))
    volume = np.empty(len(wind))
    temperature = np.empty(len(wind))
    state = HPESState(0, pcs.initial_gas_volume_m3, 287.15)
    chunk_size = 24 * repetitions
    for offset in range(0, len(wind), chunk_size):
        stop = min(offset + chunk_size, len(wind))
        result = run_simulation(state, wind[offset:stop], target[offset:stop],
                                mass, pcs, ecu, env, time_step_s)
        grid[offset:stop] = [step.grid_power_w for step in result.steps]
        volume[offset:stop] = [state.gas_volume_m3 for state in result.states[1:]]
        temperature[offset:stop] = [state.gas_temperature_k for state in result.states[1:]]
        state = result.states[-1]
    storage = wind - grid
    pressure = mass * pcs.specific_gas_constant_j_kg_k * temperature / volume
    output = pd.DataFrame({
        "wind_mw": wind / 1e6, "target_mw": target / 1e6, "grid_mw": grid / 1e6,
        "storage_mw": storage / 1e6,
        "raw_error_mw": np.abs(wind - target) / 1e6,
        "residual_error_mw": np.abs(grid - target) / 1e6,
        "gas_volume_m3": volume, "gas_pressure_bar_abs": pressure / 1e5,
        "gas_temperature_c": temperature - 273.15,
    }, index=pd.date_range(frame.index[0], periods=len(wind), freq=f"{time_step_s}s"))
    output.index.name = "interval_start_utc"
    raw_rmse = float(np.sqrt(np.mean((wind - target) ** 2)) / 1e6)
    grid_rmse = float(np.sqrt(np.mean((grid - target) ** 2)) / 1e6)
    energy_factor = time_step_s / 3600 / 1e6
    pressure_out = (pressure < pcs.minimum_absolute_pressure_pa - 1) | (pressure > pcs.maximum_absolute_pressure_pa + 1)
    metrics = {
        "raw_rmse_mw": raw_rmse, "grid_rmse_mw": grid_rmse,
        "rmse_reduction_percent": 100 * (1 - grid_rmse / raw_rmse) if raw_rmse > 1e-12 else None,
        "charged_mwh": float(np.maximum(storage, 0).sum() * energy_factor),
        "discharged_mwh": float(np.maximum(-storage, 0).sum() * energy_factor),
        "average_discharge_power_mw": float(np.maximum(-storage, 0).mean() / 1e6),
        "surplus_mwh": float(np.maximum(grid - target, 0).sum() * energy_factor),
        "shortfall_mwh": float(np.maximum(target - grid, 0).sum() * energy_factor),
        "pressure_outside_minutes": float(pressure_out.sum() * time_step_s / 60),
    }
    if not np.isfinite(output.to_numpy()).all() or np.any(temperature <= 0):
        raise ValueError("The numerical model produced an invalid state.")
    return output, metrics
