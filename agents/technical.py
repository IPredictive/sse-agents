import pandas as pd
from .ai import call_llm
from .base import Agent, Prediction

class TechnicalAgent(Agent):
    name="technical"
    def predict(self,df,context=None):
        if len(df)<40:return None
        c=df.close.astype(float)
        ma5=float(c.rolling(5).mean().iloc[-1]); ma20=float(c.rolling(20).mean().iloc[-1])
        ema12=c.ewm(span=12,adjust=False).mean(); ema26=c.ewm(span=26,adjust=False).mean()
        macd=ema12-ema26; hist=float((macd-macd.ewm(span=9,adjust=False).mean()).iloc[-1])
        d=c.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean()
        rsi=float((100-100/(1+gain/loss.replace(0,float("nan")))).iloc[-1])
        payload={"latest_close":float(c.iloc[-1]),"ma5":ma5,"ma20":ma20,"macd_hist":hist,"rsi":rsi,
                 "returns_5d":float(c.pct_change(5).iloc[-1]),"returns_20d":float(c.pct_change(20).iloc[-1])}
        out=call_llm("技术分析师","综合趋势、均线、MACD、RSI和近期动量，判断下一交易日上涨概率。",payload)
        if out:
            p,conf,reason=out; return Prediction(p,"AI："+reason,conf)
        return Prediction(0.5,"AI未配置，技术分析暂不可用",0.0)
