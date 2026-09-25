**1.** Wind magnitude is $v=\sqrt{u_{100}^2+v_{100}^2}$. The turbine produces zero below cut-in or at/above cut-out, rated power above rated speed, and the following power between cut-in and rated speed:

$$
P_w=P_r\frac{v^3-v_{ci}^3}{v_r^3-v_{ci}^3}
$$

**2.** The target is set as the trailing mean of the current and preceding hourly wind-power samples within the selected window. The system charges when wind exceeds target and discharges when wind falls below target. Requested power is the absolute difference with constraints (equipment rating, etc.)

**3.** Gas pressure is absolute. External pressure includes atmospheric pressure, and z is depth. Hydraulic flow is positive for water entering the vessel (charging).

$$
p_gV_g=mRT,\qquad p_s=p_{atm}+\rho gz,\qquad \Delta p=p_g-p_s
$$

$$
Q_h=\frac{\eta_p P_{charge}}{\Delta p}\quad\text{(charging)},\qquad Q_h=-\frac{P_{discharge}}{\eta_t\Delta p}\quad\text{(discharging)}
$$

**4.** Temperature is determined by compression work and heat exchange, while volume changes with hydraulic flow. The simulation advances these equations using explicit Euler steps.

$$
\frac{dV_g}{dt}=-Q_h,\qquad mc_v\frac{dT_g}{dt}=hA(T_s-T_g)+p_gQ_h
$$

**5.** For smoothing, charging power and discharging power below are nonnegative magnitudes. RMSE uses all equal-duration intervals. Percentage reduction is undefined when baseline error is zero.

$$
P_{grid}=P_w-P_{charge}+P_{discharge},\qquad \mathrm{RMSE}=\sqrt{\frac{1}{N}\sum_{i=1}^{N}(P_i-P_{t,i})^2}
$$

$$
\text{Error reduction}=100\left(1-\frac{\mathrm{RMSE}_{grid}}{\mathrm{RMSE}_{wind}}\right)\%
$$
