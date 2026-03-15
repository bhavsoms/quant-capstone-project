import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_calibration

st.set_page_config(page_title="I(a) Calibration", page_icon="📊", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0a0a0f;
    color: #e8e8e8;
    font-family: 'Inter', sans-serif;
}
.page-title {
    font-size: 2rem;
    font-weight: 600;
    color: #f0f0f0;
    margin-bottom: 0.2rem;
}
.theory-box {
    background: #12121a;
    border-left: 3px solid #a78bfa;
    border-radius: 0 8px 8px 0;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
    color: #aaa;
    line-height: 1.7;
}
.result-box {
    background: #12121a;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    text-align: center;
}
.result-label { font-size: 0.72rem; color: #666; text-transform: uppercase; letter-spacing: 0.08em; }
.result-value { font-size: 1.5rem; font-weight: 600; color: #a78bfa; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Part I(a) — Vasicek Calibration</div>', unsafe_allow_html=True)

st.markdown("""
<div class="theory-box">
We calibrate the Vasicek model parameters by discretizing the SDE and running OLS regression:<br><br>
<b>Δr = α + β·r(t) + ε</b> where α = a·b·Δt and β = −a·Δt<br><br>
From this: <b>a = −β/Δt</b> and <b>b = α/(a·Δt)</b><br><br>
The pre-2008 stationary subperiod is used for a and b. 
Sigma is estimated from the full sample for robustness.
OLS is used here for transparency — MLE would be statistically superior.
</div>
""", unsafe_allow_html=True)

with st.spinner("Fetching live FED data..."):
    cal = get_calibration()

c1, c2, c3, c4 = st.columns(4)
for col, label, val, sub in [
    (c1, "a — mean reversion", f"{cal['a']:.4f}", "speed of reversion"),
    (c2, "b — long-run mean",  f"{cal['b']*100:.2f}%", "equilibrium rate"),
    (c3, "σ — volatility",     f"{cal['sigma']:.4f}", "short rate vol"),
    (c4, "r(0) — current",     f"{cal['r0']*100:.2f}%", "latest FED rate"),
]:
    with col:
        st.markdown(f"""
        <div class="result-box">
            <div class="result-label">{label}</div>
            <div class="result-value">{val}</div>
            <div class="result-label" style="margin-top:0.3rem">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

dates = cal["fed_history"]["dates"]
rates = cal["fed_history"]["rates"]

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=rates, mode="lines",
                         line=dict(color="#a78bfa", width=1.5),
                         name="FED Funds Rate"))
fig.add_hline(y=cal["b"]*100, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"b = {cal['b']*100:.2f}%")
fig.add_hline(y=cal["r0"]*100, line_dash="dot", line_color="#34d399",
              annotation_text=f"r(0) = {cal['r0']*100:.2f}%")
fig.update_layout(
    title="FED Funds Rate — Vasicek Calibration",
    height=380,
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11),
    xaxis=dict(gridcolor="#1a1a2a"),
    yaxis=dict(title="Rate (%)", gridcolor="#1a1a2a"),
    legend=dict(bgcolor="#12121a"),
    margin=dict(l=40, r=40, t=50, b=40)
)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"Calibration method: {cal['method']} · {cal['n_obs']} observations · {cal['dates']['start']} to {cal['dates']['end']}")
