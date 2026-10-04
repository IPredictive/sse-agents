from agents.base import Prediction
from agents.quant import clamp, confidence_from_score, direction_text
from db import load_scored

BASE_WEIGHTS={"technical":1.00,"flow":1.00,"macro":1.10,"sentiment":0.95,"overseas":0.90}

def adaptive_weights(preds):
    weights={}
    try:
        scored=load_scored()
        for name in preds:
            x=scored[scored.agent==name].tail(60)
            if len(x)<8:
                weights[name]=BASE_WEIGHTS.get(name,1.0)
                continue
            accuracy=float(x.correct.mean())
            brier=float(x.brier.mean())
            # Accuracy and probability calibration jointly adjust the prior.
            skill=0.65*accuracy+0.35*(1.0-min(1.0,brier/0.25))
            weights[name]=BASE_WEIGHTS.get(name,1.0)*(0.75+0.85*clamp(skill,0.0,1.0))
    except Exception:
        weights={name:BASE_WEIGHTS.get(name,1.0) for name in preds}
    return weights

def combine(preds,context=None):
    if not preds:return None
    ws=adaptive_weights(preds)
    total=sum(ws.values())
    base_prob=sum(preds[k].prob_up*ws[k] for k in preds)/total
    base_conf=sum(preds[k].confidence*ws[k] for k in preds)/total
    # Reward agreement, penalize unresolved disagreement.
    spread=max(v.prob_up for v in preds.values())-min(v.prob_up for v in preds.values())
    agreement=max(0.0,1.0-spread/0.55)
    conf=clamp(0.72*base_conf+0.28*(0.50+0.42*agreement))
    # Small regime-aware correction: extreme disagreement is kept near neutral.
    if spread>0.55:
        base_prob=0.5+0.82*(base_prob-0.5)
    elif spread>0.35:
        base_prob=0.5+0.92*(base_prob-0.5)
    why="；".join(f"{k}:{preds[k].prob_up:.1%}(权重{ws[k]:.2f})" for k in preds)
    reason=f"动态加权汇总：{why}；分析师分歧={spread:.1%}；综合判断{direction_text(base_prob)}"
    return Prediction(clamp(base_prob,0.08,0.92),reason,conf)
