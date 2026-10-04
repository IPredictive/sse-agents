import numpy as np
import pandas as pd
from .base import Agent, Prediction
def _rsi(close,n=14):
    d=close.diff(); gain=d.clip(lower=0).rolling(n).mean(); loss=(-d.clip(upper=0)).rolling(n).mean(); rs=gain/loss.replace(0,np.nan); return 100-100/(1+rs)
class TechnicalAgent(Agent):
    name="technical"
    def predict(self,df,context=None):
        if len(df)<40:return None
        c=df.close.astype(float); ma5=c.rolling(5).mean().iloc[-1]; ma20=c.rolling(20).mean().iloc[-1]
        ema12=c.ewm(span=12,adjust=False).mean(); ema26=c.ewm(span=26,adjust=False).mean(); macd=ema12-ema26; hist=(macd-macd.ewm(span=9,adjust=False).mean()).iloc[-1]; rsi=_rsi(c).iloc[-1]
        score=0; notes=[]
        if ma5>ma20:score+=1;notes.append("MA5>MA20")
        else:score-=1;notes.append("MA5<MA20")
        if hist>0:score+=1;notes.append("MACD柱为正")
        else:score-=1;notes.append("MACD柱为负")
        if rsi<30:score+=1;notes.append(f"RSI={rsi:.0f}超卖")
        elif rsi>70:score-=1;notes.append(f"RSI={rsi:.0f}超买")
        else:notes.append(f"RSI={rsi:.0f}中性")
        return Prediction(float(np.clip(.5+.035*score,.40,.60)),"；".join(notes),.55+.08*abs(score))
