"""
TruthLens Proxy — Database Layer
SQLite storage for all evaluation logs, research export, and analytics.
"""
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

DB_PATH = os.getenv("TRUTHLENS_DB", "./truthlens_proxy.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id    TEXT UNIQUE NOT NULL,
            timestamp     TEXT NOT NULL,

            -- Request info
            provider      TEXT NOT NULL,   -- openai | anthropic | gemini | ollama
            model         TEXT NOT NULL,
            prompt        TEXT NOT NULL,
            system_prompt TEXT,
            sources       TEXT,            -- JSON array of source docs

            -- Response
            response      TEXT NOT NULL,
            input_tokens  INTEGER,
            output_tokens INTEGER,
            latency_ms    REAL,

            -- TruthLens scores
            groundedness      REAL,
            faithfulness      REAL,
            citation_accuracy REAL,
            consistency_score REAL,
            hallucination_risk TEXT,
            trust_score       REAL,
            eval_latency_ms   REAL,

            -- Claim verification
            total_claims      INTEGER,
            supported_count   INTEGER,
            unsupported_count INTEGER,
            contradicted_count INTEGER,
            supported_pct     REAL,
            contradicted_pct  REAL,

            -- Metadata
            tags          TEXT,            -- JSON array of user-defined tags
            session_id    TEXT,
            user_id       TEXT,
            eval_model    TEXT,            -- which model did the evaluation
            error         TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_provider   ON evaluations(provider);
        CREATE INDEX IF NOT EXISTS idx_model      ON evaluations(model);
        CREATE INDEX IF NOT EXISTS idx_timestamp  ON evaluations(timestamp);
        CREATE INDEX IF NOT EXISTS idx_trust      ON evaluations(trust_score);
        CREATE INDEX IF NOT EXISTS idx_session    ON evaluations(session_id);

        CREATE TABLE IF NOT EXISTS benchmark_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id      TEXT UNIQUE NOT NULL,
            timestamp   TEXT NOT NULL,
            provider    TEXT,
            model       TEXT,
            total_cases INTEGER,
            avg_trust   REAL,
            avg_ground  REAL,
            avg_faith   REAL,
            low_risk_pct  REAL,
            high_risk_pct REAL,
            results_json  TEXT
        );
        """)


def log_evaluation(data: Dict[str, Any]) -> int:
    """Insert a single evaluation record. Returns the row id."""
    with get_conn() as conn:
        cur = conn.execute("""
        INSERT OR REPLACE INTO evaluations (
            request_id, timestamp, provider, model,
            prompt, system_prompt, sources, response,
            input_tokens, output_tokens, latency_ms,
            groundedness, faithfulness, citation_accuracy,
            consistency_score, hallucination_risk, trust_score, eval_latency_ms,
            total_claims, supported_count, unsupported_count, contradicted_count,
            supported_pct, contradicted_pct,
            tags, session_id, user_id, eval_model, error
        ) VALUES (
            :request_id, :timestamp, :provider, :model,
            :prompt, :system_prompt, :sources, :response,
            :input_tokens, :output_tokens, :latency_ms,
            :groundedness, :faithfulness, :citation_accuracy,
            :consistency_score, :hallucination_risk, :trust_score, :eval_latency_ms,
            :total_claims, :supported_count, :unsupported_count, :contradicted_count,
            :supported_pct, :contradicted_pct,
            :tags, :session_id, :user_id, :eval_model, :error
        )
        """, data)
        return cur.lastrowid


def get_evaluations(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    session_id: Optional[str] = None,
    min_trust: Optional[float] = None,
    max_trust: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict]:
    query = "SELECT * FROM evaluations WHERE 1=1"
    params = []
    if provider:
        query += " AND provider = ?"; params.append(provider)
    if model:
        query += " AND model = ?"; params.append(model)
    if session_id:
        query += " AND session_id = ?"; params.append(session_id)
    if min_trust is not None:
        query += " AND trust_score >= ?"; params.append(min_trust)
    if max_trust is not None:
        query += " AND trust_score <= ?"; params.append(max_trust)
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_analytics() -> Dict[str, Any]:
    """Aggregate stats for the dashboard."""
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
        if total == 0:
            return {"total": 0}

        stats = conn.execute("""
        SELECT
            COUNT(*)                          as total,
            AVG(trust_score)                  as avg_trust,
            AVG(groundedness)                 as avg_groundedness,
            AVG(faithfulness)                 as avg_faithfulness,
            MIN(trust_score)                  as min_trust,
            MAX(trust_score)                  as max_trust,
            SUM(CASE WHEN hallucination_risk='Low'    THEN 1 ELSE 0 END) as low_risk,
            SUM(CASE WHEN hallucination_risk='Medium' THEN 1 ELSE 0 END) as med_risk,
            SUM(CASE WHEN hallucination_risk='High'   THEN 1 ELSE 0 END) as high_risk,
            AVG(latency_ms)                   as avg_latency,
            AVG(eval_latency_ms)              as avg_eval_latency
        FROM evaluations WHERE error IS NULL
        """).fetchone()

        by_provider = conn.execute("""
        SELECT provider, COUNT(*) as count,
               AVG(trust_score) as avg_trust,
               AVG(groundedness) as avg_groundedness,
               SUM(CASE WHEN hallucination_risk='High' THEN 1 ELSE 0 END) as high_risk_count
        FROM evaluations WHERE error IS NULL
        GROUP BY provider ORDER BY avg_trust DESC
        """).fetchall()

        by_model = conn.execute("""
        SELECT model, provider, COUNT(*) as count,
               AVG(trust_score) as avg_trust,
               AVG(groundedness) as avg_groundedness,
               AVG(faithfulness) as avg_faithfulness,
               SUM(CASE WHEN hallucination_risk='High' THEN 1 ELSE 0 END) as high_risk_count
        FROM evaluations WHERE error IS NULL
        GROUP BY model ORDER BY avg_trust DESC
        """).fetchall()

        trend = conn.execute("""
        SELECT DATE(timestamp) as date,
               COUNT(*) as count,
               AVG(trust_score) as avg_trust,
               AVG(groundedness) as avg_groundedness
        FROM evaluations WHERE error IS NULL
        GROUP BY DATE(timestamp) ORDER BY date DESC LIMIT 30
        """).fetchall()

        return {
            "total": dict(stats)["total"],
            "avg_trust": round(dict(stats)["avg_trust"] or 0, 1),
            "avg_groundedness": round(dict(stats)["avg_groundedness"] or 0, 1),
            "avg_faithfulness": round(dict(stats)["avg_faithfulness"] or 0, 1),
            "min_trust": round(dict(stats)["min_trust"] or 0, 1),
            "max_trust": round(dict(stats)["max_trust"] or 0, 1),
            "low_risk_count": dict(stats)["low_risk"],
            "medium_risk_count": dict(stats)["med_risk"],
            "high_risk_count": dict(stats)["high_risk"],
            "avg_latency_ms": round(dict(stats)["avg_latency"] or 0, 1),
            "avg_eval_latency_ms": round(dict(stats)["avg_eval_latency"] or 0, 1),
            "by_provider": [dict(r) for r in by_provider],
            "by_model": [dict(r) for r in by_model],
            "trend": [dict(r) for r in trend],
        }


def export_csv(path: str, **filters):
    """Export all evaluations to CSV for research analysis."""
    import csv
    rows = get_evaluations(limit=100000, **filters)
    if not rows:
        return 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
