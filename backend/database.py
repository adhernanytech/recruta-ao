"""
database.py — RecrutaAO Multi-Tenant
Tabelas: companies, users, candidates, jobs, match_results
Cada empresa (tenant) tem dados completamente isolados.
"""

import sqlite3
import json
import os
from typing import Optional

DB_DIR  = os.environ.get("DB_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, os.environ.get("DB_NAME", "recruitao.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Empresas (tenants) ────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            slug        TEXT    NOT NULL UNIQUE,   -- identificador URL-friendly
            email       TEXT    NOT NULL UNIQUE,   -- email de contacto da empresa
            plan        TEXT    NOT NULL DEFAULT 'free',
            active      INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Utilizadores ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id  INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'recruiter',
            active      INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Candidatos ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id                     TEXT    PRIMARY KEY,
            company_id             INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name                   TEXT    NOT NULL,
            email                  TEXT,
            phone                  TEXT,
            location               TEXT,
            summary                TEXT,
            skills                 TEXT,
            experience             TEXT,
            education              TEXT,
            languages              TEXT,
            certifications         TEXT,
            total_experience_years REAL    DEFAULT 0,
            raw_text               TEXT,
            uploaded_by            INTEGER REFERENCES users(id),
            created_at             TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Vagas ─────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id           INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            title                TEXT    NOT NULL,
            description          TEXT,
            required_skills      TEXT,
            preferred_skills     TEXT,
            min_experience_years INTEGER DEFAULT 0,
            education_level      TEXT,
            location             TEXT,
            created_by           INTEGER REFERENCES users(id),
            created_at           TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Resultados de Matching ────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id       INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            job_id           INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            candidate_id     TEXT    REFERENCES candidates(id) ON DELETE CASCADE,
            overall_score    REAL,
            skill_score      REAL,
            experience_score REAL,
            education_score  REAL,
            location_score   REAL,
            matched_skills   TEXT,
            missing_skills   TEXT,
            recommendation   TEXT,
            highlights       TEXT,
            created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ── helpers ───────────────────────────────────────────────────────────────────

def _j(v) -> str:
    return json.dumps(v or [], ensure_ascii=False)

def _pj(v) -> list:
    if not v: return []
    if isinstance(v, list): return v
    try: return json.loads(v)
    except: return []

def _row(row) -> Optional[dict]:
    return dict(row) if row else None


# ── COMPANIES ─────────────────────────────────────────────────────────────────

def create_company(name: str, slug: str, email: str) -> dict:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO companies (name, slug, email) VALUES (?,?,?)",
            (name, slug, email)
        )
        conn.commit()
        return get_company_by_id(c.lastrowid)
    finally:
        conn.close()

def get_company_by_id(cid: int) -> Optional[dict]:
    conn = get_connection()
    try:
        return _row(conn.execute("SELECT * FROM companies WHERE id=?", (cid,)).fetchone())
    finally:
        conn.close()

def get_company_by_slug(slug: str) -> Optional[dict]:
    conn = get_connection()
    try:
        return _row(conn.execute("SELECT * FROM companies WHERE slug=? AND active=1", (slug,)).fetchone())
    finally:
        conn.close()

def get_company_by_email(email: str) -> Optional[dict]:
    conn = get_connection()
    try:
        return _row(conn.execute("SELECT * FROM companies WHERE email=?", (email,)).fetchone())
    finally:
        conn.close()

def list_companies() -> list:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM companies ORDER BY created_at DESC").fetchall()]
    finally:
        conn.close()


# ── USERS ─────────────────────────────────────────────────────────────────────

def create_user(company_id: int, name: str, email: str,
                hashed_password: str, role: str = "recruiter") -> dict:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (company_id,name,email,password,role) VALUES (?,?,?,?,?)",
            (company_id, name, email, hashed_password, role)
        )
        conn.commit()
        return get_user_by_id(c.lastrowid)
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_connection()
    try:
        return _row(conn.execute("SELECT * FROM users WHERE email=? AND active=1", (email,)).fetchone())
    finally:
        conn.close()

def get_user_by_id(uid: int) -> Optional[dict]:
    conn = get_connection()
    try:
        return _row(conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
    finally:
        conn.close()

def list_users_by_company(company_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id,name,email,role,active,created_at FROM users WHERE company_id=?",
            (company_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def toggle_user_active(uid: int, active: bool):
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, uid))
        conn.commit()
    finally:
        conn.close()


# ── CANDIDATES ────────────────────────────────────────────────────────────────

def save_candidate(profile: dict, company_id: int, uploaded_by: int = None) -> dict:
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO candidates
            (id,company_id,name,email,phone,location,summary,skills,experience,
             education,languages,certifications,total_experience_years,raw_text,uploaded_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            profile["id"], company_id, profile["name"],
            profile.get("email",""), profile.get("phone",""),
            profile.get("location",""), profile.get("summary",""),
            _j(profile.get("skills",[])), _j(profile.get("experience",[])),
            _j(profile.get("education",[])), _j(profile.get("languages",[])),
            _j(profile.get("certifications",[])),
            profile.get("total_experience_years", 0),
            profile.get("raw_text","")[:500], uploaded_by
        ))
        conn.commit()
        return get_candidate(profile["id"], company_id)
    finally:
        conn.close()

