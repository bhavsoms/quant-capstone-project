from vasicek.core import (calibrate, zcb_analytical, zcb_curve,
                           zcb_monte_carlo, swap_rate,
                           bond_option, sofr_curve, swaption)
import numpy as np

_cache = {}


def get_calibration(force_refresh=False):
    if "calibration" not in _cache or force_refresh:
        _cache["calibration"] = calibrate()
    return _cache["calibration"]


def get_zcb_curve(r0=None, a=None, b=None, sigma=None):
    cal   = get_calibration()
    r0    = r0    or cal["r0"]
    a     = a     or cal["a"]
    b     = b     or cal["b"]
    sigma = sigma or cal["sigma"]
    mats  = list(np.round(np.linspace(0.25, 10, 80), 4))
    return zcb_curve(r0, a, b, sigma, mats)


def get_zcb_mc(r0=0.04, a=None, b=None, sigma=None, n_paths=20000):
    cal   = get_calibration()
    a     = a     or cal["a"]
    b     = b     or cal["b"]
    sigma = sigma or cal["sigma"]
    return zcb_monte_carlo(r0, a, b, sigma, T=5.0, n_paths=n_paths)


def get_swap_rate(r0=None, a=None, b=None, sigma=None, N=5):
    cal   = get_calibration()
    r0    = r0    or cal["r0"]
    a     = a     or cal["a"]
    b     = b     or cal["b"]
    sigma = sigma or cal["sigma"]
    return swap_rate(r0, a, b, sigma, N=N)


def get_bond_option(r0=None, a=None, b=None, sigma=None,
                    K=900.0, face=1000.0):
    cal   = get_calibration()
    r0    = r0    or cal["r0"]
    a     = a     or cal["a"]
    b     = b     or cal["b"]
    sigma = sigma or cal["sigma"]
    return bond_option(r0, a, b, sigma, K=K, face=face)


def get_sofr_curve():
    if "sofr" not in _cache:
        _cache["sofr"] = sofr_curve()
    return _cache["sofr"]


def get_swaption(K=0.045, sigma_vol=0.15, T_opt=2.0, notional=100.0):
    return swaption(K=K, sigma_vol=sigma_vol, T_opt=T_opt, notional=notional)


def get_all_results():
    cal  = get_calibration()
    zcb  = zcb_analytical(cal["r0"], cal["a"], cal["b"], cal["sigma"], 5.0)
    mc   = get_zcb_mc()
    sw   = get_swap_rate()
    opt  = get_bond_option()
    sopt = get_swaption()
    return {
        "a":              cal["a"],
        "b":              cal["b"],
        "sigma":          cal["sigma"],
        "r0":             cal["r0"],
        "zcb_5y":         zcb,
        "mc_price":       mc["price"],
        "mc_std_err":     mc["std_err"],
        "swap_rate":      sw["swap_rate"],
        "bond_call":      opt["price_path_discount"],
        "swaption_price": sopt["price"],
        "sofr_overnight": sopt["S_fwd"]
    }
