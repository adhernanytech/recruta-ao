"""
main.py — RecrutaAO API
FastAPI + SQLite + JWT Authentication
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uvicorn

from database import (
    init_db, save_candidate, get_candidate, list_candidates,
    delete_candidate, clear_candidates, save_job, get_job,
    list_jobs, delete_job, save_match_results, get_match_results,
    create_user, get_user_by_email, get_user_by_id, list_users, toggle_user_active
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, require_recruiter
)
from nlp_engine import NLPEngine, MatchingEngine

import os

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RecrutaAO API",
    description="Plataforma de recrutamento inteligente — FastAPI + SQLite + JWT",
    version="2.0.0"
)

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"   # fallback para desenvolvimento local
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

nlp     = NLPEngine()
matcher = MatchingEngine()

@app.on_event("startup")
def startup():
    init_db()
    # Cria conta admin por defeito se não existir
    if not get_user_by_email("admin@recruitao.ao"):
        create_user("Administrador", "admin@recruitao.ao",
                    hash_password("Admin@123"), role="admin")
        print("✅ Admin criado: admin@recruitao.ao / Admin@123")

# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "recrutador"

class LoginRequest(BaseModel):
    email: str
    password: str

class JobRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []
    min_experience_years: Optional[int] = 0
    education_level: Optional[str] = ""
    location: Optional[str] = ""

# ─── Rotas Públicas ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "online", "app": "RecrutaAO", "version": "2.0.0"}

@app.get("/health")
def health():
    cands = list_candidates()
    return {"status": "healthy", "candidates": len(cands)}

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register", status_code=201)
def register(data: RegisterRequest):
    if len(data.password) < 6:
        raise HTTPException(400, "Password deve ter pelo menos 6 caracteres")
    if data.role not in ("admin", "recruiter"):
        raise HTTPException(400, "Role inválido. Use 'admin' ou 'recrutador'")
    if get_user_by_email(data.email):
        raise HTTPException(400, "Email já registado")
    user = create_user(data.name, data.email, hash_password(data.password), data.role)
    token = create_access_token(user["id"], user["email"], user["role"])
    return {
        "message": "Conta criada com sucesso",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "name": user["name"],
                 "email": user["email"], "role": user["role"]}
    }

@app.post("/api/auth/login")
def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Email ou password incorrectos")
    if not user["active"]:
        raise HTTPException(403, "Conta desactivada. Contacte o administrador")
    token = create_access_token(user["id"], user["email"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "name": user["name"],
                 "email": user["email"], "role": user["role"]}
    }

@app.get("/api/auth/me")
def me(current: dict = Depends(get_current_user)):
    user = get_user_by_id(int(current["sub"]))
    if not user:
        raise HTTPException(404, "Utilizador não encontrado")
    return {"id": user["id"], "name": user["name"],
            "email": user["email"], "role": user["role"]}

# ─── UTILIZADORES (apenas admin) ──────────────────────────────────────────────

@app.get("/api/users")
def get_users(admin: dict = Depends(require_admin)):
    return list_users()

@app.patch("/api/users/{user_id}/toggle")
def toggle_user(user_id: int, admin: dict = Depends(require_admin)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "Utilizador não encontrado")
    if user_id == int(admin["sub"]):
        raise HTTPException(400, "Não podes desactivar a tua própria conta")
    toggle_user_active(user_id, not user["active"])
    return {"message": "Estado actualizado"}

# ─── CVs / CANDIDATOS ─────────────────────────────────────────────────────────

@app.post("/api/cv/upload", status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    current: dict = Depends(require_recruiter)
):
    if not file.filename.endswith(('.txt', '.pdf', '.doc', '.docx')):
        raise HTTPException(400, "Formato não suportado. Use .txt")
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        text = content.decode('latin-1', errors='ignore')
    if len(text.strip()) < 50:
        raise HTTPException(400, "CV muito curto ou ilegível")
    profile = nlp.extract_info(text, file.filename)
    saved = save_candidate(profile, uploaded_by=int(current["sub"]))
    return saved

@app.post("/api/cv/text", status_code=201)
def parse_cv_text(data: dict, current: dict = Depends(require_recruiter)):
    text = data.get("text", "")
    if len(text.strip()) < 50:
        raise HTTPException(400, "Texto do CV muito curto")
    profile = nlp.extract_info(text, data.get("filename", "cv.txt"))
    return save_candidate(profile, uploaded_by=int(current["sub"]))

@app.get("/api/candidates")
def get_candidates(current: dict = Depends(require_recruiter)):
    return list_candidates()

@app.get("/api/candidates/{candidate_id}")
def get_one_candidate(candidate_id: str, current: dict = Depends(require_recruiter)):
    c = get_candidate(candidate_id)
    if not c:
        raise HTTPException(404, "Candidato não encontrado")
    return c

@app.delete("/api/candidates/{candidate_id}")
def remove_candidate(candidate_id: str, current: dict = Depends(require_recruiter)):
    if not delete_candidate(candidate_id):
        raise HTTPException(404, "Candidato não encontrado")
    return {"message": "Candidato removido"}

@app.delete("/api/candidates")
def remove_all_candidates(current: dict = Depends(require_admin)):
    clear_candidates()
    return {"message": "Todos os candidatos removidos"}

# ─── VAGAS ────────────────────────────────────────────────────────────────────

@app.post("/api/jobs", status_code=201)
def create_job(data: JobRequest, current: dict = Depends(require_recruiter)):
    job = save_job(data.model_dump(), created_by=int(current["sub"]))
    return job

@app.get("/api/jobs")
def get_jobs(current: dict = Depends(require_recruiter)):
    return list_jobs()

@app.get("/api/jobs/{job_id}")
def get_one_job(job_id: int, current: dict = Depends(require_recruiter)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Vaga não encontrada")
    return job

@app.delete("/api/jobs/{job_id}")
def remove_job(job_id: int, current: dict = Depends(require_recruiter)):
    if not delete_job(job_id):
        raise HTTPException(404, "Vaga não encontrada")
    return {"message": "Vaga removida"}

# ─── MATCHING ─────────────────────────────────────────────────────────────────

@app.post("/api/match")
def match_all(data: JobRequest, current: dict = Depends(require_recruiter)):
    candidates = list_candidates()
    if not candidates:
        raise HTTPException(400, "Nenhum CV carregado")
    job_dict = data.model_dump()
    results = sorted(
        [matcher.match(c, job_dict) for c in candidates],
        key=lambda x: x["overall_score"], reverse=True
    )
    # Guarda a vaga e os resultados
    saved_job = save_job(job_dict, created_by=int(current["sub"]))
    save_match_results(saved_job["id"], results)
    return {"job_id": saved_job["id"], "results": results}

@app.post("/api/match/single/{candidate_id}")
def match_one(candidate_id: str, data: JobRequest,
              current: dict = Depends(require_recruiter)):
    c = get_candidate(candidate_id)
    if not c:
        raise HTTPException(404, "Candidato não encontrado")
    return matcher.match(c, data.model_dump())

@app.get("/api/match/history/{job_id}")
def match_history(job_id: int, current: dict = Depends(require_recruiter)):
    return get_match_results(job_id)

# ─── ESTATÍSTICAS ─────────────────────────────────────────────────────────────

@app.get("/api/stats")
def stats(current: dict = Depends(require_recruiter)):
    candidates = list_candidates()
    if not candidates:
        return {"total_candidates": 0}
    all_skills = [s for c in candidates for s in c.get("skills", [])]
    freq = {}
    for s in all_skills:
        freq[s] = freq.get(s, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    exp_vals = [c["total_experience_years"] for c in candidates
                if c.get("total_experience_years")]
    return {
        "total_candidates": len(candidates),
        "avg_experience_years": round(sum(exp_vals)/len(exp_vals), 1) if exp_vals else 0,
        "top_skills": [{"skill": s, "count": c} for s, c in top],
        "locations": list(set(c["location"] for c in candidates if c.get("location")))
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)