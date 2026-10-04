"""每个交易日收盘后运行：拉数据 → 跑 5 个智能体 → 写入预测。

python run_daily.py                          # 真实数据
python run_daily.py --demo --backfill 60     # 随机数据 + 回放最近 60 天（无未来函数）
"""
import argparse

import pandas as pd

from agents import ALL_AGENTS
from data import fetch_sse, make_demo
from db import init_db, load_daily, save_prediction, upsert_daily
from ensemble import combine


def predict_for(df: pd.DataFrame) -> None:
    base_date = df["date"].iloc[-1]
    preds = {}
    for agent in ALL_AGENTS:
        try:
            p = agent.predict(df)
        except Exception as e:  # 单个智能体出错不影响其他
            print(f"[{agent.name}] 出错：{e}")
            p = None
        if p:
            preds[agent.name] = p
            save_prediction(base_date, agent.name, p.prob_up, p.reason)
    ens = combine(preds)
    if ens:
        save_prediction(base_date, "ENSEMBLE", ens.prob_up, ens.reason)
        print(f"{base_date} 综合上涨概率 {ens.prob_up:.1%}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="使用随机演示数据")
    ap.add_argument("--backfill", type=int, default=0, help="回放最近 N 天的预测")
    args = ap.parse_args()

    init_db()
    upsert_daily(make_demo() if args.demo else fetch_sse())
    df = load_daily()

    for i in range(args.backfill, 0, -1):  # 用截断数据回放，保证不看未来
        predict_for(df.iloc[: len(df) - i])
    predict_for(df)


if __name__ == "__main__":
    main()
