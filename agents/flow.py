import numpy as np
from .base import Agent, Prediction
class FlowAgent(Agent):
    name="flow"
    def predict(self,df,context=None):
        if len(df)<30:return None
        c=df.close.astype(float);v=df.volume.astype(float);ret=c.pct_change();v20=v.rolling(20).mean().iloc[-1];rv=v.iloc[-1]/v20 if v20 else 1;recent=ret.tail(5).mean();p20=c.pct_change(20).iloc[-1]
        score=0;notes=[f"量比20日={rv:.2f}"]
        if rv>1.15 and recent>0:score+=1;notes.append("放量上涨")
        elif rv>1.15 and recent<0:score-=1;notes.append("放量下跌")
        if p20>.03:score+=1;notes.append("20日动量偏强")
        elif p20<-.03:score-=1;notes.append("20日动量偏弱")
        if recent>.005:score+=1
        elif recent<-.005:score-=1
        return Prediction(float(np.clip(.5+.035*score,.41,.59)),"；".join(notes),.50+.07*abs(score))
