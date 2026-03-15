import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_calibration, get_zcb_curve
from vasicek.core import zcb_analytical
import numpy as np

st.set_page_config(page_title="I(b) ZCB Analytical", page_icon="💵", layout="wide")

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

st.markdown('<div class="page-title">Part I(b) — Analytical ZCB Price</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
Under the Vasicek model, the ZCB price uses the exponential affine formula:<br><br>
<b>Z(t,T) = exp(A(τ) − B(τ)·r(t))</b><br><br>
where B(τ) = (1 − e^(−aτ))/a and A(τ) = (b − σ²/2a²)(B(τ) − τ) − σ²B(τ)²/4a<br><br>
This is exact and closed-form — no simulation needed.
</div>
""", unsafe_allow_html=True)

cal = get_calibration()

st.sidebar.header("Parameters")
r0_s    = st.sidebar.slider("r(0) %",    0.5,  8.0,  float(cal["r0"]*100),   0.1) / 100
a_s     = st.sidebar.slider("a",         0.05, 2.0,  float(cal["a"]),         0.05)
b_s     = st.sidebar.slider("b %",       1.0,  8.0,  float(cal["b"]*100),     0.1) / 100
sigma_s = st.sidebar.slider("σ",         0.001,0.05, float(cal["sigma"]),      0.001)

mats   = list(np.round(np.linspace(0.25, 10, 80), 4))
prices = [zcb_analytical(r0_s, a_s, b_s, sigma_s, T) for T in mats]
zcb_5y = zcb_analytical(r0_s, a_s, b_s, sigma_s, 5.0)
spot5  = -np.log(zcb_5y) / 5

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="result-box">
        <div class="result-label">ZCB Price Z(0,5)</div>
        <div class="result-value">${zcb_5y:.6f}</div>
        <div class="result-label">face value $1</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="result-box">
        <div class="result-label">Implied 5Y Spot Rate</div>
        <div class="result-value">{spot5*100:.4f}%</div>
        <div class="result-label">−ln(Z)/T</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=mats, y=prices, mode="lines",
                         line=dict(color="#a78bfa", width=2), name="ZCB Price"))
fig.add_trace(go.Scatter(x=[5], y=[zcb_5y], mode="markers",
                         marker=dict(color="#f59e0b", size=10),
                         name=f"Z(0,5) = {zcb_5y:.4f}"))
fig.update_layout(
    title="Vasicek ZCB Price Curve (Analytical)",
    height=400, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11),
    xaxis=dict(title="Maturity (years)", gridcolor="#1a1a2a"),
    yaxis=dict(title="Price ($)", gridcolor="#1a1a2a"),
    margin=dict(l=40, r=40, t=50, b=40)
)
st.plotly_chart(fig, use_container_width=True)
