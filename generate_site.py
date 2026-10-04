import html
from pathlib import Path
from db import init_db, load_daily, load_predictions, load_scored

OUT = Path(__file__).parent / "site" / "index.html"


def pct(x):
    return f"{float(x):.1%}"


def direction_text(p):
    if p is None:
        return "暂无"
    p = float(p)
    if p >= 0.70:
        return "强烈偏多"
    if p >= 0.60:
        return "偏多"
    if p >= 0.53:
        return "中性偏多"
    if p > 0.47:
        return "中性"
    if p > 0.40:
        return "中性偏空"
    if p > 0.30:
        return "偏空"
    return "强烈偏空"


def tone(p):
    if p is None:
        return "neutral"
    p = float(p)
    if p > 0.53:
        return "bull"
    if p < 0.47:
        return "bear"
    return "neutral"


def bar_width(p):
    if p is None:
        return 50
    return max(4, min(96, float(p) * 100))


def main():
    init_db()
    d = load_daily()
    p = load_predictions()
    s = load_scored()

    latest = p.base_date.max() if not p.empty else "-"
    rows = p[p.base_date == latest] if not p.empty else p

    chief = rows[rows.agent == "CHIEF_ANALYST"]
    if chief.empty:
        chief = rows[rows.agent == "ENSEMBLE"]

    prob = float(chief.prob_up.iloc[0]) if not chief.empty else None
    conf = float(chief.confidence.iloc[0]) if not chief.empty else None
    reason = str(chief.reason.iloc[0]) if not chief.empty else "暂无首席分析"

    price = float(d.close.iloc[-1]) if not d.empty else None
    prev = float(d.close.iloc[-2]) if len(d) > 1 else price
    change = (price / prev - 1) if price and prev else None

    analysts = [
        r for _, r in rows.iterrows()
        if r.agent not in ("CHIEF_ANALYST", "ENSEMBLE")
    ]

    cards = ""
    for r in analysts:
        p_up = float(r.prob_up)
        conf_a = float(r.confidence)
        t = tone(p_up)
        cards += f"""
        <article class="analyst-card {t}">
          <div class="analyst-head">
            <span class="agent-dot"></span>
            <span class="aname">{html.escape(str(r.agent)).upper()}</span>
          </div>
          <div class="analyst-prob">{pct(p_up)}</div>
          <div class="mini-track"><span style="width:{bar_width(p_up):.1f}%"></span></div>
          <div class="analyst-meta">
            <span>上涨概率</span><strong>信心 {pct(conf_a)}</strong>
          </div>
          <p>{html.escape(str(r.reason))}</p>
        </article>
        """

    history = ""
    if not s.empty:
        for agent, g in s.groupby("agent"):
            history += (
                f"<tr><td><span class='table-agent'>{html.escape(str(agent))}</span></td>"
                f"<td>{len(g)}</td><td>{pct(g.correct.mean())}</td>"
                f"<td>{g.brier.mean():.4f}</td></tr>"
            )

    direction = direction_text(prob)
    chief_tone = tone(prob)
    price_text = f"{price:,.2f}" if price is not None else "-"
    change_text = f"{change:+.2%}" if change is not None else "-"
    prob_text = pct(prob) if prob is not None else "-"
    conf_text = pct(conf) if conf is not None else "-"
    change_cls = "up" if change is not None and change >= 0 else "down"

    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#080b12">
