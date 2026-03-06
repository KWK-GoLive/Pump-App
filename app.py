import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def generate_standard_water_curve_target_bep(q_duty_ls, h_duty, target_eta=0.80, g=9.81):
    q_duty_m3s = q_duty_ls / 1000.0
    q_duty_m3h = q_duty_ls * 3.6
    
    # Standard test water density at 20 deg C (Source: NIST data)
    rho_standard = 998.2 
    
    p_req_w = (rho_standard * g * q_duty_m3s * h_duty) / target_eta
    p_req_kw = p_req_w / 1000.0

    q_array = np.linspace(0, q_duty_m3h * 1.5, 20)
    
    h0 = h_duty * 1.2
    k_head = (h0 - h_duty) / (q_duty_m3h**2)
    h_array = h0 - k_head * (q_array**2)
    
    a_eta = -target_eta / (q_duty_m3h**2)
    b_eta = (2 * target_eta) / q_duty_m3h
    eta_array = (a_eta * (q_array**2) + b_eta * q_array) * 100
    eta_array = np.where(eta_array < 0, 0, eta_array)

    npshr_duty = max(1.5, h_duty * 0.05) 
    npsh_0 = 1.0 
    if npshr_duty <= npsh_0:
         npshr_duty = npsh_0 + 2.0
         
    k_npsh = (npshr_duty - npsh_0) / (q_duty_m3h**2)
    npshr_array = npsh_0 + k_npsh * (q_array**2)

    df = pd.DataFrame({
        'Flow (m3/h)': np.round(q_array, 2),
        'Head (m)': np.round(h_array, 2),
        'Efficiency (%)': np.round(eta_array, 2),
        'NPSHr (m)': np.round(npshr_array, 2)
    })
    
    return df, q_duty_m3h, p_req_kw

# --- Web App Interface ---
st.set_page_config(page_title="Standard Pump Performance Model", layout="wide")
st.title("Standard Manufacturer Pump Performance Model")
st.markdown("Generates performance curves calibrated for clear water at 20°C and calculates the motor safety margin based on required absorbed power.")

# Sidebar Inputs
st.sidebar.header("Datasheet Parameters")
Q_DUTY_LS = st.sidebar.number_input("Liquid flow rate (L/S)", min_value=1.0, max_value=500.0, value=26.892, step=1.0, format="%.3f")
H_DUTY = st.sidebar.number_input("Fluid head (M)", min_value=1.0, max_value=200.0, value=12.489, step=1.0, format="%.3f")
DRIVER_POWER_KW = st.sidebar.number_input("Driver power (KW)", min_value=0.1, max_value=1000.0, value=5.500, step=0.1, format="%.3f")

st.sidebar.header("Thermodynamic Assumptions")
TARGET_BEP = st.sidebar.slider("Target Peak Efficiency", min_value=0.50, max_value=0.95, value=0.80, step=0.01)

# Execution
curve_data, q_duty_m3h, calc_p_kw = generate_standard_water_curve_target_bep(Q_DUTY_LS, H_DUTY, TARGET_BEP)
safety_margin = ((DRIVER_POWER_KW / calc_p_kw) - 1) * 100

# Output Metrics
st.subheader("Thermodynamic Adjustments (Standard Water at 20°C)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Target Peak Efficiency", f"{TARGET_BEP * 100:.1f}%")
col2.metric("Datasheet Motor Power", f"{DRIVER_POWER_KW:.2f} kW")
col3.metric("Calculated Absorbed Power", f"{calc_p_kw:.2f} kW")
col4.metric("Motor Safety Margin", f"{safety_margin:.1f}%", delta_color="normal" if safety_margin >= 0 else "inverse")

st.divider()

# Plotting and Table Columns
col_chart, col_data = st.columns([2, 1])

with col_chart:
    st.subheader("Performance Curves")
    fig, ax1 = plt.subplots(figsize=(8, 5))

    color1 = 'tab:blue'
    color3 = 'tab:red'
    ax1.set_xlabel('Flow Rate ($m^3/h$)', fontweight='bold')
    ax1.set_ylabel('Head / NPSHr ($m$)', fontweight='bold')

    line1, = ax1.plot(curve_data['Flow (m3/h)'], curve_data['Head (m)'], color=color1, label='H-Q Curve', linewidth=2)
    line3, = ax1.plot(curve_data['Flow (m3/h)'], curve_data['NPSHr (m)'], color=color3, label='NPSHr Curve (Theoretical)', linewidth=2)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2 = ax1.twinx()
    color2 = 'tab:green'
    ax2.set_ylabel('Efficiency (%)', color=color2, fontweight='bold')
    line2, = ax2.plot(curve_data['Flow (m3/h)'], curve_data['Efficiency (%)'], color=color2, linestyle='--', label=r'$\eta$-Q Curve', linewidth=2)
    
    ax2.set_ylim(0, 100)
    ax2.set_yticks(np.arange(0, 110, 10))

    lines = [line1, line2, line3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='lower center')
    
    fig.tight_layout()
    st.pyplot(fig)

with col_data:
    st.subheader("Tabular Data")
    st.dataframe(curve_data, height=400)
