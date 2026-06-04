import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO
import os

# ================= PAGE SETUP =================
st.set_page_config(page_title="Aerospace Dashboard", layout="wide")

st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Aircraft Design", "Performance", "Reports"])

# =====================================================
# TAB 1 - DESIGN
# =====================================================
with tab1:
    st.title("✈️ Aerospace Design Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        aircraft_name = st.text_input("Aircraft Name", "My Aircraft")
        airfoil = st.selectbox("Airfoil", ["NACA0012", "NACA2412", "NACA4412", "NACA23012"])
        mach = st.number_input("Mach", value=0.3)
        rho = st.number_input("Density (kg/m³)", value=1.225)

    with col2:
        span = st.number_input("Wing Span (m)", value=10.0)
        area = st.number_input("Wing Area (m²)", value=12.0)
        alpha = st.number_input("AoA (deg)", value=5.0)

    # ================= AERODYNAMICS =================
    mu = 1.81e-5
    chord = area / span
    velocity = mach * 343

    Re = (rho * velocity * chord) / mu
    q = 0.5 * rho * velocity**2

    AR = span**2 / area

    CL = 0.1 * alpha
    CD = 0.02 + (CL**2) / (np.pi * AR * 0.8)

    lift = q * area * CL
    drag = q * area * CD
    LD = lift / drag

    # ================= SUMMARY =================
    st.subheader("📌 Engineering Summary")

    st.info(f"""
Aircraft: {aircraft_name}  
Airfoil: {airfoil}  
Velocity: {velocity:.2f} m/s  
Chord: {chord:.3f} m  
Reynolds Number: {Re:.2e}  
Dynamic Pressure: {q:.2f} Pa  
""")

    st.success(f"""
CL = {CL:.3f} | CD = {CD:.4f} | L/D = {LD:.2f}  
Lift = {lift:.1f} N | Drag = {drag:.1f} N  
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
        ax.fill_between(xu, yu, yl, alpha=0.1, color="#00ffcc")

        ax.set_title(f"{airfoil} Airfoil", color="white")
        ax.grid(alpha=0.2)
        ax.tick_params(colors="white")
        ax.set_aspect("equal")

        return fig

    st.pyplot(airfoil_plot())

# =====================================================
# TAB 2 - PERFORMANCE (ALL BLACK + FIXED)
# =====================================================
with tab2:
    st.title("📊 Performance Dashboard")

    alpha_range = np.arange(-5, 16, 1)

    CL_arr = 0.1 * alpha_range
    CD_arr = 0.02 + (CL_arr**2)/(np.pi*(AR)*0.8)
    LD_arr = CL_arr / CD_arr
    CM_arr = -0.05 * alpha_range

    figs = []

    def plot(y, title, color):
        fig, ax = plt.subplots(figsize=(4,3), dpi=150)

        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.plot(alpha_range, y, color=color, linewidth=2)

        ax.set_title(title, color="white", fontsize=9)
        ax.grid(alpha=0.2)
        ax.tick_params(colors="white")

        return fig

    c1, c2, c3 = st.columns(3)

    f1 = plot(CL_arr, "CL vs AoA", "#00ffcc")
    f2 = plot(CD_arr, "CD vs AoA", "#ff5555")
    f3 = plot(LD_arr, "L/D vs AoA", "#00ff00")

    with c1: st.pyplot(f1); figs.append(f1)
    with c2: st.pyplot(f2); figs.append(f2)
    with c3: st.pyplot(f3); figs.append(f3)

    c4, c5 = st.columns(2)

    f4 = plot(CM_arr, "Cm vs AoA", "#ffaa00")

    fig5, ax5 = plt.subplots(figsize=(4,3), dpi=150)
    fig5.patch.set_facecolor("#0e1117")
    ax5.set_facecolor("#0e1117")

    ax5.plot(CD_arr, CL_arr, color="cyan", marker="o", markersize=3)
    ax5.set_title("Drag Polar", color="white")
    ax5.grid(alpha=0.2)
    ax5.tick_params(colors="white")

    with c4: st.pyplot(f4); figs.append(f4)
    with c5: st.pyplot(fig5); figs.append(fig5)

# =====================================================
# TAB 3 - REPORTS (FIXED SINGLE PAGE PDF - NO CRASH)
# =====================================================
with tab3:
    st.title("📄 Engineering Report")

    input_df = pd.DataFrame([{
        "Aircraft": aircraft_name,
        "Airfoil": airfoil,
        "Mach": mach,
        "Density": rho,
        "Span": span,
        "Area": area,
        "AoA": alpha,
        "Velocity": velocity,
        "Chord": chord,
        "Reynolds": Re,
        "Dynamic Pressure": q
    }])

    output_df = pd.DataFrame({
        "AoA": alpha_range,
        "CL": CL_arr,
        "CD": CD_arr,
        "L/D": LD_arr,
        "Cm": CM_arr
    })

    st.subheader("Input Data")
    st.dataframe(input_df)

    st.subheader("Output Data")
    st.dataframe(output_df)

    st.download_button("Download Input CSV",
                       input_df.to_csv(index=False).encode(),
                       file_name="input.csv")

    st.download_button("Download Output CSV",
                       output_df.to_csv(index=False).encode(),
                       file_name="output.csv")

    # ================= SAFE SINGLE PAGE PDF =================
    def make_pdf():
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, 800, "Aerospace Engineering Report")

        pdf.setFont("Helvetica", 9)

        pdf.drawString(50, 780, f"Aircraft: {aircraft_name}")
        pdf.drawString(50, 765, f"Airfoil: {airfoil}")
        pdf.drawString(50, 750, f"Velocity: {velocity:.2f} m/s")
        pdf.drawString(50, 735, f"Chord: {chord:.3f} m")
        pdf.drawString(50, 720, f"Reynolds: {Re:.2e}")
        pdf.drawString(50, 705, f"Dynamic Pressure: {q:.2f} Pa")
        pdf.drawString(50, 690, f"CL={CL:.3f} CD={CD:.4f} L/D={LD:.2f}")

        # SAFE GRID (NO INDEX ERROR)
        x_pos = [50, 300]
        y = 600
        col = 0

        for i, fig in enumerate(figs):
            img = f"g{i}.png"
            fig.savefig(img, dpi=250, bbox_inches="tight")

            pdf.drawImage(img, x_pos[col], y, width=220, height=160)

            os.remove(img)

            col += 1
            if col > 1:
                col = 0
                y -= 180

            if y < 120:
                break

        pdf.save()
        buffer.seek(0)
        return buffer

    pdf = make_pdf()

    st.download_button(
        "Download Full Engineering Report (Single Page)",
        pdf,
        file_name="aero_report.pdf"
    )
