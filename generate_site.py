import html, json
from pathlib import Path
from db import init_db,load_daily,load_predictions,load_scored

OUT=Path(__file__).parent/"site"/"index.html"

def pct(x):
    return f"{float(x):.1%}"

def main():
    init_db()
    d=load_daily(); p=load_predictions(); s=load_scored()
    latest=p.base_date.max() if not p.empty else "-"
    rows=p[p.base_date==latest] if not p.empty else p
    chief=rows[rows.agent=="CHIEF_ANALYST"]
    if chief.empty:
        chief=rows[rows.agent=="ENSEMBLE"]
    prob=float(chief.prob_up.iloc[0]) if not chief.empty else None
    conf=float(chief.confidence.iloc[0]) if not chief.empty else None
    reason=str(chief.reason.iloc[0]) if not chief.empty else "暂无首席分析"
    price=float(d.close.iloc[-1]) if not d.empty else None
    prev=float(d.close.iloc[-2]) if len(d)>1 else price
    change=(price/prev-1) if price and prev else None

    analysts=[r for _,r in rows.iterrows() if r.agent not in ("CHIEF_ANALYST","ENSEMBLE")]
    cards="".join(
        f"<div class='analyst'><div class='aname'>{html.escape(str(r.agent)).upper()}</div>"
        f"<div class='aprob'>{pct(r.prob_up)}</div><div class='muted'>信心 {pct(r.confidence)}</div>"
        f"<p>{html.escape(str(r.reason))}</p></div>" for r in analysts)

    history=""
    if not s.empty:
        for agent,g in s.groupby("agent"):
            history+=f"<tr><td>{html.escape(str(agent))}</td><td>{len(g)}</td><td>{pct(g.correct.mean())}</td><td>{g.brier.mean():.4f}</td></tr>"

    direction="偏多" if prob is not None and prob>.5 else "偏空" if prob is not None else "暂无"
    price_text=f"{price:,.2f}" if price is not None else "-"
    change_text=f"{change:+.2%}" if change is not None else "-"
    prob_text=pct(prob) if prob is not None else "-"
    conf_text=pct(conf) if conf is not None else "-"

    html_doc=f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>上证 AI 首席分析台</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b1020;color:#eef2ff;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:1180px;margin:auto;padding:28px 18px 50px}}.top{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}}
h1{{font-size:30px;margin:0 0 7px}}h2{{margin:0 0 15px;font-size:19px}}.muted{{color:#9aa5bd;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.card,.analyst{{background:#131a2d;border:1px solid #26314b;border-radius:16px;padding:20px;box-shadow:0 8px 28px rgba(0,0,0,.18)}}
.big{{font-size:34px;font-weight:750;margin-top:7px}}.green{{color:#55d98b}}.red{{color:#ff7182}}
.section{{margin-top:16px}}.chief{{border:1px solid #435b8e;background:linear-gradient(135deg,#18233c,#111827)}}
.chiefrow{{display:grid;grid-template-columns:220px 1fr;gap:24px;align-items:center}}.prob{{font-size:56px;font-weight:800}}.reason{{font-size:16px;line-height:1.7;color:#d9e1f2}}
.analysts{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}.analyst{{padding:16px}}.aname{{font-size:12px;color:#9aa5bd;letter-spacing:.08em;font-weight:700}}.aprob{{font-size:27px;font-weight:750;margin:8px 0}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;border-bottom:1px solid #26314b;text-align:left;font-size:14px}}
.footer{{margin-top:25px;color:#75809a;font-size:12px}}@media(max-width:850px){{.grid,.analysts,.chiefrow{{grid-template-columns:1fr}}}}
</style></head><body><main class="wrap">
<div class="top"><div><h1>上证 AI 首席分析台</h1><div class="muted">每日自动更新 · 5 位 AI 分析师 + Chief Analyst</div></div><div class="muted">分析基准日：{html.escape(str(latest))}</div></div>
<div class="grid">
<div class="card"><div class="muted">上证指数最新收盘</div><div class="big">{price_text}</div><div class="muted">{change_text} 较前一交易日</div></div>
<div class="card"><div class="muted">Chief Analyst 上涨概率</div><div class="big {'green' if prob and prob>.5 else 'red' if prob is not None else ''}">{prob_text} · {direction}</div></div>
<div class="card"><div class="muted">Chief Analyst 信心</div><div class="big">{conf_text}</div></div>
</div>
<section class="section card chief"><h2>👔 Chief Analyst 最终判断</h2><div class="chiefrow"><div><div class="muted">下一交易日</div><div class="prob">{prob_text}</div><div class="muted">{direction}</div></div><div class="reason">{html.escape(reason)}</div></div></section>
<section class="section"><h2>五位 AI 分析师</h2><div class="analysts">{cards}</div></section>
<section class="section card"><h2>历史战绩</h2><table><tr><th>分析师</th><th>样本</th><th>方向准确率</th><th>Brier</th></tr>{history or '<tr><td colspan="4">暂无已结算样本</td></tr>'}</table></section>
<div class="footer">本页面由 GitHub Actions 自动生成。仅供研究参考，不构成投资建议。</div>
</main></body></html>"""
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(html_doc,encoding="utf-8")

if __name__=="__main__": main()
