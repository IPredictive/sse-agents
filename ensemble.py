from agents.ai import call_llm
from agents.base import Prediction

WEIGHTS={"technical":1.0,"flow":1.0,"macro":1.1,"sentiment":1.0,"overseas":0.9}

def combine(preds,context=None):
    if not preds:return None
    ws={k:WEIGHTS.get(k,1.0) for k in preds}
    total=sum(ws.values())
    base_prob=sum(preds[k].prob_up*ws[k] for k in preds)/total
    base_conf=sum(preds[k].confidence*ws[k] for k in preds)/total
    payload={k:{"prob_up":round(v.prob_up,4),"confidence":round(v.confidence,4),"reason":v.reason} for k,v in preds.items()}
    out=call_llm("Chief Analyst（首席策略分析师）","审阅五位分析师的独立结论，识别分歧、判断哪些证据更可靠，给出最终的上证指数下一交易日上涨概率与信心。不要机械平均。",payload)
    if out:
        p,conf,reason=out
        return Prediction(p,"Chief Analyst："+reason,conf)
    why="；".join(f"{k}:{preds[k].prob_up:.1%}" for k in preds)
    return Prediction(float(base_prob),f"五位分析师加权汇总：{why}",float(base_conf))
