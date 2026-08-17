# HPES Project Plan
Dynamic performance analysis of hydro-pneumatic energy storage.

## 1. Interacting Models

- Wind
- Controller
- HPES pressure/volume model
- Thermal behaviour
- Electical output
- Marine Environment

### 1.1 Wind Model

Input a varying wind-history, *$v_{\mathrm{wind}}(t)$*, and turn that into turbine electrical power, *$P_{\mathrm{wind}}(t)$*.

Initially synthetic input, then add functionality to **feed off of historical wind dataset.**

### 1.2 Controller Model (Power Management)

Deciding between charge/discharge modes based off of **positive**/**negative** result originating from mathematical model. Example:
$$P_{\mathrm{wind}} - P_{\mathrm{desired}}$$

\+ constraints (ex: can't charge/discharge when full/empty, pressure can't exceed limit while meeting the required minimum accumulator pressure by rejecting too low pressures, pumps recieve maximum power+flow).

### 1.3 HPES Pressure/Volume Model

For this, need to understand:

- gas pressure and volume relationships
- compression and expansion
- work done during compression
- pre-charge pressure
- usable gas-volume range
- stored energy/capacity
- incompressible-liquid continuity
- pressure/flow/power relationships

### 1.4 Thermal Behaviour Model

Since compression rate affects pressure due to due to the opportunity to exchange heat with the surroundings, a thermal model can be developed, starting from an ideal isothermal model, transitioning to an ideal adiabatic or polytopic model, and if possible finally a more accurate finite heat-transfer model, + compare each.

### 1.5 Hydraulic Model

Considerations:

- pump during charging
- turbine during discharging
- flow rate
- pressure difference
- efficiency
- losses (ex: pipe losses)

### 1.6 Marne Environment Model

Cnsiderations that must be understood include:

- hydrostatic pressure vs depth
- external pressure acting on vessels
- displaced water volume
- buoyancy (upthrust)
- submerged weight
- seawater reaction
- seabed reaction and anchoring requirement

## 2. Mathematical Model

### 2.1 Building the Fluid Model

| Equation | Use |
| --- | --- |
| $p_{\rm outside}=p_{\rm atm}+\rho_{\rm sea}gh$ | Ambient pressure at PCS depth |
| $\Delta p=p_{\rm high}-p_{\rm low}$ | Hydraulic pressure difference across ECU |
| $V_T=V_l+V_g$ | PCS volume constraint |
| $V_{g,n+1}=V_{g,n}-Q_n\Delta t$ | Update gas volume each timestep |
| $V_{l,n+1}=V_T-V_{g,n+1}$ | Update liquid volume |
| $P_{\rm hyd}=\Delta p\,Q$ | Hydraulic power |
| $Q=P_{\rm hyd}/\Delta p$ | Required hydraulic flow |
| $P_{\rm hyd,ch}=\eta_{\rm pump}P_{\rm shaft}$ | Pump charging conversion |
| $P_{\rm elec,dis}=\eta_{\rm gen}\eta_{\rm turb}P_{\rm hyd,dis}$ | Electrical power recovered during discharge |
| $m_g=\dfrac{p_{g,0}V_{g,0}}{RT_{g,0}}$ | Calculate fixed gas mass at initialisation |
| $p_g=\dfrac{m_gRT_g}{V_g}$ | Gas pressure from current state |
| $\dot Q_{\rm heat}=hA(T_{\rm sea}-T_g)$ | Heat transfer between accumulator and sea |
| $\dfrac{dT_g}{dt}=\dfrac{hA(T_{\rm sea}-T_g)+p_gQ}{m_gc_v}$ | Transient gas-temperature model |
| $T_{g,n+1}=T_{g,n}+\dfrac{\Delta t}{m_gc_v}\left[hA(T_{\rm sea}-T_{g,n})+p_{g,n}Q_n\right]$ |  Temperature over time |
| $p_{g,n+1}=\dfrac{m_gRT_{g,n+1}}{V_{g,n+1}}$ | Recalculate pressure after timestep |

## 2.2 Wind, Control, Capacity & Performance

| Equation | Use |
| --- | --- |
| $P_{\rm wind}=f_{\rm turbine}(v_{\rm wind})$ | Convert wind-speed time series using turbine power curve |
| $P_{{\rm target},n}=\dfrac{1}{N}\sum_{k=0}^{N-1}P_{{\rm wind},n-k}$ | Rolling-average smoothing target |
| $P_{\rm mismatch}=P_{\rm wind}-P_{\rm target}$ | Decide charge/discharge request |
| $P_{\rm surplus}=\max(P_{\rm mismatch},0)$ | Available charging power |
| $P_{\rm deficit}=\max(-P_{\rm mismatch},0)$ | Required discharge power |
| $P_{\rm charge}=\min(P_{\rm surplus},P_{\rm charge,max})$ | Apply pump power limit |
| $P_{\rm discharge}=\min(P_{\rm deficit},P_{\rm discharge,max})$ | Apply turbine/generator power limit |
| $p_{\min}\le p_g\le p_{\max}$ | PCS operating-pressure constraint |
| $V_{g,\min}\le V_g\le V_{g,\max}$ | PCS operating-volume constraint |
| $SOC=\dfrac{V_{g,\max}-V_g}{V_{g,\max}-V_{g,\min}}$ | Volume-based state of charge |
| $Q_{\rm ch}=\dfrac{\eta_{\rm pump}P_{\rm charge}}{\Delta p}$ | Charging flow rate |
| $Q_{\rm dis}=-\dfrac{P_{\rm discharge}}{\eta_{\rm turb}\eta_{\rm gen}\Delta p}$ | Discharging flow rate |
| $P_{\rm grid}=P_{\rm wind}-P_{\rm charge}+P_{\rm discharge}$ | Actual smoothed output power |
| $\Delta E_n=P_n\Delta t$ | Energy transferred during one timestep |
| $P_{\rm curtailed}=\max(P_{\rm surplus}-P_{\rm charge},0)$ | Wind power that cannot be stored |
| $E_{\rm curtailed}=\sum_n P_{{\rm curtailed},n}\Delta t$ | Total curtailed wind energy |
| $P_{\rm shortfall}=\max(P_{\rm deficit}-P_{\rm discharge},0)$ | Target power storage cannot supply |
| $E_{\rm shortfall}=\sum_n P_{{\rm shortfall},n}\Delta t$ | Total unmet target energy |
| $RMSE=\sqrt{\dfrac{1}{N}\sum_{n=1}^{N}(P_{{\rm grid},n}-P_{{\rm target},n})^2}$ | Quantify smoothing performance |

## 3. Software Architecture & Testing

Tests to be run:  
- Initial ideal-gas state reproduces pre-charge pressure  
- $Q=0, T_g=T_{sea}$ leaves state unchanged
- Positive flow decreases gas volume
- Positive flow with $UA=0$ raises temperature
- Negative flow lowers temperature
- $T_g >T_{sea}$ gives negative heat flow
- Pump efficiency outside $0<η≤1$ is rejected
- Zero power mismatch gives IDLE
- Full PCS rejects further charge
- Empty PCS rejects further discharge
- Constant wind equal to target leaves PCS unchanged
- Smaller timesteps converge towards same result 

Software development workflow:
(on paper)  

Build Order:  
1. pyproject.toml
2. parameters.py & state.py
3. pcs.py
4. ecu.py & controller.py
5. step()
6. run_simulation()
7. Wind + pandas + plots + SciPy
8. Verification 