import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import numpy as np

st.set_page_config(page_title="II(c)(d) Numeraire", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { background-color: #0a0a0f; color: #e8e8e8; font-family: 'Inter', sans-serif; }
.page-title { font-size: 2rem; font-weight: 600; color: #f0f0f0; margin-bottom: 0.2rem; }
.theory-box { background: #12121a; border-left: 3px solid #a78bfa; border-radius: 0 8px 8px 0; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; color: #aaa; line-height: 1.7; }
.concept-box { background: #12121a; border: 1px solid #1e1e2e; border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; }
.concept-title { font-size: 1.1rem; font-weight: 600; color: #a78bfa; margin-bottom: 0.5rem; }
.concept-body { font-size: 0.88rem; color: #aaa; line-height: 1.8; }
.highlight { color: #f59e0b; font-weight: 500; }
.green { color: #34d399; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Part II(c)(d) — Numeraire Theory</div>', unsafe_allow_html=True)
st.markdown("""
<div class="theory-box">
A <b>numeraire</b> is any strictly positive asset used as a unit of account.
Choosing the right numeraire simplifies pricing by making the asset price ratio a martingale
under the corresponding measure — eliminating the need to explicitly model discounting.
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["European Swaption — Annuity Numeraire",
                       "Bermudan Swaption — Money Market Numeraire"])

with tab1:
    st.markdown("""
    <div class="concept-box">
        <div class="concept-title">Annuity (Swap) Numeraire</div>
        <div class="concept-body">
        For a European swaption the natural numeraire is the <span class="highlight">annuity factor</span>:<br><br>
        <b>A(t) = Σ Δt · P(t, Tᵢ)</b> for i = 1 to N<br><br>
        Under the annuity measure Q^A, the <span class="highlight">forward swap rate S(t) is a martingale</span>.
        This is precisely what makes Black's formula valid — it prices the swaption as if S follows
        geometric Brownian motion under Q^A:<br><br>
        <b>V = A(0) · E^A[max(K − S(T), 0)]</b><br><br>
        which under Q^A reduces exactly to the Black receiver formula.
        The annuity absorbs all discounting so we only need to model S — clean and elegant.
        </div>
    </div>
    """, unsafe_allow_html=True)

    np.random.seed(42)
    n_paths, T, dt = 5, 2.0, 1/252
    n_steps = int(T / dt)
    S0, sigma = 0.055, 0.15
    t_grid = np.linspace(0, T, n_steps + 1)
    dW = np.random.randn(n_paths, n_steps) * np.sqrt(dt)
    S  = np.zeros((n_paths, n_steps + 1))
    S[:, 0] = S0
    for t in range(n_steps):
        S[:, t+1] = S[:, t] * np.exp(-0.5*sigma**2*dt + sigma*dW[:, t])

    fig = go.Figure()
    for i in range(n_paths):
        fig.add_trace(go.Scatter(x=t_grid, y=S[i]*100,
                                 mode="lines", line=dict(width=1.2, color="#a78bfa"),
                                 opacity=0.6, showlegend=False))
    fig.add_hline(y=S0*100, line_dash="dot", line_color="#666",
                  annotation_text="S(0)")
    fig.add_hline(y=4.5, line_dash="dash", line_color="#f59e0b",
                  annotation_text="K = 4.5%")
    fig.update_layout(
        title="Forward Swap Rate S(t) under Annuity Measure Q^A (GBM paths)",
        height=320, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
        font=dict(color="#888", size=11),
        xaxis=dict(title="Time (years)", gridcolor="#1a1a2a"),
        yaxis=dict(title="Forward Swap Rate (%)", gridcolor="#1a1a2a"),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("""
    <div class="concept-box">
        <div class="concept-title">Rolling Money-Market Numeraire</div>
        <div class="concept-body">
        For a <span class="green">Bermudan swaption</span> the annuity numeraire breaks down
        because the annuity itself changes at each exercise date — there is no single fixed annuity.<br><br>
        The appropriate numeraire is the <span class="green">rolling money-market account</span>:<br><br>
        <b>B(t) = exp(∫₀ᵗ r(s) ds)</b><br><br>
        This is the standard risk-neutral measure Q. Under Q, all traded asset prices
        discounted by B(t) are martingales.<br><br>
        <b>Valuation — Longstaff-Schwartz (LSM) Algorithm:</b><br>
        1. Simulate many short rate paths forward to final maturity<br>
        2. At each exercise date regress continuation value on basis functions of r(t)<br>
        3. Exercise when immediate exercise value exceeds fitted continuation value<br>
        4. Price = average discounted cash flow under the optimal exercise policy
        </div>
    </div>
    """, unsafe_allow_html=True)

    np.random.seed(42)
    a, b, sigma_r, r0 = 0.15, 0.02, 0.0064, 0.0448
    n_paths_b, T_b, dt_b = 8, 7.0, 1/52
    n_steps_b = int(T_b / dt_b)
    t_b = np.linspace(0, T_b, n_steps_b + 1)
    Z_b = np.random.randn(n_paths_b, n_steps_b)
    r_b = np.zeros((n_paths_b, n_steps_b + 1))
    r_b[:, 0] = r0
    for t in range(n_steps_b):
        r_b[:, t+1] = (r_b[:, t] + a*(b - r_b[:, t])*dt_b
                       + sigma_r*np.sqrt(dt_b)*Z_b[:, t])

    exercise_dates = [2.0, 3.0, 4.0, 5.0, 6.0]

    fig2 = go.Figure()
    for i in range(n_paths_b):
        fig2.add_trace(go.Scatter(x=t_b, y=r_b[i]*100,
                                  mode="lines", line=dict(width=1, color="#a78bfa"),
                                  opacity=0.5, showlegend=False))
    for ed in exercise_dates:
        fig2.add_vline(x=ed, line_dash="dash", line_color="#f59e0b",
                       line_width=0.8,
                       annotation_text=f"Exercise {ed:.0f}Y",
                       annotation_font_size=9)
    fig2.update_layout(
        title="Bermudan Swaption — Short Rate Paths with Exercise Dates (LSM)",
        height=320, paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
        font=dict(color="#888", size=11),
        xaxis=dict(title="Time (years)", gridcolor="#1a1a2a"),
        yaxis=dict(title="Short Rate (%)", gridcolor="#1a1a2a"),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    st.plotly_chart(fig2, use_container_width=True)
