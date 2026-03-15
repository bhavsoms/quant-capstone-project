import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_calibration, get_zcb_mc
from vasicek.core import zcb_analytical
import numpy as np

st.set_page_config(page_title="I(c) Monte Carlo", page_icon="🎲", layout="wide")

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

st.markdown('<div class="page-title">Part I(c) — Monte Carlo ZCB Pricing</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
We simulate N paths of the short rate using Euler discretization:<br><br>
<b>r(t+Δt) = r(t) + a(b−r(t))Δt + σ√Δt·Z</b> where Z ~ N(0,1)<br><br>
ZCB price = E[exp(−∫r dt)] ≈ mean of discounted paths<br><br>
<b>Antithetic Variates:</b> For every path Z we also simulate −Z. Since Cov(f(Z), f(−Z)) &lt; 0,
the average has strictly lower variance than the standard estimator.
</div>
""", unsafe_allow_html=True)

cal = get_calibration()

st.sidebar.header("Parameters")
r0_s     = st.sidebar.slider("r(0) %",   0.5, 8.0,  4.0, 0.1) / 100
n_paths  = st.sidebar.select_slider("Number of paths", [1000, 5000, 10000, 20000], 10000)
antith   = st.sidebar.checkbox("Antithetic Variates", value=True)

a, b, sigma = cal["a"], cal["b"], cal["sigma"]

with st.spinner("Running simulation..."):
    result = get_zcb_mc(r0=r0_s, n_paths=n_paths)
    analytical = zcb_analytical(r0_s, a, b, sigma, 5.0)

c1, c2, c3 = st.columns(3)
for col, label, val, sub in [
    (c1, "Analytical Price",     f"${analytical:.6f}",         "exact formula"),
    (c2, "MC Price",             f"${result['price']:.6f}",    f"±{result['std_err']:.6f}"),
    (c3, "Variance Reduction",   "Antithetic Variates",        "paired Z and −Z paths"),
]:
    with col:
        st.markdown(f"""<div class="result-box">
            <div class="result-label">{label}</div>
            <div class="result-value">{val}</div>
            <div class="result-label" style="margin-top:0.3rem">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

np.random.seed(42)
n_plot, n_steps, T = 60, 252, 5.0
dt  = T / n_steps
Z   = np.random.randn(n_plot, n_steps)
r   = np.zeros((n_plot, n_steps + 1))
r[:, 0] = r0_s
for t in range(n_steps):
    r[:, t+1] = r[:, t] + a*(b - r[:, t])*dt + sigma*np.sqrt(dt)*Z[:, t]
t_grid = np.linspace(0, T, n_steps + 1)

disc = np.array(result["discount_dist"])

fig = make_subplots(rows=1, cols=2,
                    subplot_titles=["Simulated Rate Paths", "Discount Factor Distribution"])

for i in range(n_plot):
    fig.add_trace(go.Scatter(x=t_grid, y=r[i]*100, mode="lines",
                             line=dict(width=0.7, color="#a78bfa"),
                             opacity=0.2, showlegend=False), row=1, col=1)
fig.add_hline(y=b*100, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"b={b*100:.1f}%", row=1, col=1)

fig.add_trace(go.Histogram(x=disc, nbinsx=80,
                           marker_color="#a78bfa", opacity=0.8,
                           name="Discount factors"), row=1, col=2)
fig.add_vline(x=analytical, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"Analytical: {analytical:.4f}", row=1, col=2)
fig.add_vline(x=result["price"], line_dash="dot", line_color="#34d399",
              annotation_text=f"MC: {result['price']:.4f}", row=1, col=2)

fig.update_layout(
    height=420, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11), showlegend=False,
    margin=dict(l=40, r=40, t=50, b=40)
)
fig.update_xaxes(gridcolor="#1a1a2a")
fig.update_yaxes(gridcolor="#1a1a2a")
st.plotly_chart(fig, use_container_width=True)
