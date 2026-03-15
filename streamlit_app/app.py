import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vasicek.api import get_all_results, get_calibration

st.set_page_config(
    page_title="Quant Capstone | Vasicek Model",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8e8;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem;
    color: #f0f0f0;
    line-height: 1.15;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-family: 'Inter', sans-serif;
    font-weight: 300;
    font-size: 1.1rem;
    color: #888;
    margin-bottom: 2rem;
}
.sde-box {
    background: #12121a;
    border: 1px solid #2a2a3a;
    border-radius: 12px;
    padding: 1.4rem 2rem;
    font-family: 'DM Mono', monospace;
    font-size: 1.3rem;
    color: #a78bfa;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: #12121a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.metric-label {
    font-size: 0.75rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-family: 'DM Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #a78bfa;
}
.metric-sub {
    font-size: 0.72rem;
    color: #555;
    margin-top: 0.2rem;
}
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: #f0f0f0;
    margin: 2rem 0 1rem 0;
}
.chain-box {
    background: #12121a;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    transition: border-color 0.2s;
}
.chain-box:hover { border-color: #a78bfa; }
.chain-label {
    font-size: 0.7rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.chain-title {
    font-size: 0.95rem;
    font-weight: 500;
    color: #e8e8e8;
    margin: 0.3rem 0;
}
.tag {
    display: inline-block;
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.72rem;
    color: #a78bfa;
    margin: 0.2rem;
}
.footer-ref {
    font-size: 0.78rem;
    color: #444;
    border-top: 1px solid #1a1a1a;
    padding-top: 1.5rem;
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Vasicek Short Rate Model</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Indian Institute of Quantitative Finance · Capstone Project · Fixed Income Derivatives</div>', unsafe_allow_html=True)
st.markdown('<div class="sde-box">dr(t) = a(b − r(t)) dt + σ dZ(t)</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col2:
    st.link_button("📓 Open Notebook", "https://colab.research.google.com/drive/1JmOfFefPCapDmrGuyC2BGrbnmXGjfryH")
    st.link_button("🐙 View on GitHub", "https://github.com/bhavsoms/quant-capstone-project")

# ── Live Results ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Live Results</div>', unsafe_allow_html=True)

with st.spinner("Fetching live FED data and computing..."):
    results = get_all_results()
    cal     = get_calibration()

c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
metrics = [
    (c1, "Mean Reversion a",   f"{results['a']:.4f}",        "speed"),
    (c2, "Long-run Mean b",    f"{results['b']*100:.2f}%",   "equilibrium"),
    (c3, "Volatility σ",       f"{results['sigma']:.4f}",    "short rate vol"),
    (c4, "r(0) FED Rate",      f"{results['r0']*100:.2f}%",  "current"),
    (c5, "ZCB Z(0,5)",         f"${results['zcb_5y']:.4f}",  "analytical"),
    (c6, "Swap Rate",          f"{results['swap_rate']*100:.2f}%", "5Y IRS"),
    (c7, "Bond Call",          f"${results['bond_call']:.2f}", "4Y option"),
    (c8, "Swaption",           f"${results['swaption_price']:.4f}", "receiver"),
]
for col, label, value, sub in metrics:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

# ── Interactive SDE ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Interactive Model Explorer</div>', unsafe_allow_html=True)
st.caption("Move the sliders to see how changing parameters affects the short rate paths in real time.")

s1, s2, s3, s4 = st.columns(4)
with s1: a_s    = st.slider("a — mean reversion", 0.05, 2.0, float(results["a"]), 0.05)
with s2: b_s    = st.slider("b — long-run mean %", 1.0, 8.0, float(results["b"]*100), 0.1)
with s3: sig_s  = st.slider("σ — volatility", 0.001, 0.05, float(results["sigma"]), 0.001)
with s4: r0_s   = st.slider("r(0) — start rate %", 0.5, 8.0, float(results["r0"]*100), 0.1)

import numpy as np
np.random.seed(42)
n_paths, n_steps, T = 30, 252, 5
dt   = T / n_steps
Z    = np.random.randn(n_paths, n_steps)
r    = np.zeros((n_paths, n_steps + 1))
r[:, 0] = r0_s / 100
for t in range(n_steps):
    r[:, t+1] = r[:, t] + a_s*(b_s/100 - r[:, t])*dt + sig_s*np.sqrt(dt)*Z[:, t]
t_grid = np.linspace(0, T, n_steps + 1)

fig = go.Figure()
for i in range(n_paths):
    fig.add_trace(go.Scatter(x=t_grid, y=r[i]*100,
                             mode="lines", line=dict(width=0.8, color="#a78bfa"),
                             opacity=0.25, showlegend=False))
fig.add_hline(y=b_s, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"b = {b_s:.1f}%", annotation_position="right")
fig.add_hline(y=0, line_dash="dot", line_color="#444", line_width=0.8)
fig.update_layout(
    height=340,
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11),
    xaxis=dict(title="Time (years)", gridcolor="#1a1a2a", zeroline=False),
    yaxis=dict(title="Rate (%)", gridcolor="#1a1a2a", zeroline=False),
    margin=dict(l=40, r=40, t=20, b=40)
)
st.plotly_chart(fig, use_container_width=True)

# ── Pricing Chain ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Pricing Chain</div>', unsafe_allow_html=True)
st.caption("Each block is a sub-question in the capstone. Navigate using the sidebar.")

chain = [
    ("Part I(a)", "Calibration",    "Live FED data → a, b, σ"),
    ("Part I(b)", "ZCB Analytical", "Affine formula → Z(0,5)"),
    ("Part I(c)", "Monte Carlo",    "Simulated paths → price"),
    ("Part I(d)", "Swap Rate",      "Fixed leg → par rate"),
    ("Part I(e)", "Bond Option",    "Call on ZCB → $58"),
    ("Part II(a)","SOFR Curve",     "Linear interpolation"),
    ("Part II(b)","Swaption",       "Black's model → $0.39"),
    ("Part II(c)","Numeraire",      "Annuity measure theory"),
]

cols = st.columns(8)
for col, (part, title, desc) in zip(cols, chain):
    with col:
        st.markdown(f"""
        <div class="chain-box">
            <div class="chain-label">{part}</div>
            <div class="chain-title">{title}</div>
            <div class="chain-label" style="font-size:0.65rem;margin-top:0.3rem">{desc}</div>
        </div>""", unsafe_allow_html=True)

# ── Tech Stack ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
tags = ["Python 3", "NumPy", "SciPy", "Pandas", "Plotly", "Streamlit",
        "FRED API", "Vasicek (1977)", "Black's Model", "IIQF Certification"]
st.markdown(" ".join([f'<span class="tag">{t}</span>' for t in tags]),
            unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer-ref">
Brigo & Mercurio (2006) · Glasserman (2004) · Hull (2022) · Tuckman & Serrat (2011)<br>
Data: Federal Reserve Economic Data (FRED) · Built with Streamlit · Deployed on Streamlit Community Cloud
</div>
""", unsafe_allow_html=True)
