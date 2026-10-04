import numpy as np
from .base import Agent, Prediction
class OverseasAgent(Agent):
    name="overseas"
    def predict(self,df,context=None):
        vals={k:v for k,v in (context or {}).get("overseas",{}).items() if isinstance(v,(int,float)) and np.isfinite(v)}
        if not vals:return None
        score=0;notes=[]
        for k,v in vals.items():
            if v>.004:score+=1
            elif v<-.004:score-=1
            notes.append(f"{k}{v:+.2%}")
        return Prediction(float(np.clip(.5+.025*score,.42,.58)),"；".join(notes),.48+.05*min(3,abs(score)))
