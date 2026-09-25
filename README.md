# Try out the simulation online: https://closed-hpes-simulation.streamlit.app/

## Closed Hydro-Pneumatic Energy Storage Simulation

A Python model of closed-cycle hydro-pneumatic storage for wind-power smoothing, with a Streamlit web interface. Wind input is ERA5 data for 2025 at 35.75° N, 14.75° E, near Malta.

Select any period within 2025 and adjust containment volume, deployment depth, equipment rating and smoothing window. Results include power and error plots, gas pressure/volume/temperature, RMSE and energy totals. Time series and study settings can be downloaded.

`src/hpes_sim/` contains the model, `streamlit_app.py` the interface, `examples/` the wind data, and `tests/` the tests. [Model assumptions](docs/model_assumptions.md) and [governing equations](docs/system_logic.md) describe the engineering basis and limitations.

ERA5 data © ECMWF, provided through the Copernicus Climate Change Service Climate Data Store, [DOI: 10.24381/1cf1ad76](https://doi.org/10.24381/1cf1ad76), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Wind components were converted to CSV and are transformed into model outputs. Software: MIT licence.
