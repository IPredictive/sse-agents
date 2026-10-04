import numpy as np
from context import llm_news_score
from .base import Agent, Prediction
POS=["利好","上涨","增长","降准","降息","支持","提振","回暖","反弹","突破","改善","放松","刺激","强劲"]
NEG=["利空","下跌","下降","收紧","加息","风险","承压","回落","跌破","恶化","监管","制裁","通胀"]
def score_titles(titles):return sum(sum(t.count(x) for x in POS)-sum(t.count(x) for x in NEG) for t in titles)
class SentimentAgent(Agent):
    name="sentiment"
    def predict(self,df,context=None):
        t=(context or {}).get("news_titles",[])
        if not t:return None
        llm=llm_news_score(t,"市场情绪");
        if llm:
            p,r=llm; return Prediction(p,"LLM："+r,.65)
        s=score_titles(t);return Prediction(float(np.clip(.5+.025*s,.35,.65)),f"读取{len(t)}条财经标题，关键词情绪分={s:+d}",.50+.03*min(5,abs(s)))
class MacroAgent(Agent):
    name="macro"
    def predict(self,df,context=None):
        t=(context or {}).get("macro_titles",[])
        if not t:return None
        llm=llm_news_score(t,"宏观政策");
        if llm:
            p,r=llm; return Prediction(p,"LLM："+r,.65)
        s=score_titles(t);return Prediction(float(np.clip(.5+.03*s,.35,.65)),f"读取{len(t)}条宏观/政策标题，政策情绪分={s:+d}",.50+.04*min(4,abs(s)))
