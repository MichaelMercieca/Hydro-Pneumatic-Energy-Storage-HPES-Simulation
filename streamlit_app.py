"""Public HPES engineering demonstrator. Start with streamlit run streamlit_app.py."""

from dataclasses import asdict
from datetime import date
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from hpes_sim.era5 import DATASET, START_DATE, END_DATE, select_dates
from hpes_sim.web_model import Design, simulate

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Closed HPES Simulation", layout="wide")


@st.cache_data(max_entries=1)
def wind_data():
    return pd.read_csv(ROOT / "examples" / "era5_2025.csv", index_col=0, parse_dates=True)


def finish_run(wind, design, start, end):
    with st.spinner("Running the storage model…"):
        output, metrics = simulate(wind, design)
    st.session_state.pop("csv_download", None)
    st.session_state.result = (output, metrics, {
        "design": asdict(design), "start": str(start), "end": str(end),
        "source": "ERA5 2025", "dataset": DATASET, "latitude": 35.75, "longitude": 14.75,
        "time_step_s": 60, "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "state_timing": "Powers apply over each interval; thermodynamic states are at interval end.",
        "data_attribution": "ERA5, ECMWF via Copernicus Climate Data Store; CC BY 4.0; wind converted to model outputs.",
        "dataset_doi": "https://doi.org/10.24381/1cf1ad76",
        "data_license": "https://creativecommons.org/licenses/by/4.0/",
    })


def line_chart(frame, columns, labels, title, unit, limits=()):
    figure = go.Figure()
    colors = ["#8996a8", "#d89a36", "#087f8c"] if len(columns) == 3 else ["#087f8c", "#d89a36"]
    for column, label, color in zip(columns, labels, colors):
        figure.add_trace(go.Scatter(x=frame.index, y=frame[column], name=label,
                                   mode="lines", line={"color": color, "width": 1.6, "shape": "hv"}))
    for value in limits:
        figure.add_hline(y=value, line_dash="dash", line_color="#a6aab1")
    figure.update_layout(title=title, yaxis_title=unit, height=320, margin=dict(l=10, r=10, t=45, b=15),
                         legend=dict(orientation="h", y=1.15), hovermode="x unified", xaxis_title="UTC")
    return credit_chart(figure)


def credit_chart(figure):
    """Keep data credit attached when a visitor exports a plot as PNG."""
    figure.add_annotation(text="Derived from ERA5 · © ECMWF / C3S CDS · CC BY 4.0<br>doi.org/10.24381/1cf1ad76",
                          x=0, y=-0.4, xref="paper", yref="paper", showarrow=False,
                          xanchor="left", font=dict(size=9, color="#687785"))
    figure.update_layout(margin=dict(l=10, r=10, t=70, b=95), height=390)
    return figure


st.title("Closed Hydro-Pneumatic Energy Storage (C-HPES) Simulation")
st.caption("Wind-power smoothing using a C-HPES model at a reference site near Malta (35.75° N, 14.75° E). Wind data: ERA5 100 m wind over the year 2025")

st.subheader("Simulation settings")
with st.form("study"):
    dates = st.date_input("Wind date range (UTC, inclusive)",
                          (date(2025, 4, 9), date(2025, 4, 15)),
                          min_value=START_DATE, max_value=END_DATE)
    left, right = st.columns(2)
    with left:
        volume = st.slider("Total containment volume (m³)", 1000, 6000, 4080, 10,
                           help="Aggregate internal volume of the pressure containment, represented as one lumped vessel. Gas-volume fractions scale with this value.")
        depth = st.slider("Deployment depth (m)", 30, 200, 55, 5,
                          help="Sensitivity-study range based on published closed-cycle HPES cases. The selected depth is a model input, not a bathymetric measurement of the wind-data point.")
        power = st.slider("Pump / turbine electrical rating (MW)", 0.5, 10.0, 5.0, 0.5)
    with right:
        wind_rating = st.slider("Wind turbine rating (MW)", 1.0, 20.0, 10.0, 0.5)
        smoothing = st.slider("Trailing-average target window (h)", 2, 24, 6)
    submitted = st.form_submit_button("Run simulation", type="primary")

with st.expander("Model assumptions"):
    st.markdown((ROOT / "docs" / "model_assumptions.md").read_text(encoding="utf-8"))
with st.expander("System logic & main equations used"):
    st.markdown((ROOT / "docs" / "system_logic.md").read_text(encoding="utf-8"))

if submitted:
    try:
        if len(dates) != 2:
            raise ValueError("Choose both a start and an end date.")
        start, end = dates
        design = Design(volume, depth, power, wind_rating, smoothing)
        finish_run(select_dates(wind_data(), start, end), design, start, end)
    except ValueError as error:
        st.error(str(error))

if "result" not in st.session_state:
    st.info("Select Run simulation to calculate results for the selected period and settings.")
