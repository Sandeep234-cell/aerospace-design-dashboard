import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO
import os

st.set_page_config(page_title="Aerospace Dashboard", layout="wide")

tab1, tab2, tab3 = st.tabs(["Aircraft Design", "Performance", "Reports"])

# =====================================================
# TAB 1 - INPUT + AIRFOIL
# =====================================================
with tab1:
    st.title("✈️ Aircraft Design")

    aircraft_name = st.text_input("Aircraft Name", "My Aircraft")

    airfoil = st.selectbox(
        "Airfoil",
        ["NACA0012", "NACA2412", "NACA4412", "NACA23012"]
    )

    mach = st.number_input("Mach", value=0.3)
    rho = st.number_input("Density", value=1.225)
    span = st.number_input("Wing Span", value=10.0)
    area = st.number_input("Wing Area", value=12.0)
    alpha = st.number_input("AoA (deg)", value=5.0)

    velocity = mach * 343
    AR = span**2 / area

    CL = 0.1 * alpha
    CD = 0.02 + (CL**2)/(np.pi * AR * 0.8)

    q = 0.5 * rho * velocity**2
    lift = q * area * CL
    drag = q * area * CD
    LD = lift / drag

    st.subheader("Results")
    st.write(f"CL: {CL:.3f}, CD: {CD:.4f}, L/D: {LD:.2f}")

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

        yt = 5 * t * (
            0.2969*np.sqrt(x)
            -0.1260*x
            -0.3516*x**2
            +0.2843*x**3
            -0.1015*x**4
        )

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

        fig, ax = plt.subplots(figsize=(7,4), dpi=150)
        ax.plot(xu, yu, label="Upper")
        ax.plot(xl, yl, label="Lower")
        ax.plot(x, yc, "--")
        ax.set_title("Airfoil Shape")
        ax.grid()
        ax.legend()
        return fig

    st.pyplot(airfoil_plot())

# =====================================================
# TAB 2 - PERFORMANCE
# =====================================================
with tab2:
    st.title("📊 Performance")

    alpha_range = np.arange(-5, 16, 1)

    CL_arr = 0.1 * alpha_range
    CD_arr = 0.02 + (CL_arr**2)/(np.pi*(AR)*0.8)
    LD_arr = CL_arr / CD_arr
    CM_arr = -0.05 * alpha_range

    figs = []

    def make_plot(y, title):
        fig, ax = plt.subplots(figsize=(7,4), dpi=200)
        ax.plot(alpha_range, y, linewidth=2)
        ax.set_title(title)
        ax.grid()
        return fig

    f1 = make_plot(CL_arr, "CL vs AoA")
    st.pyplot(f1); figs.append(f1)

    f2 = make_plot(CD_arr, "CD vs AoA")
    st.pyplot(f2); figs.append(f2)

    f3 = make_plot(LD_arr, "L/D vs AoA")
    st.pyplot(f3); figs.append(f3)

    f4, ax4 = plt.subplots(figsize=(7,4), dpi=200)
    ax4.plot(CD_arr, CL_arr, marker="o")
    ax4.set_title("Drag Polar")
    ax4.grid()
    st.pyplot(f4); figs.append(f4)

    f5 = make_plot(CM_arr, "Cm vs AoA")
    st.pyplot(f5); figs.append(f5)

# =====================================================
# TAB 3 - REPORTS (KILLER EXPORT)
# =====================================================
with tab3:
    st.title("📄 Engineering Report Export")

    # INPUT DATA
    input_df = pd.DataFrame([{
        "Aircraft": aircraft_name,
        "Mach": mach,
        "Density": rho,
        "Span": span,
        "Area": area,
        "AoA": alpha,
        "CL": CL,
        "CD": CD,
        "L/D": LD
    }])

    # OUTPUT DATA
    output_df = pd.DataFrame({
        "AoA": alpha_range,
        "CL": CL_arr,
        "CD": CD_arr,
        "L/D": LD_arr,
        "Cm": CM_arr
    })

    st.download_button("Download Input Data",
                       input_df.to_csv(index=False).encode(),
                       file_name="input_data.csv")

    st.download_button("Download Output Data",
                       output_df.to_csv(index=False).encode(),
                       file_name="output_data.csv")

    # ================= PDF =================
    def make_pdf():
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, 800, "Aerospace Engineering Report")

        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 780, f"Aircraft: {aircraft_name}")
        pdf.drawString(50, 765, f"CL: {CL:.3f} CD: {CD:.4f} L/D: {LD:.2f}")

        pdf.showPage()

        y = 700

        for i, fig in enumerate(figs):
            img = f"g{i}.png"
            fig.savefig(img, dpi=300, bbox_inches="tight")

            pdf.drawImage(img, 40, y, width=520, height=200)
            y -= 220

            if y < 100:
                pdf.showPage()
                y = 700

            os.remove(img)

        pdf.save()
        buffer.seek(0)
        return buffer

    pdf = make_pdf()

    st.download_button(
        "Download FULL Engineering PDF (ALL graphs + data)",
        pdf,
        file_name="aero_report.pdf"
    )
