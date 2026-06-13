"""
main.py — RecrutaAO Multi-Tenant API v3.0
Cada empresa tem dados completamente isolados (company_id em todas as queries)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os, re, uvicorn

from database_v2 import (
    init_db,
    create_company, get_company_by_slug, get_company_by_email, get_company_by_id, list_companies,
    create_user, get_user_by_email, get_user_by_id, list_users_by_company, toggle_user_active,
    save_candidate, get_candidate, list_candidates, delete_candidate, clear_candidates,
    save_job, get_job, list_jobs, delete_job,
    save_match_results, get_match_results, get_stats
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, require_recruiter
)
from nlp_engine import NLPEngine, MatchingEngine

app = FastAPI(title="RecrutaAO API", version="3.0.0")

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
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


# ── Schemas ───────────────────────────────────────────────────────────────────

class CompanyRegisterRequest(BaseModel):
    company_name: str
    company_email: str
    admin_name: str
    admin_email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class InviteUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "recruiter"

class JobRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []
    min_experience_years: Optional[int] = 0
    education_level: Optional[str] = ""
    location: Optional[str] = ""


# ── helper: gera slug único ───────────────────────────────────────────────────

def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug[:40]


# ── helper: obtém company_id do token ────────────────────────────────────────

def _cid(user: dict) -> int:
    return int(user["company_id"])


# ── Rotas públicas ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"app": "RecrutaAO", "version": "3.0.0", "status": "online"}

@app.get("/health")
def health():
    return {"status": "healthy"}


# ── REGISTO DE EMPRESA ────────────────────────────────────────────────────────

@app.post("/api/companies/register", status_code=201)
def register_company(data: CompanyRegisterRequest):
    """
    Cria uma nova empresa + utilizador admin em simultâneo.
    É o ponto de entrada de um novo cliente do sistema.
    """
    if len(data.password) < 6:
        raise HTTPException(400, "Password deve ter pelo menos 6 caracteres")
    if get_company_by_email(data.company_email):
        raise HTTPException(400, "Já existe uma empresa com este email")
    if get_user_by_email(data.admin_email):
        raise HTTPException(400, "Este email de utilizador já está registado")

    slug = _slugify(data.company_name)
    # garante slug único
    base_slug = slug
    i = 1
    while get_company_by_slug(slug):
        slug = f"{base_slug}-{i}"
        i += 1

    company = create_company(data.company_name, slug, data.company_email)
    user = create_user(
        company["id"], data.admin_name, data.admin_email,
        hash_password(data.password), role="admin"
    )
    token = create_access_token(user["id"], user["email"], user["role"], company["id"])
    return {
        "message": "Empresa criada com sucesso",
        "access_token": token,
        "token_type": "bearer",
        "company": {"id": company["id"], "name": company["name"], "slug": company["slug"]},
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
    }

@app.get("/api/companies/check-slug/{slug}")
def check_slug(slug: str):
    """Verifica se um slug já está ocupado (para feedback em tempo real no formulário)."""
    exists = get_company_by_slug(slug) is not None
    return {"slug": slug, "available": not exists}


# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login")
def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Email ou password incorrectos")
    if not user["active"]:
        raise HTTPException(403, "Conta desactivada. Contacte o administrador")
    company = get_company_by_id(user["company_id"])
    if not company or not company["active"]:
        raise HTTPException(403, "Empresa inactiva")
    token = create_access_token(user["id"], user["email"], user["role"], user["company_id"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "company": {"id": company["id"], "name": company["name"], "slug": company["slug"]},
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
    }

@app.get("/api/auth/me")
def me(current: dict = Depends(get_current_user)):
    user = get_user_by_id(int(current["sub"]))
    company = get_company_by_id(_cid(current))
    if not user: raise HTTPException(404, "Utilizador não encontrado")
    return {
        "id": user["id"], "name": user["name"],
        "email": user["email"], "role": user["role"],
        "company": {"id": company["id"], "name": company["name"], "slug": company["slug"]}
    }


# ── UTILIZADORES DA EMPRESA ───────────────────────────────────────────────────

@app.get("/api/users")
def get_users(current: dict = Depends(require_admin)):
    return list_users_by_company(_cid(current))

@app.post("/api/users/invite", status_code=201)
def invite_user(data: InviteUserRequest, current: dict = Depends(require_admin)):
    if get_user_by_email(data.email):
        raise HTTPException(400, "Email já registado")
    if data.role not in ("admin", "recruiter"):
        raise HTTPException(400, "Role inválido")
    user = create_user(_cid(current), data.name, data.email,
                       hash_password(data.password), data.role)
    return {"message": "Utilizador adicionado", "user": {
        "id": user["id"], "name": user["name"],
        "email": user["email"], "role": user["role"]
    }}

@app.patch("/api/users/{uid}/toggle")
def toggle_user(uid: int, current: dict = Depends(require_admin)):
    user = get_user_by_id(uid)
    if not user or user["company_id"] != _cid(current):
        raise HTTPException(404, "Utilizador não encontrado nesta empresa")
    if uid == int(current["sub"]):
        raise HTTPException(400, "Não podes desactivar a tua própria conta")
    toggle_user_active(uid, not user["active"])
    return {"message": "Estado actualizado"}


# ── CVs ───────────────────────────────────────────────────────────────────────

@app.post("/api/cv/upload", status_code=201)
async def upload_cv(file: UploadFile = File(...),
                    current: dict = Depends(require_recruiter)):
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
    return save_candidate(profile, _cid(current), int(current["sub"]))

@app.post("/api/cv/text", status_code=201)
def parse_cv_text(data: dict, current: dict = Depends(require_recruiter)):
    text = data.get("text", "")
    if len(text.strip()) < 50:
        raise HTTPException(400, "Texto do CV muito curto")
    profile = nlp.extract_info(text, data.get("filename", "cv.txt"))
    return save_candidate(profile, _cid(current), int(current["sub"]))

@app.get("/api/candidates")
def get_candidates(current: dict = Depends(require_recruiter)):
    return list_candidates(_cid(current))

@app.get("/api/candidates/{cid}")
def get_one(cid: str, current: dict = Depends(require_recruiter)):
    c = get_candidate(cid, _cid(current))
    if not c: raise HTTPException(404, "Candidato não encontrado")
    return c

@app.delete("/api/candidates/{cid}")
def remove_candidate(cid: str, current: dict = Depends(require_recruiter)):
    if not delete_candidate(cid, _cid(current)):
        raise HTTPException(404, "Candidato não encontrado")
    return {"message": "Candidato removido"}

@app.delete("/api/candidates")
def remove_all(current: dict = Depends(require_admin)):
    clear_candidates(_cid(current))
    return {"message": "Todos os candidatos removidos"}


# ── VAGAS ─────────────────────────────────────────────────────────────────────

@app.post("/api/jobs", status_code=201)
def create_job(data: JobRequest, current: dict = Depends(require_recruiter)):
    return save_job(data.model_dump(), _cid(current), int(current["sub"]))

@app.get("/api/jobs")
def get_jobs(current: dict = Depends(require_recruiter)):
    return list_jobs(_cid(current))

@app.get("/api/jobs/{jid}")
def get_one_job(jid: int, current: dict = Depends(require_recruiter)):
    j = get_job(jid, _cid(current))
    if not j: raise HTTPException(404, "Vaga não encontrada")
    return j

@app.delete("/api/jobs/{jid}")
def remove_job(jid: int, current: dict = Depends(require_recruiter)):
    if not delete_job(jid, _cid(current)):
        raise HTTPException(404, "Vaga não encontrada")
    return {"message": "Vaga removida"}


# ── MATCHING ──────────────────────────────────────────────────────────────────

@app.post("/api/match")
def match_all(data: JobRequest, current: dict = Depends(require_recruiter)):
    candidates = list_candidates(_cid(current))
    if not candidates:
        raise HTTPException(400, "Nenhum CV carregado")
    job_dict = data.model_dump()
    results = sorted(
        [matcher.match(c, job_dict) for c in candidates],
        key=lambda x: x["overall_score"], reverse=True
    )
    saved_job = save_job(job_dict, _cid(current), int(current["sub"]))
    save_match_results(saved_job["id"], _cid(current), results)
    return {"job_id": saved_job["id"], "results": results}

@app.post("/api/match/single/{cid}")
def match_one(cid: str, data: JobRequest, current: dict = Depends(require_recruiter)):
    c = get_candidate(cid, _cid(current))
    if not c: raise HTTPException(404, "Candidato não encontrado")
    return matcher.match(c, data.model_dump())

@app.get("/api/match/history/{jid}")
def match_history(jid: int, current: dict = Depends(require_recruiter)):
    return get_match_results(jid, _cid(current))


# ── STATS ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def stats(current: dict = Depends(require_recruiter)):
    return get_stats(_cid(current))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
