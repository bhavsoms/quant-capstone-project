import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from vasicek.api import get_swaption
import numpy as np

st.set_page_config(page_title="II(b) Swaption", page_icon="🔀", layout="wide")

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

st.markdown('<div class="page-title">Part II(b) — European Receiver Swaption</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
A receiver swaption gives the holder the right to enter a swap receiving floating and paying fixed K.<br><br>
We use <b>Black's model</b> under the lognormal forward swap rate assumption:<br><br>
<b>V = A(0) · [K·N(−d₂) − S·N(−d₁)]</b><br><br>
where d₁ = (ln(S/K) + ½σ²T) / (σ√T) and d₂ = d₁ − σ√T<br><br>
Note: σ = 15% is a <b>lognormal vol</b> — not normal/Bachelier.
The swaption is out of the money when S(0) &gt; K (receiver pays above-market fixed).
</div>
""", unsafe_allow_html=True)

st.sidebar.header("Parameters")
K_s       = st.sidebar.slider("Strike K %",     1.0,  8.0,  4.5,  0.1) / 100
sigma_s   = st.sidebar.slider("Vol σ %",         5.0, 40.0, 15.0,  0.5) / 100
T_s       = st.sidebar.slider("Option expiry Y", 1.0,  5.0,  2.0,  0.5)
notional  = st.sidebar.slider("Notional $",     10,  500,  100,   10)

result = get_swaption(K=K_s, sigma_vol=sigma_s, T_opt=T_s, notional=float(notional))

otm_label = "OUT OF THE MONEY" if result["otm"] else "IN THE MONEY"
otm_color = "#f59e0b" if result["otm"] else "#34d399"

c1, c2, c3, c4, c5 = st.columns(5)
for col, label, val, sub in [
    (c1, "Swaption Price",      f"${result['price']:.4f}",      otm_label),
    (c2, "Forward Swap Rate",   f"{result['S_fwd']*100:.4f}%",  "S(0)"),
    (c3, "Annuity A(0)",        f"{result['annuity']:.4f}",     "Σ P(0,Ti)·Δt"),
    (c4, "d1",                  f"{result['d1']:.4f}",          "Black's d1"),
    (c5, "d2",                  f"{result['d2']:.4f}",          "Black's d2"),
]:
    with col:
        st.markdown(f"""<div class="result-box">
            <div class="result-label">{label}</div>
            <div class="result-value">{val}</div>
            <div class="result-label" style="margin-top:0.3rem;color:{otm_color if label=='Swaption Price' else '#666'}">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

fig = make_subplots(rows=1, cols=2,
                    subplot_titles=["Swaption Price vs Implied Vol",
                                    "Swaption Price vs Strike"])

fig.add_trace(go.Scatter(x=np.array(result["vols_range"])*100,
                         y=result["prices_vol"],
                         mode="lines", line=dict(color="#a78bfa", width=2),
                         name="Price vs vol"), row=1, col=1)
fig.add_vline(x=sigma_s*100, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"σ={sigma_s*100:.0f}% → ${result['price']:.4f}",
              row=1, col=1)

fig.add_trace(go.Scatter(x=np.array(result["strikes_range"])*100,
                         y=result["prices_k"],
                         mode="lines", line=dict(color="#a78bfa", width=2),
                         name="Price vs strike"), row=1, col=2)
fig.add_vline(x=K_s*100, line_dash="dash", line_color="#f59e0b",
              annotation_text=f"K={K_s*100:.1f}%", row=1, col=2)
fig.add_vline(x=result["S_fwd"]*100, line_dash="dot", line_color="#34d399",
              annotation_text=f"ATM={result['S_fwd']*100:.2f}%", row=1, col=2)

fig.update_layout(
    height=420, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
    font=dict(color="#888", size=11), showlegend=False,
    margin=dict(l=40, r=40, t=50, b=40)
)
fig.update_xaxes(gridcolor="#1a1a2a")
fig.update_yaxes(gridcolor="#1a1a2a")
st.plotly_chart(fig, use_container_width=True)