def get_candidate(candidate_id: str, company_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM candidates WHERE id=? AND company_id=?",
            (candidate_id, company_id)
        ).fetchone()
        if not row: return None
        d = dict(row)
        for f in ["skills","experience","education","languages","certifications"]:
            d[f] = _pj(d.get(f))
        return d
    finally:
        conn.close()

def list_candidates(company_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE company_id=? ORDER BY created_at DESC",
            (company_id,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            for f in ["skills","experience","education","languages","certifications"]:
                d[f] = _pj(d.get(f))
            result.append(d)
        return result
    finally:
        conn.close()

def delete_candidate(candidate_id: str, company_id: int) -> bool:
    conn = get_connection()
    try:
        c = conn.execute(
            "DELETE FROM candidates WHERE id=? AND company_id=?",
            (candidate_id, company_id)
        )
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()

def clear_candidates(company_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM candidates WHERE company_id=?", (company_id,))
        conn.commit()
    finally:
        conn.close()


# ── JOBS ──────────────────────────────────────────────────────────────────────

def save_job(job: dict, company_id: int, created_by: int = None) -> dict:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO jobs
            (company_id,title,description,required_skills,preferred_skills,
             min_experience_years,education_level,location,created_by)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            company_id, job["title"], job.get("description",""),
            _j(job.get("required_skills",[])), _j(job.get("preferred_skills",[])),
            job.get("min_experience_years",0), job.get("education_level",""),
            job.get("location",""), created_by
        ))
        conn.commit()
        return get_job(c.lastrowid, company_id)
    finally:
        conn.close()

def get_job(job_id: int, company_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM jobs WHERE id=? AND company_id=?",
            (job_id, company_id)
        ).fetchone()
        if not row: return None
        d = dict(row)
        d["required_skills"] = _pj(d.get("required_skills"))
        d["preferred_skills"] = _pj(d.get("preferred_skills"))
        return d
    finally:
        conn.close()

def list_jobs(company_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE company_id=? ORDER BY created_at DESC",
            (company_id,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["required_skills"] = _pj(d.get("required_skills"))
            d["preferred_skills"] = _pj(d.get("preferred_skills"))
            result.append(d)
        return result
    finally:
        conn.close()

def delete_job(job_id: int, company_id: int) -> bool:
    conn = get_connection()
    try:
        c = conn.execute(
            "DELETE FROM jobs WHERE id=? AND company_id=?",
            (job_id, company_id)
        )
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()


# ── MATCH RESULTS ─────────────────────────────────────────────────────────────

def save_match_results(job_id: int, company_id: int, results: list):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM match_results WHERE job_id=? AND company_id=?",
            (job_id, company_id)
        )
        for r in results:
            conn.execute("""
                INSERT INTO match_results
                (company_id,job_id,candidate_id,overall_score,skill_score,
                 experience_score,education_score,location_score,
                 matched_skills,missing_skills,recommendation,highlights)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                company_id, job_id, r["candidate"]["id"],
                r["overall_score"], r["skill_score"],
                r["experience_score"], r["education_score"], r["location_score"],
                _j(r["matched_skills"]), _j(r["missing_skills"]),
                r["recommendation"], _j(r["highlights"])
            ))
        conn.commit()
    finally:
        conn.close()

def get_match_results(job_id: int, company_id: int) -> list:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT mr.*, c.name as candidate_name
            FROM match_results mr
            JOIN candidates c ON mr.candidate_id = c.id
            WHERE mr.job_id=? AND mr.company_id=?
            ORDER BY mr.overall_score DESC
        """, (job_id, company_id)).fetchall()
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

def get_stats(company_id: int) -> dict:
    candidates = list_candidates(company_id)
    if not candidates:
        return {"total_candidates": 0}
    all_skills = [s for c in candidates for s in c.get("skills", [])]
    freq = {}
    for s in all_skills:
        freq[s] = freq.get(s, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    exp_vals = [c["total_experience_years"] for c in candidates if c.get("total_experience_years")]
    return {
        "total_candidates": len(candidates),
        "avg_experience_years": round(sum(exp_vals)/len(exp_vals), 1) if exp_vals else 0,
        "top_skills": [{"skill": s, "count": c} for s, c in top],
        "locations": list(set(c["location"] for c in candidates if c.get("location")))
    }
