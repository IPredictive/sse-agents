import numpy as np,pandas as pd

def _clean(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    cols = ["date","open","high","low","close","volume"]
    if not all(c in df.columns for c in cols):
        return pd.DataFrame()
    for c in cols[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[cols].dropna(subset=["date","close"]).sort_values("date").drop_duplicates("date")

def fetch_sse():
    import akshare as ak
    sources = []
    for name, loader in [
        ("eastmoney", lambda: ak.stock_zh_index_daily_em(
            symbol="sh000001", start_date="19900101", end_date="20500101"
        )),
        ("sina", lambda: ak.stock_zh_index_daily(symbol="sh000001")),
    ]:
        try:
            clean = _clean(loader())
            if not clean.empty:
                sources.append((clean["date"].max(), name, clean))
        except Exception:
            pass

    # Prefer the source with the newest trading date. This prevents a stale
    # upstream feed from freezing the whole analysis at an old market date.
    if sources:
        _, _, df = max(sources, key=lambda x: x[0])
        return df.tail(1200).reset_index(drop=True)

    # Final fallback: Tencent historical index feed.
    try:
        df = ak.stock_zh_index_daily_tx(symbol="sh000001")
        df = df.rename(columns={"amount": "volume"})
        clean = _clean(df)
        if not clean.empty:
            return clean.tail(1200).reset_index(drop=True)
    except Exception:
        pass

    raise RuntimeError("Unable to fetch Shanghai Composite historical data from all configured sources")

def make_demo(n=400,seed=7):
    rng=np.random.default_rng(seed);dates=pd.bdate_range(end=pd.Timestamp.today().normalize(),periods=n+5)[-n:];close=3000*np.exp(np.cumsum(rng.normal(0,.01,n)));op=close*(1+rng.normal(0,.002,n));return pd.DataFrame({"date":dates.strftime("%Y-%m-%d"),"open":op,"high":np.maximum(op,close)*1.003,"low":np.minimum(op,close)*.997,"close":close,"volume":rng.integers(2e8,5e8,n)})
