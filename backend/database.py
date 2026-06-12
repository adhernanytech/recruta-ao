"""
database.py — Camada de persistência SQLite para o RecrutaAO
Tabelas: users, candidates, jobs, match_results
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_DIR = os.environ.get("DB_DIR", os.path.dirname(__file__))
DB_PATH = os.path.join(DB_DIR, os.environ.get("DB_NAME", "./bd/recruitao.db"))

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # acesso por nome de coluna
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria todas as tabelas se não existirem."""
    conn = get_connection()
    c = conn.cursor()

    # ── Utilizadores ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,          -- bcrypt hash
            role        TEXT    NOT NULL DEFAULT 'recruiter',
                                                   -- 'admin' | 'recruiter'
            active      INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Candidatos / CVs ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id                    TEXT    PRIMARY KEY,
            name                  TEXT    NOT NULL,
            email                 TEXT,
            phone                 TEXT,
            location              TEXT,
            summary               TEXT,
            skills                TEXT,   -- JSON array
            experience            TEXT,   -- JSON array
            education             TEXT,   -- JSON array
            languages             TEXT,   -- JSON array
            certifications        TEXT,   -- JSON array
            total_experience_years REAL   DEFAULT 0,
            raw_text              TEXT,
            uploaded_by           INTEGER REFERENCES users(id),
            created_at            TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Vagas ─────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            title                 TEXT    NOT NULL,
            description           TEXT,
            required_skills       TEXT,   -- JSON array
            preferred_skills      TEXT,   -- JSON array
            min_experience_years  INTEGER DEFAULT 0,
            education_level       TEXT,
            location              TEXT,
            created_by            INTEGER REFERENCES users(id),
            created_at            TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Resultados de Matching ─────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id           INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            candidate_id     TEXT    REFERENCES candidates(id) ON DELETE CASCADE,
            overall_score    REAL,
            skill_score      REAL,
            experience_score REAL,
            education_score  REAL,
            location_score   REAL,
            matched_skills   TEXT,   -- JSON array
            missing_skills   TEXT,   -- JSON array
            recommendation   TEXT,
            highlights       TEXT,   -- JSON array
            created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ─── helpers JSON ────────────────────────────────────────────────────────────

def _j(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)

def _pj(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []


# ─── USERS ───────────────────────────────────────────────────────────────────

def create_user(name: str, email: str, hashed_password: str, role: str = "recruiter") -> dict:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
            (name, email, hashed_password, role)
        )
        conn.commit()
        return get_user_by_id(c.lastrowid)
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email=? AND active=1", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def list_users() -> list:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id,name,email,role,active,created_at FROM users").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def toggle_user_active(user_id: int, active: bool):
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))
        conn.commit()
    finally:
        conn.close()


# ─── CANDIDATES ──────────────────────────────────────────────────────────────

def save_candidate(profile: dict, uploaded_by: int = None) -> dict:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO candidates
            (id, name, email, phone, location, summary, skills, experience,
             education, languages, certifications, total_experience_years,
             raw_text, uploaded_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            profile["id"], profile["name"], profile.get("email",""),
            profile.get("phone",""), profile.get("location",""),
            profile.get("summary",""),
            _j(profile.get("skills",[])),
            _j(profile.get("experience",[])),
            _j(profile.get("education",[])),
            _j(profile.get("languages",[])),
            _j(profile.get("certifications",[])),
            profile.get("total_experience_years", 0),
            profile.get("raw_text","")[:500],
            uploaded_by
        ))
        conn.commit()
        return get_candidate(profile["id"])
    finally:
        conn.close()

def get_candidate(candidate_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        for f in ["skills","experience","education","languages","certifications"]:
            d[f] = _pj(d.get(f))
        return d
    finally:
        conn.close()

def list_candidates() -> list:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM candidates ORDER BY created_at DESC").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            for f in ["skills","experience","education","languages","certifications"]:
                d[f] = _pj(d.get(f))
            result.append(d)
        return result
    finally:
        conn.close()

def delete_candidate(candidate_id: str) -> bool:
    conn = get_connection()
    try:
        c = conn.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()

def clear_candidates():
    conn = get_connection()
    try:
        conn.execute("DELETE FROM candidates")
        conn.commit()
    finally:
        conn.close()


# ─── JOBS ─────────────────────────────────────────────────────────────────────

def save_job(job: dict, created_by: int = None) -> dict:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO jobs
            (title, description, required_skills, preferred_skills,
             min_experience_years, education_level, location, created_by)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            job["title"], job.get("description",""),
            _j(job.get("required_skills",[])),
            _j(job.get("preferred_skills",[])),
            job.get("min_experience_years", 0),
            job.get("education_level",""),
            job.get("location",""),
            created_by
        ))
        conn.commit()
        return get_job(c.lastrowid)
    finally:
        conn.close()

def get_job(job_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["required_skills"] = _pj(d.get("required_skills"))
        d["preferred_skills"] = _pj(d.get("preferred_skills"))
        return d
    finally:
        conn.close()

def list_jobs() -> list:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["required_skills"] = _pj(d.get("required_skills"))
            d["preferred_skills"] = _pj(d.get("preferred_skills"))
            result.append(d)
        return result
    finally:
        conn.close()

def delete_job(job_id: int) -> bool:
    conn = get_connection()
    try:
        c = conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()


# ─── MATCH RESULTS ────────────────────────────────────────────────────────────

def save_match_results(job_id: int, results: list):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM match_results WHERE job_id=?", (job_id,))
        for r in results:
            conn.execute("""
                INSERT INTO match_results
                (job_id, candidate_id, overall_score, skill_score,
                 experience_score, education_score, location_score,
                 matched_skills, missing_skills, recommendation, highlights)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                job_id,
                r["candidate"]["id"],
                r["overall_score"], r["skill_score"],
                r["experience_score"], r["education_score"], r["location_score"],
                _j(r["matched_skills"]), _j(r["missing_skills"]),
                r["recommendation"], _j(r["highlights"])
            ))
        conn.commit()
    finally:
        conn.close()

def get_match_results(job_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT mr.*, c.name as candidate_name
            FROM match_results mr
            JOIN candidates c ON mr.candidate_id = c.id
            WHERE mr.job_id = ?
            ORDER BY mr.overall_score DESC
        """, (job_id,)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["matched_skills"] = _pj(d.get("matched_skills"))
            d["missing_skills"]  = _pj(d.get("missing_skills"))
            d["highlights"]      = _pj(d.get("highlights"))
            result.append(d)
        return result
    finally:
        conn.close()