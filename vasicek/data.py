import pandas as pd
import numpy as np


def fetch_fed_rates(start="2000-01-01", end="2024-12-31"):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
    df  = pd.read_csv(url, header=0)
    df.columns = ["date", "rate"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[df["rate"].astype(str).str.strip() != "."].copy()
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce") / 100
    df = df.dropna(subset=["rate"])
    df = df[(df["date"] >= start) & (df["date"] <= end)]
    return df.reset_index(drop=True)


def fetch_sofr_overnight():
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SOFR"
        df  = pd.read_csv(url, header=0)
        df.columns = ["date", "rate"]
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
        return float(df["rate"].dropna().iloc[-1] / 100)
    except Exception:
        return 0.053


def build_sofr_curve(sofr_on: float):
    tenors  = np.array([0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
    spreads = np.array([0.000, 0.001, 0.003, 0.007, 0.011, 0.016, 0.019, 0.022])
    return tenors, sofr_on + spreads


def interpolate_curve(tenors, rates, query_times):
    r     = np.interp(query_times, tenors, rates)
    discs = np.exp(-r * query_times)
    return r, discs