else:
    frame, metrics, metadata = st.session_state.result
    st.subheader("Results")
    st.caption(f"Completed run: {metadata['start']} through {metadata['end']} UTC · {metadata['source']} · "
               f"{metadata['design']['volume_m3']:,.0f} m³ · {metadata['design']['depth_m']:g} m depth · "
               f"{metadata['design']['power_mw']:g} MW storage · {metadata['design']['wind_rating_mw']:g} MW wind · "
               f"{metadata['design']['smoothing_hours']} h target. Controls take effect only after Run simulation.")
    a, b, c = st.columns(3)
    reduction = metrics["rmse_reduction_percent"]
    a.metric("RMSE reduction", "N/A" if reduction is None else f"{reduction:.1f}%")
    b.metric("RMSE without HPES", f"{metrics['raw_rmse_mw']:.3f} MW")
    c.metric("RMSE with HPES", f"{metrics['grid_rmse_mw']:.3f} MW")
    average_discharge = metrics.get("average_discharge_power_mw", metrics["discharged_mwh"] / (len(frame) * metadata["time_step_s"] / 3600))
    if metrics["pressure_outside_minutes"]:
        st.warning(f"Pressure is outside the operating band for {metrics['pressure_outside_minutes']:.0f} minutes. "
                   "Passive thermal relaxation is not actively regulated by this model; interpret this run as an exploratory result.")
    chart_frame = frame
    if len(frame) > 31 * 24 * 60:
        powers = frame[["wind_mw", "target_mw", "grid_mw", "storage_mw", "raw_error_mw", "residual_error_mw"]].resample("h").mean()
        states = frame[["gas_volume_m3", "gas_pressure_bar_abs", "gas_temperature_c"]].resample("h").last()
        chart_frame = powers.join(states)
        st.caption("Charts: hourly mean power/error and end-of-hour storage states. Metrics and downloadable data retain the 60-second resolution.")
    performance, operation, downloads = st.tabs(["Power smoothing", "Storage operation", "Results & downloads"])
    with performance:
        st.plotly_chart(line_chart(chart_frame, ["wind_mw", "target_mw", "grid_mw"],
                                  ["Wind", "Target", "Grid output"], "Power delivered to the grid", "MW"), width="stretch")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart_frame.index, y=chart_frame.residual_error_mw, name="With HPES", mode="lines", line=dict(color="#087f8c", shape="hv")))
        fig.add_trace(go.Scatter(x=chart_frame.index, y=chart_frame.raw_error_mw, name="Without HPES", mode="lines",
                                line=dict(color="#8996a8", shape="hv"), fill="tonexty", fillcolor="rgba(8,127,140,0.20)"))
        fig.update_layout(title="Absolute target error", yaxis_title="Absolute error (MW)", xaxis_title="UTC",
                          height=350, hovermode="x unified", legend=dict(orientation="h", y=1.15))
        st.plotly_chart(credit_chart(fig), width="stretch")
        st.caption("Shaded area compares absolute target error before and after storage. The target is a causal trailing average of hourly wind power.")
    with operation:
        st.plotly_chart(line_chart(chart_frame, ["storage_mw"], ["Storage"], "Storage power (+ = charging, - = discharging)", "MW", [0]), width="stretch")
        # left, right = st.columns(2)
        scale = metadata["design"]["volume_m3"] / 4080
        # with left:
        st.plotly_chart(line_chart(chart_frame, ["gas_pressure_bar_abs"], ["Pressure"], "Gas pressure", "bar absolute", [81.01325, 201.01325]), width="stretch")
        # with right:
        st.plotly_chart(line_chart(chart_frame, ["gas_volume_m3"], ["Gas volume"], "Gas volume", "m³", [1200 * scale, 3900 * scale]), width="stretch")
        st.plotly_chart(line_chart(chart_frame, ["gas_temperature_c"], ["Temperature"], "Gas temperature", "°C", [14]), width="stretch")
        st.caption("Dashed lines show operating limits or the 14°C seawater reference. State values are recorded at the end of each 60-second interval.")
    with downloads:
        st.write(f"Average discharge power: **{average_discharge:.3f} MW** over the full selected period, including idle and charging hours.")
        interval_hours = metadata["time_step_s"] / 3600
        wind_energy = float(frame.wind_mw.sum() * interval_hours)
        target_energy = float(frame.target_mw.sum() * interval_hours)

        def energy_share(value, total, basis):
            return f"{100 * value / total:.1f}% of {basis}" if total > 1e-12 else f"N/A — no {basis}"

        st.caption(f"Selected period: {wind_energy:.2f} MWh of wind generation; {target_energy:.2f} MWh of target delivery.")
        st.table(pd.DataFrame({
            "Energy measure": ["Charging energy", "Surplus energy", "Energy shortfall"],
            "Amount": [f"{metrics[key]:.2f} MWh" for key in ("charged_mwh", "surplus_mwh", "shortfall_mwh")],
            "Share of period total": [
                energy_share(metrics["charged_mwh"], wind_energy, "wind generation"),
                energy_share(metrics["surplus_mwh"], target_energy, "target delivery"),
                energy_share(metrics["shortfall_mwh"], target_energy, "target delivery"),
            ],
        }).set_index("Energy measure"))
        st.caption("Surplus and shortfall are measured relative to the smoothing target.")
        if st.button("Prepare time-series download"):
            from io import BytesIO
            with st.spinner("Preparing download…"):
                buffer = BytesIO()
                frame.to_csv(buffer, compression={"method": "gzip", "compresslevel": 1}, chunksize=10000)
                st.session_state.csv_download = buffer.getvalue()
        if "csv_download" in st.session_state:
            st.download_button("Download time series (CSV.gz)", st.session_state.csv_download, "hpes_results.csv.gz", "application/gzip")
        st.download_button("Download study settings & metrics (JSON)", json.dumps({**metadata, "metrics": metrics}, indent=2), "hpes_study.json", "application/json")
        st.dataframe(frame.iloc[::60], width="stretch")
        st.caption("Table: hourly snapshots. Compressed CSV: every simulation interval. Study JSON: settings, metrics and attribution.")

st.divider()
st.caption("ERA5 wind data © ECMWF, supplied through the Copernicus Climate Change Service Climate Data Store. "
           "[Dataset & DOI](https://doi.org/10.24381/1cf1ad76) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). "
           "Wind components are transformed into wind speed, idealised turbine power and HPES simulation results.")
