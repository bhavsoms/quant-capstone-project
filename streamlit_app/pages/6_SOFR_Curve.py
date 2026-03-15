import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_sofr_curve
import numpy as np

st.set_page_config(page_title="II(a) SOFR Curve", page_icon="📈", layout="wide")

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

st.markdown('<div class="page-title">Part II(a) — SOFR Yield Curve</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
We fetch the SOFR overnight rate from FRED and build a term structure using linear interpolation:<br><br>
<b>r(t) = r(t₁) + (t − t₁)/(t₂ − t₁) · (r(t₂) − r(t₁))</b><br><br>
Representative spreads are added above the overnight rate to construct
the full curve across tenors. This is simpler than cubic spline or Nelson-Siegel
but sufficient for semi-annual cash flow discounting.
</div>
""", unsafe_allow_html=True)

with st.spinner("Fetching SOFR data..."):
    result = get_sofr_curve()

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="result-box">
        <div class="result-label">SOFR Overnight</div>
        <div class="result-value">{result['sofr_overnight']*100:.4f}%</div>
        <div class="result-label">live from FRED</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="result-box">
        <div class="result-label">5Y Discount Factor</div>
        <div class="result-value">{result['query_disc'][8]:.6f}</div>
        <div class="result-label">exp(−r·T)</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

fig = make_subplots(rows=1, cols=2,
                    subplot_titles=["SOFR Yield Curve (Linear Interpolation)",
                                    "SOFR Discount Factors"])

fig.add_trace(go.Scatter(x=result["fine_times"], y=np.array(result["fine_rates"])*100,
                         mode="lines", line=dict(color="#a78bfa", width=2),
                         name="Interpolated"), row=1, col=1)
fig.add_trace(go.Scatter(x=result["tenors"], y=np.array(result["tenor_rates"])*100,
                         mode="markers", marker=dict(color="#f59e0b", size=8),
                         name="SOFR tenors"), row=1, col=1)

fig.add_trace(go.Scatter(x=result["fine_times"], y=result["fine_disc"],
                         mode="lines", line=dict(color="#a78bfa", width=2),
                         showlegend=False), row=1, col=2)
fig.add_trace(go.Scatter(x=result["query_times"], y=result["query_disc"],
                         mode="markers", marker=dict(color="#f59e0b", size=6),
                         name="Semi-annual points"), row=1, col=2)

fig.update_layout(
    height=420, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11),
    margin=dict(l=40, r=40, t=50, b=40)
)
fig.update_xaxes(title_text="Maturity (years)", gridcolor="#1a1a2a")
fig.update_yaxes(gridcolor="#1a1a2a")
fig.update_yaxes(title_text="Rate (%)", row=1, col=1)
fig.update_yaxes(title_text="Discount Factor", row=1, col=2)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Discount Curve Table")
import pandas as pd
df = pd.DataFrame({
    "Tenor": [f"{t:.1f}y" for t in result["query_times"][:10]],
    "Rate (%)": [f"{r*100:.4f}%" for r in result["query_rates"][:10]],
    "Discount Factor": [f"{d:.6f}" for d in result["query_disc"][:10]]
})
st.dataframe(df, use_container_width=True, hide_index=True)
