import pandas as pd
from .ai import call_llm
from .base import Agent, Prediction

class FlowAgent(Agent):
    name="flow"
    def predict(self,df,context=None):
        if len(df)<30:return None
        c=df.close.astype(float); v=df.volume.astype(float); ret=c.pct_change()
        payload={"latest_close":float(c.iloc[-1]),"volume_ratio_20d":float(v.iloc[-1]/v.rolling(20).mean().iloc[-1]),
                 "return_5d":float(c.pct_change(5).iloc[-1]),"return_20d":float(c.pct_change(20).iloc[-1]),
                 "avg_return_5d":float(ret.tail(5).mean())}
        out=call_llm("资金流与量价分析师","分析成交量、量价关系和短中期动量，判断下一交易日上涨概率。",payload)
        if out:
            p,conf,reason=out; return Prediction(p,"AI："+reason,conf)
        return Prediction(0.5,"AI未配置，资金流分析暂不可用",0.0)
