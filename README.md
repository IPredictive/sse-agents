# 上证指数次日预测（5 智能体，私人看板）

## 快速开始
```bash
pip install -r requirements.txt
python run_daily.py --demo --backfill 60   # 先用演示数据跑通
streamlit run dashboard.py                 # 打开看板
```
换成真实数据：`python run_daily.py`（需联网，使用 AKShare）。

## 每日定时（cron，时区 Asia/Shanghai）
```
30 15 * * 1-5  cd /path/to/sse_agents && python run_daily.py
```
(节假日休市时重复运行是安全的：同一天同一智能体只记录第一次。)

## 结构
- `agents/` 5 个智能体（technical 已实现，其余 4 个为弃权占位）
- `ensemble.py` 汇总（默认等权）
- `db.py` SQLite 表与读写；predictions 表带触发器，写入后不可改/删
- `run_daily.py` 每日任务；`dashboard.py` Streamlit 看板

## 下一步
1. 依次实现 flow / macro / sentiment / overseas
2. 跑 1–2 个月真实记录，再按 Brier 调整 ensemble.WEIGHTS
