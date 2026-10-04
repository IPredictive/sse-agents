from .base import Agent, Prediction
from .quant import clamp, confidence_from_score, direction_text, title_sentiment

class SentimentAgent(Agent):
    name="sentiment"
    def predict(self,df,context=None):
        titles=(context or {}).get("news_titles",[])
        if not titles:return Prediction(0.5,"暂无新闻数据，情绪保持中性",0.35)
        s,e,n=title_sentiment(titles[:20])
        p=clamp(0.5+0.34*s,0.12,0.88)
        conf=confidence_from_score(s*2.0,e)
        return Prediction(p,f"读取{n}条财经标题；新闻情绪{direction_text(p)}，综合情绪分={s:+.2f}",conf)

class MacroAgent(Agent):
    name="macro"
    def predict(self,df,context=None):
        titles=(context or {}).get("macro_titles",[])
        if not titles:return Prediction(0.5,"暂无宏观政策新闻，宏观判断保持中性",0.35)
        s,e,n=title_sentiment(titles[:20])
        # Macro headlines are less reactive than daily sentiment.
        p=clamp(0.5+0.30*s,0.15,0.85)
        conf=confidence_from_score(s*1.7,e)
        return Prediction(p,f"读取{n}条宏观/政策标题；政策环境{direction_text(p)}，政策情绪分={s:+.2f}",conf)
