from agents.base import Prediction
from agents.quant import clamp, confidence_from_score, direction_text
from db import load_scored

BASE_WEIGHTS={"technical":1.00,"flow":1.00,"macro":1.10,"sentiment":0.95,"overseas":0.90}

def evidence_quality(pred, name, context=None):
    conf=clamp(getattr(pred,"confidence",0.5),0.5,0.92)
    q=0.45+0.75*(conf-0.5)/0.42
    c=context or {}
    if name=="sentiment":
        n=len(c.get("news_items",[]) or [])
        q*=0.75 if n<4 else (0.90 if n<8 else 1.0)
    elif name=="macro":
        n=len(c.get("macro_items",[]) or [])
        q*=0.75 if n<4 else (0.90 if n<8 else 1.0)
    elif name=="overseas":
        q*=0.82 if len(c.get("overseas",{}) or {})<3 else 1.0
    return clamp(q,0.35,1.0)

def stabilize_extreme(p, quality):
    p=float(p); q=clamp(quality,0.35,1.0)
    if abs(p-0.5)<=0.30:return p
    damp=0.45+0.55*q
    return 0.5+(p-0.5)*damp

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
    quality={k:evidence_quality(v,k,context) for k,v in preds.items()}
    adjusted={k:stabilize_extreme(v.prob_up,quality[k]) for k,v in preds.items()}
    for k in ws: ws[k]*=(0.78+0.42*quality[k])
    total=sum(ws.values())
    base_prob=sum(adjusted[k]*ws[k] for k in preds)/total
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
    why="；".join(f"{k}:{adjusted[k]:.1%}(证据{quality[k]:.0%}，权重{ws[k]:.2f})" for k in preds)
    reason=f"动态加权汇总：{why}；分析师分歧={spread:.1%}；综合判断{direction_text(base_prob)}"
    return Prediction(clamp(base_prob,0.08,0.92),reason,conf)
