"""数据获取：真实数据用 AKShare；--demo 用随机游走数据（仅用于跑通流程）。"""
import numpy as np
import pandas as pd


def fetch_sse() -> pd.DataFrame:
    import akshare as ak

    df = ak.stock_zh_index_daily(symbol="sh000001")  # 上证指数日线
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df[["date", "open", "high", "low", "close", "volume"]].tail(800)


def make_demo(n: int = 400, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n + 5)[-n:]
    close = 3000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * 1.003
    low = np.minimum(open_, close) * 0.997
    vol = rng.integers(2e8, 5e8, n)
    return pd.DataFrame(
        {"date": dates.strftime("%Y-%m-%d"), "open": open_, "high": high,
         "low": low, "close": close, "volume": vol}
    )
