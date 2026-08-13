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

## 2 Mathematical Model

### 2.1 Building the Fluid Model

Core equations to be used in the simulator:

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
| $T_{g,n+1}=T_{g,n}+\dfrac{\Delta t}{m_gc_v}\left[hA(T_{\rm sea}-T_{g,n})+p_{g,n}Q_n\right]$ | Explicit-Euler temperature update |
| $p_{g,n+1}=\dfrac{m_gRT_{g,n+1}}{V_{g,n+1}}$ | Recalculate pressure after timestep |