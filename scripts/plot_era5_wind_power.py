"""Plot ERA5 wind speed and simplified wind-farm power."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from hpes_sim.parameters import WindTurbineParameters
from hpes_sim.wind import (
    calculate_turbine_power_w,
    calculate_wind_farm_power_w,
    calculate_wind_speed_m_s,
    load_era5_wind_dataset,
)


def main() -> None:
    """Generate a diagnostic plot from the downloaded ERA5 week."""
    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "data" / "processed" / "era5_wind.nc"
    output_path = (
        project_root / "outputs" / "figures" / "era5_wind_power.png"
    )

    parameters = WindTurbineParameters(
        rated_power_w=15.0e6,
        cut_in_speed_m_s=3.0,
        rated_speed_m_s=11.0,
        cut_out_speed_m_s=25.0,
        number_of_turbines=10,
    )

    with load_era5_wind_dataset(input_path) as dataset:
        wind_speed_m_s = calculate_wind_speed_m_s(dataset).load()
        wind_farm_power_mw = (
            calculate_wind_farm_power_w(wind_speed_m_s, parameters).load()
            / 1.0e6
        )

    curve_speed_m_s = np.linspace(0.0, 30.0, 301)
    curve_power_mw = [
        calculate_turbine_power_w(speed, parameters) / 1.0e6
        for speed in curve_speed_m_s
    ]

    figure, axes = plt.subplots(
        3, 1, figsize=(12, 11), constrained_layout=True
    )
    figure.suptitle(
        "ERA5 Wind and Simplified 10 × 15 MW Wind-Farm Output"
    )

    axes[0].plot(wind_speed_m_s["valid_time"], wind_speed_m_s)
    axes[0].axhline(
        parameters.cut_in_speed_m_s,
        linestyle="--",
        label="Cut-in speed",
    )
    axes[0].axhline(
        parameters.rated_speed_m_s,
        linestyle=":",
        label="Rated speed",
    )
    axes[0].set_ylabel("Wind speed [m/s]")
    axes[0].legend()

    axes[1].plot(
        wind_farm_power_mw["valid_time"],
        wind_farm_power_mw,
    )
    axes[1].set_ylabel("Wind-farm power [MW]")
    axes[1].set_xlabel("Time [UTC]")
    # axes[1].tick_params(axis="x", labelrotation=30)

    axes[2].plot(curve_speed_m_s, curve_power_mw)
    axes[2].axvline(parameters.cut_in_speed_m_s, linestyle="--")
    axes[2].axvline(parameters.rated_speed_m_s, linestyle=":")
    axes[2].axvline(parameters.cut_out_speed_m_s, linestyle="--")
    axes[2].set_xlabel("Wind speed [m/s]")
    axes[2].set_ylabel("Single-turbine power [MW]")

    for axis in axes:
        axis.grid(alpha=0.25)

    # figure.autofmt_xdate()
    # figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)

    print(output_path)


if __name__ == "__main__":
    main()
