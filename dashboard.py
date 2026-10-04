import streamlit as st
from db import init_db,load_daily,load_predictions,load_scored
st.set_page_config(page_title="上证指数多智能体预测",layout="wide");init_db();daily,preds,scored=load_daily(),load_predictions(),load_scored()
if daily.empty or preds.empty:st.info("还没有数据，请先运行 GitHub Actions 或 python run_daily.py --demo --backfill 60");st.stop()
latest=preds.base_date.max();today=preds[preds.base_date==latest];last=daily.iloc[-1];prev=daily.iloc[-2].close if len(daily)>1 else last.close
st.title("上证指数多智能体预测");st.caption("仅供研究，不构成投资建议。");c1,c2,c3=st.columns(3);c1.metric("最新收盘",f"{last.close:,.2f}",f"{last.close/prev-1:+.2%}");ens=today[today.agent=="ENSEMBLE"]
if not ens.empty:
 p=float(ens.prob_up.iloc[0]);c2.metric("下一交易日上涨概率",f"{p:.1%}","偏多" if p>.5 else "偏空");c3.metric("综合置信度",f"{float(ens.confidence.iloc[0]):.1%}")
st.subheader("各智能体观点");view=today[today.agent!="ENSEMBLE"][["agent","prob_up","confidence","reason"]].copy();view.prob_up=view.prob_up.map("{:.1%}".format);view.confidence=view.confidence.map("{:.1%}".format);st.dataframe(view,hide_index=True)
st.subheader("历史战绩")
if scored.empty:st.write("暂无已出结果的预测。")
else:
 e=scored[scored.agent=="ENSEMBLE"].set_index("base_date")
 if not e.empty:st.line_chart(e.correct.expanding().mean().rename("综合累计方向准确率"))
 stats=scored.groupby("agent").agg(样本数=("correct","size"),方向准确率=("correct","mean"),Brier=("brier","mean"));st.dataframe(stats.style.format({"方向准确率":"{:.1%}","Brier":"{:.4f}"}))
st.subheader("指数走势");st.line_chart(daily.set_index("date").close.tail(250))
