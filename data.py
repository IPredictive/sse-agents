import numpy as np,pandas as pd
def fetch_sse():
    import akshare as ak
    df=ak.stock_zh_index_daily(symbol="sh000001");df.date=pd.to_datetime(df.date).dt.strftime("%Y-%m-%d");return df[["date","open","high","low","close","volume"]].tail(1200)
def make_demo(n=400,seed=7):
    rng=np.random.default_rng(seed);dates=pd.bdate_range(end=pd.Timestamp.today().normalize(),periods=n+5)[-n:];close=3000*np.exp(np.cumsum(rng.normal(0,.01,n)));op=close*(1+rng.normal(0,.002,n));return pd.DataFrame({"date":dates.strftime("%Y-%m-%d"),"open":op,"high":np.maximum(op,close)*1.003,"low":np.minimum(op,close)*.997,"close":close,"volume":rng.integers(2e8,5e8,n)})
