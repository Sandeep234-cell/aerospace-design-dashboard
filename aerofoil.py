import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO
import os

st.set_page_config(page_title="Aerospace Design Dashboard", layout="wide")

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["Aircraft Design", "Performance", "Reports"])

# =========================================================
# TAB 1 - DESIGN
# =========================================================
with tab1:
    st.title("✈️ Aircraft Design Dashboard")

    aircraft_name = st.text_input("Aircraft Name", "My Aircraft")

    airfoil = st.selectbox(
        "Airfoil",
        ["NACA0012", "NACA2412", "NACA4412", "NACA23012"]
    )

    mach = st.number_input("Mach", value=0.3)
    rho = st.number_input("Density (kg/m³)", value=1.225)
    span = st.number_input("Wing Span", value=10.0)
    area = st.number_input("Wing Area", value=12.0)
    alpha = st.number_input("AoA (deg)", value=5.0)

    def compute():
        velocity = mach * 343
        AR = span**2 / area

        CL = 0.1 * alpha
        CD = 0.02 + (CL**2) / (np.pi * AR * 0.8)

        q = 0.5 * rho * velocity**2

        lift = q * area * CL
        drag = q * area * CD

        LD = lift / drag

        return AR, CL, CD, lift, drag, LD

    AR, CL, CD, lift, drag, LD = compute()

    st.subheader("Results")
    st.write(f"Aspect Ratio: {AR:.2f}")
    st.write(f"CL: {CL:.3f}")
    st.write(f"CD: {CD:.4f}")
    st.write(f"Lift: {lift:.1f} N")
    st.write(f"Drag: {drag:.1f} N")
    st.write(f"L/D: {LD:.2f}")

    # ---------------- AIRFOIL ----------------
    def plot_airfoil(name):
        if "2412" in name:
            m, p, t = 0.02, 0.4, 0.12
        elif "4412" in name:
            m, p, t = 0.04, 0.4, 0.12
        elif "23012" in name:
            m, p, t = 0.02, 0.3, 0.12
        else:
            m, p, t = 0.0, 0.0, 0.12

        x = np.linspace(0, 1, 200)

        yt = 5 * t * (
            0.2969*np.sqrt(x)
            -0.1260*x
            -0.3516*x**2
            +0.2843*x**3
            -0.1015*x**4
        )

        # SAFE CAMBER FIX
        if p == 0 or m == 0:
            yc = np.zeros_like(x)
            dyc_dx = np.zeros_like(x)
        else:
            yc = np.where(
                x < p,
                m/(p**2) * (2*p*x - x**2),
                m/((1-p)**2) * ((1 - 2*p) + 2*p*x - x**2)
            )

            dyc_dx = np.where(
                x < p,
                2*m/(p**2) * (p - x),
                2*m/((1-p)**2) * (p - x)
            )

        theta = np.arctan(dyc_dx)

        xu = x - yt*np.sin(theta)
        yu = yc + yt*np.cos(theta)

        xl = x + yt*np.sin(theta)
        yl = yc - yt*np.cos(theta)

        fig, ax = plt.subplots()
        ax.plot(xu, yu, label="Upper")
        ax.plot(xl, yl, label="Lower")
        ax.plot(x, yc, "--", label="Camber")
        ax.set_title(name)
        ax.set_aspect("equal")
        ax.grid()
        ax.legend()

        return fig

    st.pyplot(plot_airfoil(airfoil))

# =========================================================
# TAB 2 - PERFORMANCE
# =========================================================
with tab2:
    st.title("📊 Performance Analysis")

    alpha_range = np.arange(-5, 16, 1)

    CL_arr = 0.1 * alpha_range
    AR_fixed = 10**2 / 12
    CD_arr = 0.02 + (CL_arr**2)/(np.pi*AR_fixed*0.8)
    LD_arr = CL_arr / CD_arr
    CM_arr = -0.05 * alpha_range

    figs = []  # IMPORTANT

    fig1, ax1 = plt.subplots()
    ax1.plot(alpha_range, CL_arr)
    ax1.set_title("CL vs AoA")
    ax1.grid()
    st.pyplot(fig1)
    figs.append(fig1)

    fig2, ax2 = plt.subplots()
    ax2.plot(alpha_range, CD_arr)
    ax2.set_title("CD vs AoA")
    ax2.grid()
    st.pyplot(fig2)
    figs.append(fig2)

    fig3, ax3 = plt.subplots()
    ax3.plot(alpha_range, LD_arr)
    ax3.set_title("L/D vs AoA")
    ax3.grid()
    st.pyplot(fig3)
    figs.append(fig3)

    fig4, ax4 = plt.subplots()
    ax4.plot(CD_arr, CL_arr, marker="o")
    ax4.set_title("Drag Polar")
    ax4.set_xlabel("CD")
    ax4.set_ylabel("CL")
    ax4.grid()
    st.pyplot(fig4)
    figs.append(fig4)

    fig5, ax5 = plt.subplots()
    ax5.plot(alpha_range, CM_arr)
    ax5.set_title("Cm vs AoA")
    ax5.grid()
    st.pyplot(fig5)
    figs.append(fig5)

# =========================================================
# TAB 3 - REPORTS
# =========================================================
with tab3:
    st.title("📄 Reports")

    df = pd.DataFrame({
        "AoA": alpha_range,
        "CL": CL_arr,
        "CD": CD_arr,
        "L/D": LD_arr,
        "Cm": CM_arr
    })

    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="aero_data.csv",
        mime="text/csv"
    )

    # ---------------- PDF ----------------
    def create_pdf():
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, 800, "Aerospace Design Report")

        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, 770, f"Aircraft: {aircraft_name}")
        pdf.drawString(50, 750, f"Airfoil: {airfoil}")
        pdf.drawString(50, 730, f"CL: {CL:.3f}")
        pdf.drawString(50, 710, f"CD: {CD:.4f}")
        pdf.drawString(50, 690, f"L/D: {LD:.2f}")

        y = 650

        # SAVE ALL GRAPHS INTO PDF
        for i, fig in enumerate(figs):
            img = f"plot_{i}.png"
            fig.savefig(img, dpi=300, bbox_inches="tight")
            pdf.drawImage(img, 50, y, width=500, height=140)
            y -= 150

            # cleanup
            if os.path.exists(img):
                os.remove(img)

        pdf.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = create_pdf()

    st.download_button(
        "Download PDF Report (All Graphs)",
        pdf_buffer,
        file_name="aerospace_report.pdf",
        mime="application/pdf"
    )
