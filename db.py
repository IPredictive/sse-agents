"""SQLite 存储：行情、预测。预测写入后不可修改/删除（触发器保证）。"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "sse.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_index (
    date   TEXT PRIMARY KEY,           -- YYYY-MM-DD
    open   REAL, high REAL, low REAL, close REAL, volume REAL
);

CREATE TABLE IF NOT EXISTS predictions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    base_date  TEXT NOT NULL,          -- 预测所用数据的最后一个交易日
    agent      TEXT NOT NULL,          -- 智能体名；综合结果为 ENSEMBLE
    prob_up    REAL NOT NULL,          -- 下一交易日上涨概率 0~1
    reason     TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (base_date, agent)
);

CREATE TRIGGER IF NOT EXISTS predictions_no_update
BEFORE UPDATE ON predictions
BEGIN SELECT RAISE(ABORT, 'predictions are immutable'); END;

CREATE TRIGGER IF NOT EXISTS predictions_no_delete
BEFORE DELETE ON predictions
BEGIN SELECT RAISE(ABORT, 'predictions are immutable'); END;
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def upsert_daily(df: pd.DataFrame) -> None:
    rows = df[["date", "open", "high", "low", "close", "volume"]].values.tolist()
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO daily_index VALUES (?,?,?,?,?,?)", rows
        )


def load_daily() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql("SELECT * FROM daily_index ORDER BY date", conn)


def save_prediction(base_date: str, agent: str, prob_up: float, reason: str) -> None:
    """INSERT OR IGNORE：同一天同一智能体只记录第一次，之后不会被覆盖。"""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO predictions (base_date, agent, prob_up, reason) "
            "VALUES (?,?,?,?)",
            (base_date, agent, float(prob_up), reason),
        )


def load_predictions() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(
            "SELECT base_date, agent, prob_up, reason, created_at "
            "FROM predictions ORDER BY base_date, agent",
            conn,
        )


def load_scored() -> pd.DataFrame:
    """把预测与真实结果对上：结果 = base_date 之后的第一个交易日相对 base_date 的涨跌。"""
    sql = """
    SELECT p.base_date, p.agent, p.prob_up,
      (SELECT close FROM daily_index WHERE date = p.base_date) AS base_close,
      (SELECT close FROM daily_index d WHERE d.date > p.base_date
         ORDER BY d.date LIMIT 1) AS result_close
    FROM predictions p
    """
    with get_conn() as conn:
        df = pd.read_sql(sql, conn)
    df = df.dropna(subset=["base_close", "result_close"]).copy()
    df["went_up"] = (df["result_close"] > df["base_close"]).astype(int)
    df["correct"] = ((df["prob_up"] > 0.5).astype(int) == df["went_up"]).astype(int)
    df["brier"] = (df["prob_up"] - df["went_up"]) ** 2
    return df.sort_values("base_date")
