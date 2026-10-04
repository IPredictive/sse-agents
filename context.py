import json, os, urllib.parse, urllib.request, xml.etree.ElementTree as ET, time
def _get(url,timeout=12):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 sse-agents/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
def google_news(query,limit=12):
    try:
        url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":query,"hl":"zh-CN","gl":"CN","ceid":"CN:zh-Hans"});root=ET.fromstring(_get(url));return [x.text for x in root.findall("./channel/item/title")[:limit] if x.text]
    except Exception as e:print("news fetch skipped:",e);return []
def yahoo_return(symbol,days=3):
    try:
        end=int(time.time());start=end-days*86400;url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?period1={start}&period2={end}&interval=1d";o=json.loads(_get(url));c=o["chart"]["result"][0]["indicators"]["quote"][0]["close"];c=[x for x in c if x is not None];return c[-1]/c[-2]-1 if len(c)>=2 else None
    except Exception as e:print(f"Yahoo {symbol} skipped:",e);return None
def build_context():
    overseas={};symbols={"标普500":"^GSPC","纳斯达克":"^IXIC","恒生指数":"^HSI","美元人民币":"CNY=X"}
    for k,s in symbols.items():
        r=yahoo_return(s)
        if r is not None:overseas[k]=r
    return {"news_titles":google_news("上证指数 OR A股 OR 沪深股市"),"macro_titles":google_news("中国 央行 OR 国务院 OR 财政政策 OR 货币政策 OR 宏观经济 股市"),"overseas":overseas}


def llm_news_score(titles, role):
    """可选 LLM 层：没有 OPENAI_API_KEY 时返回 None，不影响规则 Agent。"""
    key=os.getenv("OPENAI_API_KEY")
    if not key or not titles:
        return None
    model=os.getenv("OPENAI_MODEL") or "gpt-6-luna"
    prompt=(
        "你是中国A股研究员。只根据给出的新闻标题，判断对下一交易日上证指数的方向影响。"
        "不要使用未来信息。返回严格JSON：{\"prob_up\":0到1之间数字,\"reason\":\"不超过80字\"}。"
        f"角色：{role}。\n新闻标题：\n" + "\n".join(f"- {x}" for x in titles[:12])
    )
    try:
        payload={"model":model,"input":[{"role":"user","content":prompt}]}
        req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=45) as r: obj=json.loads(r.read())
        text=obj.get("output_text","").strip()
        if not text:
            parts=[]
            for item in obj.get("output",[]):
                for c in item.get("content",[]):
                    if c.get("type")=="output_text": parts.append(c.get("text",""))
            text="".join(parts).strip()
        if text.startswith("```"):
            text=text.strip("`").replace("json\n", "", 1).strip()
        result=json.loads(text); p=float(result["prob_up"]); reason=str(result.get("reason","LLM分析"))
        if 0<=p<=1:return p,reason
    except Exception as e:
        print("LLM news scoring skipped:",e)
    return None
