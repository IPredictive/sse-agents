from agents.base import Prediction
WEIGHTS={}
def combine(preds):
    if not preds:return None
    ws={k:WEIGHTS.get(k,1.) for k in preds};total=sum(ws.values());prob=sum(preds[k].prob_up*ws[k] for k in preds)/total;conf=sum(preds[k].confidence*ws[k] for k in preds)/total;why="；".join(f"{k}:{preds[k].prob_up:.1%}" for k in preds);return Prediction(float(prob),f"综合{len(preds)}个智能体：{why}",float(conf))
