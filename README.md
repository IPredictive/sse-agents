# 上证指数多智能体预测（GitHub 自动运行版）

把整个目录上传到 GitHub 后，GitHub Actions 会在每个工作日 15:35（Asia/Shanghai）运行：抓取上证指数、读取海外市场和新闻、运行 5 个 Agent、保存 SQLite 历史，并生成 `site/index.html`。

## Agent
- Technical：MA / MACD / RSI
- Flow：成交量与动量代理资金面
- Macro：宏观/政策新闻标题
- Sentiment：财经新闻标题
- Overseas：标普500、纳斯达克、恒生、美元人民币
- ENSEMBLE：综合可用 Agent

## GitHub
1. 新建 repository，建议 Private。
2. 上传全部文件。
3. Settings → Actions → General，允许 Actions。
4. Actions → Daily SSE Agents → Run workflow 手动跑一次。
5. 本 workflow 使用 `contents: write`，因此需要允许 `GITHUB_TOKEN` 写入仓库内容。

## LLM（可选）
当前规则版不需要 API Key。若以后接入 LLM，可在 Settings → Secrets and variables → Actions 设置 `OPENAI_API_KEY`，再设置 `OPENAI_MODEL`。不要把密钥写入代码。

## 看板
每次运行都会更新 `site/index.html`。可以用 GitHub Pages 部署它；如果仓库/账户不支持对应的 Pages 权限，也可以直接在仓库查看，或下载 Actions artifact。

## 本地测试
```bash
pip install -r requirements.txt
python run_daily.py --demo --backfill 60 --no-news
python generate_site.py
streamlit run dashboard.py
```

## 重要
这是研究和回测框架，不是可靠的股票预测器。所谓“上涨概率”是规则/模型输出，不是保证性的真实概率；不要据此自动交易。

## GitHub Pages
仓库上传后，先手动运行 `Daily SSE Agents`。如果在 Settings → Pages 把 Build and deployment / Source 设为 **GitHub Actions**，随后 `Deploy dashboard to GitHub Pages` 会发布 `site/`。GitHub Actions 支持 schedule 与时区配置；本项目定时任务使用上海时区。
