import numpy as np
from vasicek.data import (fetch_fed_rates, fetch_sofr_overnight,
                          build_sofr_curve, interpolate_curve)


def calibrate(start="2000-01-01", end="2024-12-31"):
    df      = fetch_fed_rates(start, end)
    df_stat = df[df["date"] <= "2008-12-31"].copy()

    def _ols(rates, dt=1/12):
        r         = rates.values
        dr        = np.diff(r)
        r_lag     = r[:-1]
        X         = np.column_stack([np.ones(len(dr)), r_lag])
        coeffs    = np.linalg.lstsq(X, dr, rcond=None)[0]
        a_hat     = -coeffs[1] / dt
        b_hat     = coeffs[0] / (a_hat * dt) if abs(a_hat) > 1e-8 else np.nan
        resid     = dr - (coeffs[0] + coeffs[1] * r_lag)
        sigma_hat = float(np.std(resid, ddof=1) / np.sqrt(dt))
        return float(a_hat), float(b_hat), sigma_hat

    a_raw, b_raw, _ = _ols(df_stat["rate"])
    _, _, sigma     = _ols(df["rate"])

    a_ok = 0.01 < a_raw < 5.0
    b_ok = 0.005 < b_raw < 0.15

    if a_ok and b_ok:
        a, b   = a_raw, b_raw
        method = "OLS clean"
    else:
        a      = float(np.clip(a_raw, 0.15, 2.0))
        b      = float(np.clip(b_raw, 0.02, 0.07))
        method = "practitioner floor applied"

    r0 = float(df["rate"].iloc[-1])

    return {
        "a": a, "b": b, "sigma": sigma, "r0": r0,
        "method": method,
        "n_obs": len(df),
        "dates": {"start": str(df["date"].iloc[0].date()),
                  "end":   str(df["date"].iloc[-1].date())},
        "fed_history": {
            "dates": df["date"].dt.strftime("%Y-%m-%d").tolist(),
            "rates": (df["rate"] * 100).round(4).tolist()
        }
    }


def zcb_analytical(r0, a, b, sigma, T, face=1.0):
    B = (1 - np.exp(-a * T)) / a
    A = (b - sigma**2 / (2*a**2)) * (B - T) - (sigma**2 * B**2) / (4*a)
    return float(face * np.exp(A - B * r0))


def zcb_curve(r0, a, b, sigma, maturities):
    prices = [zcb_analytical(r0, a, b, sigma, T) for T in maturities]
    return {"maturities": maturities, "prices": prices}


def zcb_monte_carlo(r0, a, b, sigma, T=5.0,
                    n_steps=252, n_paths=20000, face=1.0):
    dt   = T / n_steps
    half = n_paths // 2
    Z    = np.concatenate([np.random.randn(half, n_steps),
                           -np.random.randn(half, n_steps)], axis=0)
    r        = np.zeros((n_paths, n_steps + 1))
    r[:, 0]  = r0
    for t in range(n_steps):
        r[:, t+1] = r[:, t] + a*(b - r[:, t])*dt + sigma*np.sqrt(dt)*Z[:, t]
    disc    = np.exp(-np.sum(r[:, :-1], axis=1) * dt) * face
    price   = float(np.mean(disc))
    std_err = float(np.std(disc, ddof=1) / np.sqrt(n_paths))
    return {
        "price":         price,
        "std_err":       std_err,
        "n_paths":       n_paths,
        "discount_dist": np.round(disc, 6).tolist(),
        "sample_paths":  r[:50].tolist(),
        "t_grid":        np.linspace(0, T, n_steps + 1).tolist()
    }


def swap_rate(r0, a, b, sigma, N=5, dt=1.0):
    times = np.arange(dt, N + dt, dt)
    zcbs  = np.array([zcb_analytical(r0, a, b, sigma, float(t)) for t in times])
    numer = 1 - zcbs[-1]
    denom = float(np.sum(zcbs) * dt)
    rate  = float(numer / denom)
    return {
        "swap_rate":      rate,
        "numerator":      float(numer),
        "denominator":    denom,
        "payment_times":  times.tolist(),
        "zcb_prices":     np.round(zcbs, 6).tolist()
    }


