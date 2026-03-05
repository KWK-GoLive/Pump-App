import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# --- Core Functions (Unchanged) ---
def generate_theoretical_pump_curve(q_duty, h_duty, target_efficiency, rho=1000, g=9.81):
    q_duty_m3s = q_duty / 3600
    p_shaft_w = (rho * g * q_duty_m3s * h_duty) / target_efficiency
    p_shaft_kw = p_shaft_w / 1000
    
    eta_duty = target_efficiency
    q_array = np.linspace(0, q_duty * 1.5, 20)
    
    h0 = h_duty * 1.2
    k_head = (h0 - h_duty) / (q_duty**2)
    h_array = h0 - k_head * (q_array**2)
    
    a_eta = -eta_duty / (q_duty**2)
    b_eta = (2 * eta_duty) / q_duty
    eta_array = (a_eta * (q_array**2) + b_eta * q_array) * 100
    eta_array = np.where(eta_array < 0, 0, eta_array)

    npshr_duty = max(1.5, h_duty * 0.05) 
    npsh_0 = 1.0 
    
    if npshr_duty <= npsh_0:
         npshr_duty = npsh_0 + 2.0
         
    k_npsh = (npshr_duty - npsh_0) / (q_duty**2)
    npshr_array = npsh_0 + k_npsh * (q_array**2)

    df = pd.DataFrame({
        'Flow (m3/h)': np.round(q_array, 2),
        'Head (m)': np.round(h_array, 2),
        'Efficiency (%)': np.round(eta_array, 2),
        'NPSHr (m)': np.round(npshr_array, 2)
    })
    
    return df, q_duty, h_duty, eta_duty * 100, npshr_duty, p_shaft_kw

def calculate_pump_installed_cost(p_shaft_kw, cepci_current=800.0):
    k1, k2, k3 = 3.3892, 0.0536, 0.1538
    f_bm = 3.30
    cepci_base = 397.0 
    
    log_p = np.log10(p_shaft_kw)
    log_cp0 = k1 + k2 * log_p + k3 * (log_p**2)
    cp0 = 10**log_cp0
    
    c_bm_base = cp0 * f_bm
    c_bm_current = c_bm_base * (cepci_current / cepci_base)
    
    return cp0, c_bm_current

# --- Web App Interface ---
st.set_page_config(page_title="Pump Performance Model", layout="wide")
st.title("Pump Performance & Cost Model")
st.markdown("Analyze theoretical centrifugal pump curves and estimate bare module costs based on fundamental thermodynamic scaling.")

# Sidebar Inputs
st.sidebar.header("Operating Parameters")
Q_DUTY = st.sidebar.number_input("Design Flow Rate (m3/h)", min_value=10.0, max_value=1000.0, value=100.0, step=10.0)
H_DUTY = st.sidebar.number_input("Design Head (m)", min_value=5.0, max_value=500.0, value=50.0, step=5.0)
#TARGET_EFFICIENCY = st.sidebar.slider("Target Efficiency", min_value=0.50, max_value=0.95, value=0.85, step=0.01)

# Execution
curve_data, q_d, h_d, eta_d, npshr_d, calc_p_kw = generate_theoretical_pump_curve(Q_DUTY, H_DUTY, TARGET_EFFICIENCY)
base_cost, installed_cost = calculate_pump_installed_cost(calc_p_kw)

# Output Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Thermodynamic Shaft Power", f"{calc_p_kw:.2f} kW")
col2.metric("Base Equipment Cost (2001)", f"${base_cost:,.2f}")
col3.metric("Total Installed Cost (Current)", f"${installed_cost:,.2f}")

st.divider()

# Plotting and Table Columns
col_chart, col_data = st.columns([2, 1])

with col_chart:
    st.subheader("Performance Curves")
    fig, ax1 = plt.subplots(figsize=(8, 5))

    color1 = 'tab:blue'
    color3 = 'tab:red'
    ax1.set_xlabel('Flow Rate (m3/h)', fontweight='bold')
    ax1.set_ylabel('Head / NPSHr (m)', fontweight='bold')

    line1, = ax1.plot(curve_data['Flow (m3/h)'], curve_data['Head (m)'], color=color1, label='H-Q Curve', linewidth=2)
    line3, = ax1.plot(curve_data['Flow (m3/h)'], curve_data['NPSHr (m)'], color=color3, label='NPSHr Curve', linewidth=2)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2 = ax1.twinx()
    color2 = 'tab:green'
    ax2.set_ylabel('Efficiency (%)', color=color2, fontweight='bold')
    line2, = ax2.plot(curve_data['Flow (m3/h)'], curve_data['Efficiency (%)'], color=color2, linestyle='--', label='Efficiency Curve', linewidth=2)
    
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
