import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_calibration, get_bond_option
import numpy as np

st.set_page_config(page_title="I(e) Bond Option", page_icon="📉", layout="wide")

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

st.markdown('<div class="page-title">Part I(e) — European Call on ZCB</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
We price a European call on a 5Y ZCB (face $1000) expiring at t=4Y with strike K=900.<br><br>
<b>Payoff = max(Z[4y,5y] × 1000 − K, 0)</b><br><br>
Z[4y,5y] is computed analytically at each simulated r(4y) using the affine formula.
The payoff is discounted using either the simulated path integral or the 4Y spot rate.<br><br>
<b>Known limitation:</b> Vasicek allows negative rates — some paths may produce Z[t,T] &gt; face value.
This is a structural property of the model, not a coding error.
</div>
""", unsafe_allow_html=True)

cal = get_calibration()

st.sidebar.header("Parameters")
K_s    = st.sidebar.slider("Strike K ($)", 800, 980, 900, 10)
r0_s   = st.sidebar.slider("r(0) %", 0.5, 8.0, float(cal["r0"]*100), 0.1) / 100

with st.spinner("Running Monte Carlo simulation..."):
    result = get_bond_option(r0=r0_s, K=float(K_s))

c1, c2, c3, c4 = st.columns(4)
for col, label, val, sub in [
    (c1, "Option Price (path)", f"${result['price_path_discount']:.4f}", "path discounting"),
    (c2, "Option Price (spot)", f"${result['price_spot_discount']:.4f}", "4Y spot rate"),
    (c3, "Std Error",           f"${result['std_err']:.4f}",             "MC uncertainty"),
    (c4, "Paths ITM",           f"{result['pct_itm']:.1f}%",             "in the money"),
]:
    with col:
        st.markdown(f"""<div class="result-box">
            <div class="result-label">{label}</div>
            <div class="result-value">{val}</div>
            <div class="result-label" style="margin-top:0.3rem">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

zcb_dist    = np.array(result["zcb_dist"])
payoff_dist = np.array(result["payoff_dist"])
pos_payoffs = payoff_dist[payoff_dist > 0]

fig = make_subplots(rows=1, cols=2,
                    subplot_titles=["Bond Price Distribution at t=4y",
                                    f"Positive Payoffs ({result['pct_itm']:.1f}% of paths)"])

fig.add_trace(go.Histogram(x=zcb_dist, nbinsx=80,
                           marker_color="#a78bfa", opacity=0.85), row=1, col=1)
fig.add_vline(x=K_s, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"K = ${K_s}", row=1, col=1)

fig.add_trace(go.Histogram(x=pos_payoffs, nbinsx=60,
                           marker_color="#34d399", opacity=0.85), row=1, col=2)

fig.update_layout(
    height=420, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11), showlegend=False,
    margin=dict(l=40, r=40, t=50, b=40)
)
fig.update_xaxes(gridcolor="#1a1a2a")
fig.update_yaxes(gridcolor="#1a1a2a")
st.plotly_chart(fig, use_container_width=True)
