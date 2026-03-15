import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_calibration, get_swap_rate
import numpy as np

st.set_page_config(page_title="I(d) Swap Rate", page_icon="🔄", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { background-color: #0a0a0f; color: #e8e8e8; font-family: 'Inter', sans-serif; }
.page-title { font-size: 2rem; font-weight: 600; color: #f0f0f0; margin-bottom: 0.2rem; }
.theory-box { background: #12121a; border-left: 3px solid #a78bfa; border-radius: 0 8px 8px 0; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; color: #aaa; line-height: 1.7; }
.result-box { background: #12121a; border: 1px solid #1e1e2e; border-radius: 10px; padding: 1rem 1.5rem; text-align: center; }
.result-label { font-size: 0.72rem; color: #666; text-transform: uppercase; letter-spacing: 0.08em; }
.result-value { font-size: 1.5rem; font-weight: 600; color: #a78bfa; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Part I(d) — Interest Rate Swap Rate</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
The par swap rate equates the PV of fixed and floating legs:<br><br>
<b>Swap Rate = (1 − Z(N)) / Σ Z(i)·Δt</b> for i = 1 to N<br><br>
Where Z(i) is the Vasicek ZCB price at maturity i and Δt is the payment interval.
For annual payments Δt = 1. The floating leg is linked to SOFR.
</div>
""", unsafe_allow_html=True)

cal = get_calibration()

st.sidebar.header("Parameters")
N_s  = st.sidebar.slider("Swap maturity (years)", 1, 10, 5, 1)
r0_s = st.sidebar.slider("r(0) %", 0.5, 8.0, float(cal["r0"]*100), 0.1) / 100

result = get_swap_rate(r0=r0_s, N=N_s)

c1, c2, c3 = st.columns(3)
for col, label, val, sub in [
    (c1, "Swap Rate",    f"{result['swap_rate']*100:.4f}%", f"{N_s}Y IRS fixed leg"),
    (c2, "Numerator",    f"{result['numerator']:.6f}",      "1 − Z(N)"),
    (c3, "Denominator",  f"{result['denominator']:.6f}",    "Σ Z(i)·Δt"),
]:
    with col:
        st.markdown(f"""<div class="result-box">
            <div class="result-label">{label}</div>
            <div class="result-value">{val}</div>
            <div class="result-label" style="margin-top:0.3rem">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

times = result["payment_times"]
zcbs  = result["zcb_prices"]
sr    = result["swap_rate"]

fig = go.Figure()
fig.add_trace(go.Bar(x=times, y=zcbs, name="ZCB price Z(0,i)",
                     marker_color="#a78bfa", opacity=0.85, width=0.4))
fig.add_hline(y=sr, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"Swap Rate = {sr*100:.4f}%")
fig.update_layout(
    title=f"ZCB Prices and {N_s}Y Swap Rate",
    height=400, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11),
    xaxis=dict(title="Maturity (years)", gridcolor="#1a1a2a",
               tickvals=times, ticktext=[f"{t:.0f}y" for t in times]),
    yaxis=dict(title="Price / Rate", gridcolor="#1a1a2a"),
    margin=dict(l=40, r=40, t=50, b=40)
)
st.plotly_chart(fig, use_container_width=True)