def bond_option(r0, a, b, sigma, t_opt=4.0, T_bond=5.0,
                K=900.0, face=1000.0, n_steps=252, n_paths=40000):
    dt   = t_opt / n_steps
    half = n_paths // 2
    Z    = np.concatenate([np.random.randn(half, n_steps),
                           -np.random.randn(half, n_steps)], axis=0)
    r        = np.zeros((n_paths, n_steps + 1))
    r[:, 0]  = r0
    for step in range(n_steps):
        r[:, step+1] = (r[:, step] + a*(b - r[:, step])*dt
                        + sigma*np.sqrt(dt)*Z[:, step])
    r_t      = r[:, -1]
    disc_0_t = np.exp(-np.sum(r[:, :-1], axis=1) * dt)
    tau      = T_bond - t_opt
    B_tau    = (1 - np.exp(-a * tau)) / a
    A_tau    = ((b - sigma**2/(2*a**2))*(B_tau - tau)
                - (sigma**2 * B_tau**2)/(4*a))
    zcb_t    = face * np.exp(A_tau - B_tau * r_t)
    payoff   = np.maximum(zcb_t - K, 0)
    opt_path = float(np.mean(disc_0_t * payoff))
    se       = float(np.std(disc_0_t * payoff, ddof=1) / np.sqrt(n_paths))
    z4       = zcb_analytical(r0, a, b, sigma, t_opt)
    r4_spot  = -np.log(z4) / t_opt
    opt_spot = float(np.exp(-r4_spot * t_opt) * np.mean(payoff))
    return {
        "price_path_discount": opt_path,
        "price_spot_discount": opt_spot,
        "std_err":             se,
        "pct_itm":             float(np.mean(payoff > 0) * 100),
        "zcb_dist":            np.round(zcb_t[:2000], 2).tolist(),
        "payoff_dist":         np.round(payoff[:2000], 2).tolist()
    }


def sofr_curve():
    sofr_on        = fetch_sofr_overnight()
    tenors, rates  = build_sofr_curve(sofr_on)
    query_times    = np.arange(0.5, 10.5, 0.5)
    r_q, disc_q    = interpolate_curve(tenors, rates, query_times)
    t_fine         = np.linspace(0.1, 10, 200)
    r_fine, d_fine = interpolate_curve(tenors, rates, t_fine)
    return {
        "sofr_overnight": sofr_on,
        "tenors":         tenors.tolist(),
        "tenor_rates":    rates.tolist(),
        "query_times":    query_times.tolist(),
        "query_rates":    np.round(r_q, 6).tolist(),
        "query_disc":     np.round(disc_q, 6).tolist(),
        "fine_times":     np.round(t_fine, 4).tolist(),
        "fine_rates":     np.round(r_fine, 6).tolist(),
        "fine_disc":      np.round(d_fine, 6).tolist()
    }


def swaption(K=0.045, sigma_vol=0.15, T_opt=2.0,
             N_swap=5.0, dt=0.5, notional=100.0):
    from scipy.stats import norm
    sofr_on       = fetch_sofr_overnight()
    tenors, rates = build_sofr_curve(sofr_on)
    swap_times    = np.arange(T_opt + dt, T_opt + N_swap + dt, dt)
    _, disc_swap  = interpolate_curve(tenors, rates, swap_times)
    annuity       = float(np.sum(disc_swap) * dt)
    S             = float((disc_swap[0] - disc_swap[-1]) / annuity)
    d1 = (np.log(S/K) + 0.5*sigma_vol**2*T_opt) / (sigma_vol*np.sqrt(T_opt))
    d2 = d1 - sigma_vol*np.sqrt(T_opt)
    price = float(notional * annuity * (K*norm.cdf(-d2) - S*norm.cdf(-d1)))

    vols_range    = np.linspace(0.05, 0.40, 80).tolist()
    strikes_range = np.linspace(0.01, 0.10, 80).tolist()

    prices_vol = []
    for v in vols_range:
        d1v = (np.log(S/K) + 0.5*v**2*T_opt) / (v*np.sqrt(T_opt))
        d2v = d1v - v*np.sqrt(T_opt)
        prices_vol.append(float(notional * annuity *
                          (K*norm.cdf(-d2v) - S*norm.cdf(-d1v))))

    prices_k = []
    for k in strikes_range:
        d1k = (np.log(S/k) + 0.5*sigma_vol**2*T_opt) / (sigma_vol*np.sqrt(T_opt))
        d2k = d1k - sigma_vol*np.sqrt(T_opt)
        prices_k.append(float(notional * annuity *
                         (k*norm.cdf(-d2k) - S*norm.cdf(-d1k))))

    return {
        "price":          price,
        "S_fwd":          S,
        "annuity":        annuity,
        "d1":             float(d1),
        "d2":             float(d2),
        "K":              K,
        "sigma_vol":      sigma_vol,
        "T_opt":          T_opt,
        "notional":       notional,
        "otm":            S > K,
        "vols_range":     vols_range,
        "prices_vol":     prices_vol,
        "strikes_range":  strikes_range,
        "prices_k":       prices_k
    }
