import pandas as pd
import streamlit as st

from db import init_db, load_daily, load_predictions, load_scored

st.set_page_config(page_title="上证指数预测看板", layout="wide")
init_db()

daily, preds, scored = load_daily(), load_predictions(), load_scored()
if daily.empty or preds.empty:
    st.info("还没有数据，先运行：python run_daily.py --demo --backfill 60")
    st.stop()

st.title("上证指数次日预测（私人看板）")
st.caption("仅供技术研究，不构成投资建议。")

# ---- 最新预测 ----
latest = preds["base_date"].max()
today = preds[preds["base_date"] == latest]
last = daily.iloc[-1]
prev = daily.iloc[-2]["close"] if len(daily) > 1 else last["close"]

c1, c2 = st.columns(2)
c1.metric("最新收盘", f"{last['close']:,.2f}", f"{(last['close']/prev-1):+.2%}")
ens = today[today["agent"] == "ENSEMBLE"]
if not ens.empty:
    p = ens["prob_up"].iloc[0]
    c2.metric(f"基于 {latest} 数据：下一交易日上涨概率", f"{p:.1%}",
              "偏多" if p > 0.5 else "偏空")

st.subheader("各智能体观点")
view = today[today["agent"] != "ENSEMBLE"][["agent", "prob_up", "reason"]].copy()
view["prob_up"] = view["prob_up"].map("{:.1%}".format)
st.dataframe(view, hide_index=True)

# ---- 战绩 ----
st.subheader("历史战绩")
if scored.empty:
    st.write("暂无已出结果的预测。")
else:
    e = scored[scored["agent"] == "ENSEMBLE"].set_index("base_date")
    if not e.empty:
        st.line_chart(e["correct"].expanding().mean().rename("综合累计方向准确率"))

    stats = scored.groupby("agent").agg(
        样本数=("correct", "size"),
        方向准确率=("correct", "mean"),
        Brier=("brier", "mean"),
    )
    st.dataframe(stats.style.format({"方向准确率": "{:.1%}", "Brier": "{:.4f}"}))
    base_rate = scored.drop_duplicates("base_date")["went_up"].mean()
    st.caption(f"对照基线：样本期内上涨天数占比 {base_rate:.1%}（永远猜涨的准确率）；"
               "Brier 越低越好，纯猜 0.5 为 0.25。")

st.subheader("指数走势")
st.line_chart(daily.set_index("date")["close"].tail(250))
