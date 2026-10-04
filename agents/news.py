from .ai import call_llm
from .base import Agent, Prediction

class SentimentAgent(Agent):
    name="sentiment"
    def predict(self,df,context=None):
        titles=(context or {}).get("news_titles",[])
        if not titles:return None
        out=call_llm("A股新闻与市场情绪分析师","逐条判断新闻对上证指数的潜在影响，综合市场情绪、事件重要性和方向性。",titles[:12])
        if out:
            p,conf,reason=out; return Prediction(p,"AI："+reason,conf)
        return Prediction(0.5,"AI未配置，新闻情绪分析暂不可用",0.0)

class MacroAgent(Agent):
    name="macro"
    def predict(self,df,context=None):
        titles=(context or {}).get("macro_titles",[])
        if not titles:return None
        out=call_llm("宏观政策分析师","分析央行、财政、监管和宏观经济政策新闻对下一交易日上证指数的影响。",titles[:12])
        if out:
            p,conf,reason=out; return Prediction(p,"AI："+reason,conf)
        return Prediction(0.5,"AI未配置，宏观政策分析暂不可用",0.0)
