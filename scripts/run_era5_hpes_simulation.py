"""Run the HPES model using the downloaded ERA5 wind time series."""

from pathlib import Path

import matplotlib
from matplotlib.ticker import MultipleLocator
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from hpes_sim.controller import calculate_trailing_average_target_power_w
from hpes_sim.parameters import (
    ECUParameters,
    EnvironmentParameters,
    PCSParameters,
    WindTurbineParameters,
)
from hpes_sim.pcs import (
    calculate_gas_pressure_pa,
    calculate_initial_gas_mass_kg,
)
from hpes_sim.simulation import run_simulation
from hpes_sim.state import HPESState, OperatingMode
from hpes_sim.wind import (
    calculate_wind_farm_power_w,
    calculate_wind_speed_m_s,
    load_era5_wind_dataset,
    repeat_power_samples,
)


def main() -> None:
    """Run and plot a seven-day ERA5-driven HPES demonstration."""
    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "data" / "processed" / "era5_wind.nc"
    output_path = (
        project_root / "outputs" / "figures" / "era5_hpes_simulation.png"
    )

    wind_parameters = WindTurbineParameters(
        rated_power_w=10.0e6,
        cut_in_speed_m_s=3.0,
        rated_speed_m_s=11.0,
        cut_out_speed_m_s=25.0,
        number_of_turbines=1,
    )
    pcs_parameters = PCSParameters(
        total_volume_m3=4080.0,
        initial_gas_volume_m3=3000.0,
        initial_absolute_pressure_pa=8.5e6,
        initial_temperature_k=287.15,
        heat_transfer_coefficient_w_m2_k=10.0,
        heat_transfer_area_m2=500.0,
        minimum_gas_volume_m3=1200.0,
        maximum_gas_volume_m3=3900.0,
    )
    ecu_parameters = ECUParameters(
        maximum_charging_power_w=5.0e6,
        maximum_discharging_power_w=5.0e6,
    )
    environment = EnvironmentParameters(
        deployment_depth_m=55.0,
        seawater_temperature_k=287.15,
    )
    initial_state = HPESState(
        time_s=0.0,
        gas_volume_m3=pcs_parameters.initial_gas_volume_m3,
        gas_temperature_k=pcs_parameters.initial_temperature_k,
    )

    with load_era5_wind_dataset(input_path) as dataset:
        wind_speed_m_s = calculate_wind_speed_m_s(dataset).load()
        hourly_wind_power_w = calculate_wind_farm_power_w(
            wind_speed_m_s,
            wind_parameters,
        ).load()

    hourly_wind_power_values_w = tuple(
        float(power_w) for power_w in hourly_wind_power_w.values
    )
    hourly_target_power_w = calculate_trailing_average_target_power_w(
        renewable_power_series_w=hourly_wind_power_values_w,
        window_steps=6,
    )

    simulation_time_step_s = 60.0
    wind_power_w = repeat_power_samples(
        hourly_wind_power_values_w,
        sample_interval_s=3600.0,
        simulation_time_step_s=simulation_time_step_s,
    )
    target_power_w = repeat_power_samples(
        hourly_target_power_w,
        sample_interval_s=3600.0,
        simulation_time_step_s=simulation_time_step_s,
    )

    gas_mass_kg = calculate_initial_gas_mass_kg(pcs_parameters)
    result = run_simulation(
        initial_state=initial_state,
        renewable_power_series_w=wind_power_w,
        target_power_series_w=target_power_w,
        gas_mass_kg=gas_mass_kg,
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=simulation_time_step_s,
    )

    time_hours = np.array([step.state.time_s for step in result.steps]) / 3600
    grid_power_mw = np.array(
        [step.grid_power_w for step in result.steps]
    ) / 1.0e6
    accepted_storage_power_mw = np.array([
        step.accepted_command.electrical_power_w
        * (
            1.0
            if step.accepted_command.mode is OperatingMode.CHARGING
            else -1.0
            if step.accepted_command.mode is OperatingMode.DISCHARGING
            else 0.0
        )
        for step in result.steps
    ]) / 1.0e6
    gas_volume_m3 = np.array(
        [state.gas_volume_m3 for state in result.states[1:]]
    )
    gas_temperature_k = np.array(
        [state.gas_temperature_k for state in result.states[1:]]
    )
    gas_pressure_bar = np.array([
        calculate_gas_pressure_pa(
            gas_mass_kg=gas_mass_kg,
            gas_volume_m3=state.gas_volume_m3,
            gas_temperature_k=state.gas_temperature_k,
            specific_gas_constant_j_kg_k=(
                pcs_parameters.specific_gas_constant_j_kg_k
            ),
        ) / 1.0e5
        for state in result.states[1:]
    ])

    wind_power_mw = np.array(wind_power_w) / 1.0e6
    target_power_mw = np.array(target_power_w) / 1.0e6
    raw_deviation_mw = wind_power_mw - target_power_mw
    grid_deviation_mw = grid_power_mw - target_power_mw
    raw_absolute_error_mw = np.abs(raw_deviation_mw)
    grid_absolute_error_mw = np.abs(grid_deviation_mw)
    raw_rmse_mw = float(np.sqrt(np.mean(raw_deviation_mw ** 2)))
    grid_rmse_mw = float(np.sqrt(np.mean(grid_deviation_mw ** 2)))
    rmse_reduction_percent = (
        100.0 * (raw_rmse_mw - grid_rmse_mw) / raw_rmse_mw
        if raw_rmse_mw > 0.0
        else 0.0
    )

    figure, axes = plt.subplots(6, 1, figsize=(30, 16), sharex=True)
    figure.suptitle("ERA5 C-HPES Simulation")

    axes[0].step(
        time_hours,
        wind_power_mw,
        where="post",
        color="0.65",
        linewidth=1.0,
        label="Wind",
    )
    axes[0].step(
        time_hours,
        target_power_mw,
        where="post",
        color="tab:orange",
        linewidth=1.5,
        label="Target",
    )
    axes[0].plot(
        time_hours,
        grid_power_mw,
        color="tab:green",
        linewidth=1.0,
        label="Grid output",
    )
    axes[0].set_ylabel("Power [MW]")
    axes[0].legend(ncol=3)

    axes[1].step(
        time_hours,
        raw_absolute_error_mw,
        where="post",
        color="0.65",
        linewidth=1.0,
        label="Without HPES",
    )
    axes[1].plot(
        time_hours,
        grid_absolute_error_mw,
        color="tab:green",
        linewidth=1.0,
        label="With HPES",
    )
    axes[1].fill_between(
        time_hours,
        grid_absolute_error_mw,
        raw_absolute_error_mw,
        step="post",
        color="tab:green",
        alpha=0.25,
        label="Error removed by HPES",
    )
    axes[1].set_ylabel("Absolute target error [MW]")
    axes[1].legend(ncol=3)

    axes[2].plot(time_hours, accepted_storage_power_mw)
    axes[2].axhline(0.0, linewidth=0.8)
    axes[2].set_ylabel("HPES power [MW]\n(+ charge, − discharge)")

    axes[3].plot(time_hours, gas_volume_m3)
    axes[3].axhline(pcs_parameters.minimum_gas_volume_m3, linestyle="--")
    axes[3].axhline(pcs_parameters.maximum_gas_volume_m3, linestyle="--")
    axes[3].set_ylabel("Gas volume [m³]")

    axes[4].plot(time_hours, gas_pressure_bar)
    axes[4].axhline(
        pcs_parameters.minimum_absolute_pressure_pa / 1.0e5,
        linestyle="--",
    )
    axes[4].axhline(
        pcs_parameters.maximum_absolute_pressure_pa / 1.0e5,
        linestyle="--",
    )
    axes[4].set_ylabel("Pressure [bar abs]")

    axes[5].plot(time_hours, gas_temperature_k)
    axes[5].axhline(environment.seawater_temperature_k, linestyle="--")
    axes[5].set_ylabel("Gas temperature [K]")
    axes[5].set_xlabel("Elapsed time [h]")
    axes[5].xaxis.set_major_locator(MultipleLocator(50))

    for axis in axes:
        axis.grid(alpha=0.25)

    figure.tight_layout(rect=[0,0,1,0.98])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200)
    # plt.show()
    plt.close(figure)

    print(f"Raw wind-to-target RMSE: {raw_rmse_mw:.3f} MW")
    print(f"Grid-to-target RMSE: {grid_rmse_mw:.3f} MW")
    print(f"RMSE reduction from HPES: {rmse_reduction_percent:.1f}%")
    print(f"Plot written to: {output_path}")


if __name__ == "__main__":
    main()
