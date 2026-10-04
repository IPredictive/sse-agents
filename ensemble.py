from agents.base import Prediction

# 初始等权；积累战绩后可按各智能体的 Brier score 调整
WEIGHTS: dict[str, float] = {}


def combine(preds: dict[str, Prediction]) -> Prediction | None:
    if not preds:
        return None
    ws = {k: WEIGHTS.get(k, 1.0) for k in preds}
    total = sum(ws.values())
    prob = sum(preds[k].prob_up * ws[k] for k in preds) / total
    return Prediction(prob, f"综合 {len(preds)} 个智能体：{', '.join(preds)}")