<title>狮城胖叔·上证分析台</title>
<style>
:root {{
  --bg:#080b12; --panel:#10151f; --panel2:#141b28; --line:#222c3d;
  --text:#f4f7fb; --muted:#8d98aa; --soft:#c5cedc; --green:#42d392;
  --red:#ff6576; --blue:#7aa2ff; --gold:#f4c95d;
}}
* {{ box-sizing:border-box }}
body {{
  margin:0; color:var(--text); background:
  radial-gradient(circle at 80% -10%, rgba(91,118,255,.18), transparent 32%),
  radial-gradient(circle at 10% 15%, rgba(66,211,146,.07), transparent 25%),
  var(--bg);
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
}}
.wrap {{ max-width:1240px; margin:auto; padding:30px 20px 64px }}
.top {{
  display:flex; justify-content:space-between; align-items:flex-end; gap:24px;
  padding:8px 2px 28px;
}}
.brand {{ display:flex; gap:14px; align-items:center }}
.logo {{
  width:48px; height:48px; display:grid; place-items:center; border-radius:15px;
  background:linear-gradient(145deg,#1b2740,#101827); border:1px solid #2c3a55;
  box-shadow:0 10px 30px rgba(0,0,0,.25); font-size:24px;
}}
h1 {{ margin:0 0 5px; font-size:28px; letter-spacing:-.03em }}
h2 {{ margin:0 0 18px; font-size:17px }}
.muted {{ color:var(--muted); font-size:13px }}
.date-pill {{
  border:1px solid var(--line); background:rgba(16,21,31,.75); color:var(--soft);
  border-radius:999px; padding:9px 13px; font-size:12px; white-space:nowrap;
}}
.grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px }}
.card {{
  background:linear-gradient(180deg,rgba(20,27,40,.94),rgba(13,18,27,.94));
  border:1px solid var(--line); border-radius:18px; padding:20px;
  box-shadow:0 16px 42px rgba(0,0,0,.18);
}}
.metric-label {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.06em }}
.big {{ font-size:32px; font-weight:800; letter-spacing:-.04em; margin:10px 0 5px }}
.sub {{ color:var(--soft); font-size:12px }}
.up {{ color:var(--green) }} .down {{ color:var(--red) }}
.chief {{
  margin-top:14px; overflow:hidden; position:relative;
  background:
    radial-gradient(circle at 90% 10%, rgba(122,162,255,.16), transparent 30%),
    linear-gradient(135deg,#141d30,#0e141f);
  border-color:#2c3d5e;
}}
.chief::after {{
  content:""; position:absolute; width:180px; height:180px; right:-70px; bottom:-90px;
  border:1px solid rgba(122,162,255,.16); border-radius:50%;
}}
.chief-top {{ display:flex; justify-content:space-between; align-items:center; gap:16px }}
.kicker {{
  display:inline-flex; align-items:center; gap:7px; color:#b9c7e4; font-size:12px;
  border:1px solid #30415f; background:rgba(35,49,78,.45); border-radius:999px; padding:6px 10px;
}}
.kicker-dot {{ width:6px; height:6px; border-radius:50%; background:var(--gold); box-shadow:0 0 12px var(--gold) }}
.chiefrow {{ display:grid; grid-template-columns:250px 1fr; gap:28px; align-items:center; margin-top:20px }}
.prob {{ font-size:62px; line-height:1; font-weight:850; letter-spacing:-.06em }}
.chief-direction {{ margin-top:9px; font-size:15px; font-weight:700 }}
.reason {{ color:#d8dfeb; font-size:14px; line-height:1.85; max-width:760px }}
.conf-row {{ margin-top:14px; display:flex; align-items:center; gap:10px; color:var(--muted); font-size:12px }}
.conf-track,.mini-track {{ height:6px; background:#202a3a; border-radius:999px; overflow:hidden }}
.conf-track {{ width:150px }}
.conf-track span {{ display:block; height:100%; width:{bar_width(conf):.1f}%; background:linear-gradient(90deg,#5f8cff,#7aa2ff); border-radius:inherit }}
.section {{ margin-top:28px }}
.section-title {{ display:flex; justify-content:space-between; align-items:end; margin-bottom:14px }}
.section-title .hint {{ color:var(--muted); font-size:12px }}
.analysts {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px }}
.analyst-card {{
  min-width:0; background:rgba(16,21,31,.92); border:1px solid var(--line);
  border-radius:16px; padding:16px; transition:transform .2s ease,border-color .2s ease;
}}
.analyst-card:hover {{ transform:translateY(-2px); border-color:#34445e }}
.analyst-head {{ display:flex; align-items:center; gap:8px }}
.agent-dot {{ width:7px; height:7px; border-radius:50%; background:#7f8ba0 }}
.bull .agent-dot {{ background:var(--green); box-shadow:0 0 10px rgba(66,211,146,.5) }}
.bear .agent-dot {{ background:var(--red); box-shadow:0 0 10px rgba(255,101,118,.45) }}
.aname {{ color:#aeb9cb; font-size:11px; letter-spacing:.09em; font-weight:800 }}
.analyst-prob {{ font-size:29px; font-weight:800; margin:14px 0 9px; letter-spacing:-.04em }}
.mini-track span {{ display:block; height:100%; border-radius:inherit; background:#65738a }}
.bull .mini-track span {{ background:var(--green) }}
.bear .mini-track span {{ background:var(--red) }}
.analyst-meta {{ display:flex; justify-content:space-between; margin-top:8px; color:var(--muted); font-size:11px }}
.analyst-meta strong {{ color:#b8c2d2; font-weight:600 }}
.analyst-card p {{ color:#aeb8c8; font-size:12px; line-height:1.65; margin:13px 0 0 }}
.table-wrap {{ overflow:auto }}
table {{ width:100%; border-collapse:collapse; min-width:560px }}
th,td {{ padding:12px 10px; border-bottom:1px solid var(--line); text-align:left; font-size:13px }}
th {{ color:var(--muted); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.05em }}
td {{ color:#d6deea }}
.table-agent {{ font-weight:700; color:#eef2ff }}
.footer {{ margin-top:28px; display:flex; justify-content:space-between; gap:12px; color:#68758a; font-size:11px }}
@media(max-width:980px) {{
  .analysts {{ grid-template-columns:repeat(2,1fr) }}
  .chiefrow {{ grid-template-columns:190px 1fr }}
}}
@media(max-width:700px) {{
  .wrap {{ padding:20px 14px 45px }}
  .top {{ align-items:flex-start; flex-direction:column; padding-bottom:20px }}
  h1 {{ font-size:24px }}
  .grid {{ grid-template-columns:1fr }}
  .chiefrow {{ grid-template-columns:1fr; gap:18px }}
  .prob {{ font-size:52px }}
  .analysts {{ grid-template-columns:1fr }}
  .footer {{ flex-direction:column }}
}}
</style>
</head>
<body>
<main class="wrap">
  <header class="top">
    <div class="brand">
      <div class="logo">📈</div>
      <div>
        <h1>狮城胖叔·上证分析台</h1>
        <div class="muted">量化数据 · 多维信号 · 每日自动更新</div>
      </div>
    </div>
    <div class="date-pill">分析基准日 · {html.escape(str(latest))}</div>
  </header>

  <section class="grid">
    <div class="card">
      <div class="metric-label">上证指数 · Latest Close</div>
      <div class="big">{price_text}</div>
      <div class="sub {change_cls}">{change_text} <span style="color:var(--muted)">较前一交易日</span></div>
    </div>
    <div class="card">
      <div class="metric-label">Chief Analyst · Upside Probability</div>
      <div class="big {chief_tone}">{prob_text}</div>
      <div class="sub">{direction} · 下一交易日</div>
    </div>
    <div class="card">
      <div class="metric-label">Model Confidence</div>
      <div class="big">{conf_text}</div>
      <div class="conf-row"><span>综合信心</span><div class="conf-track"><span></span></div></div>
    </div>
  </section>

  <section class="card chief">
    <div class="chief-top">
      <div>
        <div class="kicker"><span class="kicker-dot"></span> CHIEF ANALYST · FINAL CALL</div>
      </div>
      <div class="muted">面向下一交易日</div>
    </div>
    <div class="chiefrow">
      <div>
        <div class="prob {chief_tone}">{prob_text}</div>
        <div class="chief-direction">{direction}</div>
      </div>
      <div>
        <div class="reason">{html.escape(reason)}</div>
        <div class="conf-row">模型信心 {conf_text}<div class="conf-track"><span></span></div></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-title">
      <h2>五位智能分析师</h2>
      <span class="hint">独立信号 → 动态加权 → Chief Analyst</span>
    </div>
    <div class="analysts">{cards}</div>
  </section>

  <section class="section card">
    <div class="section-title">
      <h2>历史战绩</h2>
      <span class="hint">已结算预测</span>
    </div>
    <div class="table-wrap">
      <table>
        <tr><th>分析师</th><th>样本</th><th>方向准确率</th><th>Brier</th></tr>
        {history or '<tr><td colspan="4">暂无已结算样本</td></tr>'}
      </table>
    </div>
  </section>

  <footer class="footer">
    <span>狮城胖叔·上证分析台</span>
    <span>GitHub Actions 自动生成 · 仅供研究参考，不构成投资建议</span>
  </footer>
</main>
</body>
</html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()
