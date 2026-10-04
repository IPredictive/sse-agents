import numpy as np
from .ai import call_llm
from .base import Agent, Prediction

class OverseasAgent(Agent):
    name="overseas"
    def predict(self,df,context=None):
        vals={k:v for k,v in (context or {}).get("overseas",{}).items() if isinstance(v,(int,float)) and np.isfinite(v)}
        if not vals:return None
        out=call_llm("全球市场分析师","结合海外股指、汇率等外部市场变量，判断其对下一交易日上证指数的影响。",vals)
        if out:
            p,conf,reason=out; return Prediction(p,"AI："+reason,conf)
        return Prediction(0.5,"AI未配置，海外市场分析暂不可用",0.0)
