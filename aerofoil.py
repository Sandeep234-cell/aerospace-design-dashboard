import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO
import os

# ================= THEME =================
st.set_page_config(page_title="Aero CFD Dashboard", layout="wide")

st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Design",
    "Performance",
    "CFD Cp Field",
    "Reports"
])

# =====================================================
# TAB 1 - DESIGN
# =====================================================
with tab1:
    st.title("✈️ Aerospace Design Dashboard")

    c1, c2 = st.columns(2)

    with c1:
        aircraft_name = st.text_input("Aircraft Name", "My Aircraft")
        airfoil = st.selectbox("Airfoil", ["NACA0012", "NACA2412", "NACA4412", "NACA23012"])
        mach = st.number_input("Mach", value=0.3)
        rho = st.number_input("Density (kg/m³)", value=1.225)

    with c2:
        span = st.number_input("Wing Span (m)", value=10.0)
        area = st.number_input("Wing Area (m²)", value=12.0)
        alpha = st.number_input("AoA (deg)", value=5.0)

    # ================= AERO CALC =================
    mu = 1.81e-5
    chord = area / span
    velocity = mach * 343

    Re = (rho * velocity * chord) / mu
    q = 0.5 * rho * velocity**2

    CL = 0.1 * alpha
    CD = 0.02 + (CL**2)/(np.pi*span**2/area*0.8)

    lift = q * area * CL
    drag = q * area * CD
    LD = lift / drag

    st.subheader("📌 Aircraft Summary")

    st.info(f"""
Aircraft: {aircraft_name}  
Airfoil: {airfoil}  
Velocity: {velocity:.2f} m/s  
Chord: {chord:.3f} m  
Reynolds Number: {Re:.2e}  
Dynamic Pressure: {q:.2f} Pa  
""")

    st.success(f"""
CL={CL:.3f} | CD={CD:.4f} | L/D={LD:.2f}  
Lift={lift:.1f} N | Drag={drag:.1f} N
""")

    # ================= AIRFOIL =================
    def airfoil_plot():
        x = np.linspace(0, 1, 200)

        if "0012" in airfoil:
            m, p, t = 0.0, 0.0, 0.12
        elif "2412" in airfoil:
            m, p, t = 0.02, 0.4, 0.12
        elif "4412" in airfoil:
            m, p, t = 0.04, 0.4, 0.12
        else:
            m, p, t = 0.02, 0.3, 0.12

        yt = 5*t*(0.2969*np.sqrt(x)-0.1260*x-0.3516*x**2+0.2843*x**3-0.1015*x**4)

        if p == 0:
            yc = np.zeros_like(x)
            dyc = np.zeros_like(x)
        else:
            yc = np.where(
                x < p,
                m/(p**2)*(2*p*x - x**2),
                m/((1-p)**2)*((1-2*p)+2*p*x-x**2)
            )
            dyc = np.where(
                x < p,
                2*m/(p**2)*(p-x),
                2*m/((1-p)**2)*(p-x)
            )

        theta = np.arctan(dyc)

        xu = x - yt*np.sin(theta)
        yu = yc + yt*np.cos(theta)
        xl = x + yt*np.sin(theta)
        yl = yc - yt*np.cos(theta)

        fig, ax = plt.subplots(figsize=(5,3), dpi=150)
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.plot(xu, yu, color="#00ffcc")
        ax.plot(xl, yl, color="#00ffcc")
        ax.fill_between(xu, yu, yl, color="#00ffcc", alpha=0.08)

        ax.set_title("Airfoil Geometry", color="white")
        ax.tick_params(colors="white")
        ax.grid(alpha=0.2)
        ax.set_aspect("equal")

        st.pyplot(fig)

# =====================================================
# TAB 2 - PERFORMANCE (COMPACT)
# =====================================================
with tab2:
    st.title("📊 Performance")

    alpha_range = np.arange(-5, 16, 1)

    CL_arr = 0.1 * alpha_range
    CD_arr = 0.02 + (CL_arr**2)/(np.pi*(span**2/area)*0.8)
    LD_arr = CL_arr / CD_arr
    CM_arr = -0.05 * alpha_range

    def small(y, title, color):
        fig, ax = plt.subplots(figsize=(4,3), dpi=150)
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.plot(alpha_range, y, color=color)
        ax.set_title(title, color="white", fontsize=9)
        ax.grid(alpha=0.2)
        ax.tick_params(colors="white")
        return fig

    c1, c2, c3 = st.columns(3)

    with c1:
        st.pyplot(small(CL_arr, "CL vs AoA", "#00ffcc"))
    with c2:
        st.pyplot(small(CD_arr, "CD vs AoA", "#ff4444"))
    with c3:
        st.pyplot(small(LD_arr, "L/D vs AoA", "#00ff00"))

    c4, c5 = st.columns(2)

    with c4:
        st.pyplot(small(CM_arr, "Cm vs AoA", "#ffaa00"))

    with c5:
        fig, ax = plt.subplots(figsize=(4,3), dpi=150)
        ax.plot(CD_arr, CL_arr, color="cyan")
        ax.set_title("Drag Polar", color="white")
        ax.grid(alpha=0.2)
        st.pyplot(fig)

# =====================================================
# TAB 3 - CFD STYLE Cp FIELD (NEW)
# =====================================================
with tab3:
    st.title("🌪 CFD-Style Pressure Field (Cp)")

    x = np.linspace(-1.5, 2, 200)
    y = np.linspace(-1.2, 1.2, 200)
    X, Y = np.meshgrid(x, y)

    U_inf = 1.0
    R = 0.35

    r = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)

    V_r = U_inf * (1 - (R**2/(r**2 + 1e-6))) * np.cos(theta)
    V_t = -U_inf * (1 + (R**2/(r**2 + 1e-6))) * np.sin(theta)

    V = np.sqrt(V_r**2 + V_t**2)

    Cp = 1 - (V/U_inf)**2
    Cp[r < R] = np.nan

    fig, ax = plt.subplots(figsize=(7,5), dpi=160)
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    cf = ax.contourf(X, Y, Cp, levels=50, cmap="coolwarm")
    ax.contour(X, Y, Cp, levels=12, colors="black", alpha=0.3)

    # streamlines (IMPORTANT)
    ax.streamplot(X, Y, V_r, V_t, color="white", density=1, linewidth=0.6)

    circle = plt.Circle((0,0), R, color="white")
    ax.add_patch(circle)

    ax.set_title("Pressure Coefficient (Cp) + Flow Streamlines", color="white")
    ax.tick_params(colors="white")
    ax.set_aspect("equal")

    st.pyplot(fig)

# =====================================================
# TAB 4 - REPORTS
# =====================================================
with tab4:
    st.title("📄 Engineering Report")

    st.write("### Input Data")
    st.write({
        "Aircraft": aircraft_name,
        "Airfoil": airfoil,
        "Mach": mach,
        "Span": span,
        "Area": area,
        "Reynolds": Re
    })

    st.write("### Output Data")
    st.write({
        "CL": CL,
        "CD": CD,
        "L/D": LD,
        "Lift": lift,
        "Drag": drag,
        "Dynamic Pressure": q
    })

    df = pd.DataFrame({
        "AoA": alpha_range,
        "CL": CL_arr,
        "CD": CD_arr,
        "L/D": LD_arr,
        "Cm": CM_arr
    })

    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode(),
        file_name="aero_output.csv"
    )
