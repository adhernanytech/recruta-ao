"""
tests.py — Testes Automatizados do RecrutaAO
============================================
Cobre 3 níveis:

  1. Testes Unitários    — NLPEngine, MatchingEngine, auth helpers
  2. Testes de Integração — endpoints FastAPI via TestClient
  3. Testes de Aceitação  — fluxos completos do utilizador

Como correr:
    pip install pytest
    pytest tests.py -v

Para relatório de cobertura:
    pip install pytest-cov
    pytest tests.py -v --cov=. --cov-report=html
"""

import os
import json
import time
import pytest

os.environ["DB_PATH"] = "test_recruitao.db"   # BD isolada para testes

from fastapi.testclient import TestClient
from main import app
from database import init_db, clear_candidates
from auth import hash_password, verify_password, create_access_token, decode_token
from nlp_engine import NLPEngine, MatchingEngine

client = TestClient(app)

# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Inicializa a BD de teste uma única vez por sessão."""
    init_db()
    yield
    # Limpeza final
    if os.path.exists("test_recruitao.db"):
        os.remove("test_recruitao.db")

@pytest.fixture(autouse=True)
def clean_candidates():
    """Limpa candidatos antes de cada teste."""
    clear_candidates()
    yield

@pytest.fixture(scope="session")
def admin_token():
    """Obtém token do admin criado no startup."""
    r = client.post("/api/auth/login",
                    json={"email": "admin@recruitao.ao", "password": "Admin@123"})
    assert r.status_code == 200
    return r.json()["access_token"]

@pytest.fixture
def recruiter_token(admin_token):
    """Cria um recruiter e devolve o seu token."""
    email = f"recruiter_{int(time.time())}@test.ao"
    r = client.post("/api/auth/register",
                    json={"name": "Recruiter Teste", "email": email,
                          "password": "Test@123", "role": "recruiter"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    # register é público, não precisa de token
    r = client.post("/api/auth/register",
                    json={"name": "Recruiter Teste", "email": email,
                          "password": "Test@123", "role": "recruiter"})
    if r.status_code == 400:  # já existe, faz login
        r = client.post("/api/auth/login",
                        json={"email": email, "password": "Test@123"})
    return r.json()["access_token"]

@pytest.fixture
def auth_headers(recruiter_token):
    return {"Authorization": f"Bearer {recruiter_token}"}

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

CV_SENIOR = """António Manuel Silva
Email: antonio.silva@email.com
Phone: +244 923 456 789
Location: Luanda

SUMMARY
Senior Software Engineer with 7 years of experience building scalable APIs.

EXPERIENCE
Senior Software Engineer
Sonangol Digital - Luanda
2017 - 2024
Built Python microservices and React dashboards.

EDUCATION
Bachelor in Computer Science
Universidade Agostinho Neto - 2017

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, React, Machine Learning

LANGUAGES
Portuguese, English
"""

CV_JUNIOR = """Carlos Nkosi
carlos@email.com
Luanda

EDUCATION
Bachelor Information Technology
Instituto Politecnico - 2023

SKILLS
HTML, CSS, JavaScript, React, Python, SQL

EXPERIENCE
Web Developer Intern - StartupAO - 2023 (6 months)

LANGUAGES
Portuguese, English
"""

CV_UNRELATED = """Maria Contadora
maria.conta@email.com
Luanda

SUMMARY
Contabilista com 10 anos de experiência em auditoria e finanças.

EXPERIENCE
Contabilista Sénior - Banco BFA - Luanda
2014 - 2024
Gestão de contas, reconciliações bancárias, relatórios financeiros.

EDUCATION
Licenciatura em Contabilidade
UCAN - 2014

SKILLS
Excel, SAP, Contabilidade, Auditoria, Fiscalidade

LANGUAGES
Portuguese, French
"""

JOB_PYTHON = {
    "title": "Senior Python Developer",
    "description": "Backend developer com experiência em APIs",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "AWS"],
    "min_experience_years": 3,
    "education_level": "bachelor",
    "location": "Luanda"
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. TESTES UNITÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

class TestPasswordHashing:

    def test_hash_is_not_plaintext(self):
        h = hash_password("MinhaPass@123")
        assert h != "MinhaPass@123"
        assert len(h) > 20

    def test_correct_password_verifies(self):
        h = hash_password("MinhaPass@123")
        assert verify_password("MinhaPass@123", h) is True

    def test_wrong_password_fails(self):
        h = hash_password("MinhaPass@123")
        assert verify_password("OutraPass@456", h) is False

    def test_empty_password_fails(self):
        h = hash_password("MinhaPass@123")
        assert verify_password("", h) is False

    def test_two_hashes_are_different(self):
        """Salt aleatório garante hashes diferentes para a mesma password."""
        h1 = hash_password("igual")
        h2 = hash_password("igual")
        assert h1 != h2
        assert verify_password("igual", h1)
        assert verify_password("igual", h2)


class TestJWT:

    def test_token_criado_e_decodificado(self):
        token = create_access_token(1, "user@test.ao", "recruiter")
        data  = decode_token(token)
        assert data["sub"] == "1"
        assert data["email"] == "user@test.ao"
        assert data["role"] == "recruiter"

    def test_token_invalido_lanca_excecao(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            decode_token("token.invalido.aqui")

    def test_token_expirado_lanca_excecao(self):
        import hmac as _hmac, hashlib, base64, json as _json, time as _time
        from auth import SECRET_KEY, _b64url_encode
        from fastapi import HTTPException
        header  = _b64url_encode(_json.dumps({"alg":"HS256","typ":"JWT"}).encode())
        payload = _b64url_encode(_json.dumps({
            "sub":"1","email":"x@x.com","role":"recruiter",
            "iat": int(_time.time()) - 7200,
            "exp": int(_time.time()) - 3600    # expirado há 1 hora
        }).encode())
        sig = _b64url_encode(
            _hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        )
        with pytest.raises(HTTPException):
            decode_token(f"{header}.{payload}.{sig}")


class TestNLPExtraction:
    nlp = NLPEngine()

    def test_extrai_nome(self):
        p = self.nlp.extract_info(CV_SENIOR, "cv.txt")
        assert "António" in p["name"] or "Silva" in p["name"]

    def test_extrai_email(self):
        p = self.nlp.extract_info(CV_SENIOR)
        assert p["email"] == "antonio.silva@email.com"

    def test_extrai_telefone(self):
        p = self.nlp.extract_info(CV_SENIOR)
        assert "244" in p["phone"] or "923" in p["phone"]

    def test_extrai_localizacao(self):
        p = self.nlp.extract_info(CV_SENIOR)
        assert p["location"].lower() == "luanda"

    def test_extrai_skills_corretas(self):
        p = self.nlp.extract_info(CV_SENIOR)
        skills_lower = [s.lower() for s in p["skills"]]
        assert "python" in skills_lower
        assert "fastapi" in skills_lower
        assert "react" in skills_lower

    def test_nao_extrai_skills_falsas(self):
        """CV de contabilidade não deve ter skills de programação."""
        p = self.nlp.extract_info(CV_UNRELATED)
        skills_lower = [s.lower() for s in p["skills"]]
        assert "python" not in skills_lower
        assert "fastapi" not in skills_lower
        assert "docker" not in skills_lower

    def test_extrai_experiencia_anos(self):
        p = self.nlp.extract_info(CV_SENIOR)
        assert p["total_experience_years"] >= 5

    def test_extrai_educacao(self):
        p = self.nlp.extract_info(CV_SENIOR)
        assert len(p["education"]) >= 1
        assert "bachelor" in p["education"][0]["degree"].lower() or \
               "computer" in p["education"][0]["degree"].lower()

    def test_extrai_idiomas(self):
        p = self.nlp.extract_info(CV_SENIOR)
        langs_lower = [l.lower() for l in p["languages"]]
        assert "portuguese" in langs_lower
        assert "english" in langs_lower

    def test_cv_vazio_retorna_desconhecido(self):
        p = self.nlp.extract_info("Texto muito curto", "cv.txt")
        assert p["name"] != ""
        assert p["skills"] == []


class TestMatchingEngine:
    engine = MatchingEngine()
    nlp    = NLPEngine()

    def _profile(self, text):
        return self.nlp.extract_info(text)

    def test_senior_score_alto(self):
        r = self.engine.match(self._profile(CV_SENIOR), JOB_PYTHON)
        assert r["overall_score"] >= 70, f"Score esperado ≥70, obtido {r['overall_score']}"

    def test_junior_score_medio(self):
        r = self.engine.match(self._profile(CV_JUNIOR), JOB_PYTHON)
        assert r["overall_score"] < 70

    def test_nao_relacionado_score_baixo(self):
        r = self.engine.match(self._profile(CV_UNRELATED), JOB_PYTHON)
        assert r["overall_score"] < 30, f"Score esperado <30, obtido {r['overall_score']}"

    def test_skills_matched_corretas(self):
        r = self.engine.match(self._profile(CV_SENIOR), JOB_PYTHON)
        matched_lower = [s.lower() for s in r["matched_skills"]]
        assert "python" in matched_lower

    def test_skills_missing_corretas(self):
        r = self.engine.match(self._profile(CV_JUNIOR), JOB_PYTHON)
        # Junior não tem FastAPI nem PostgreSQL
        missing_lower = [s.lower() for s in r["missing_skills"]]
        assert "fastapi" in missing_lower or "postgresql" in missing_lower

    def test_sem_skills_obrigatorias_score_zero_skills(self):
        r = self.engine.match(self._profile(CV_UNRELATED), JOB_PYTHON)
        assert r["skill_score"] == 0.0

    def test_ranking_correto(self):
        profiles = [
            self._profile(CV_SENIOR),
            self._profile(CV_JUNIOR),
            self._profile(CV_UNRELATED)
        ]
        results = sorted(
            [self.engine.match(p, JOB_PYTHON) for p in profiles],
            key=lambda x: x["overall_score"], reverse=True
        )
        # Sénior deve ficar em primeiro
        assert results[0]["candidate"]["name"] != results[2]["candidate"]["name"]
        assert results[0]["overall_score"] >= results[1]["overall_score"] >= results[2]["overall_score"]

    def test_recomendacao_correta(self):
        r_high = self.engine.match(self._profile(CV_SENIOR), JOB_PYTHON)
        r_low  = self.engine.match(self._profile(CV_UNRELATED), JOB_PYTHON)
        assert "✅" in r_high["recommendation"] or "👍" in r_high["recommendation"]
        assert "❌" in r_low["recommendation"] or "⚠️" in r_low["recommendation"]


# ══════════════════════════════════════════════════════════════════════════════
# 2. TESTES DE INTEGRAÇÃO (endpoints HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoints:

    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "online"

    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert "healthy" in r.json()["status"]


class TestAuthEndpoints:

    def test_register_sucesso(self):
        r = client.post("/api/auth/register", json={
            "name": "Novo Utilizador",
            "email": f"novo_{int(time.time())}@test.ao",
            "password": "Pass@123",
            "role": "recruiter"
        })
        assert r.status_code == 201
        assert "access_token" in r.json()
        assert r.json()["user"]["role"] == "recruiter"

    def test_register_email_duplicado(self):
        email = f"dup_{int(time.time())}@test.ao"
        client.post("/api/auth/register",
                    json={"name":"A","email":email,"password":"Pass@123"})
        r = client.post("/api/auth/register",
                        json={"name":"B","email":email,"password":"Pass@123"})
        assert r.status_code == 400

    def test_register_password_curta(self):
        r = client.post("/api/auth/register", json={
            "name": "Teste", "email": "short@test.ao", "password": "123"
        })
        assert r.status_code == 400

    def test_login_sucesso(self, admin_headers):
        r = client.post("/api/auth/login",
                        json={"email": "admin@recruitao.ao", "password": "Admin@123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_password_errada(self):
        r = client.post("/api/auth/login",
                        json={"email": "admin@recruitao.ao", "password": "errada"})
        assert r.status_code == 401

    def test_login_email_inexistente(self):
        r = client.post("/api/auth/login",
                        json={"email": "nao_existe@test.ao", "password": "Pass@123"})
        assert r.status_code == 401

    def test_me_autenticado(self, auth_headers):
        r = client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert "email" in r.json()

    def test_me_sem_token(self):
        r = client.get("/api/auth/me")
        assert r.status_code == 403

    def test_me_token_invalido(self):
        r = client.get("/api/auth/me",
                       headers={"Authorization": "Bearer token.falso.aqui"})
        assert r.status_code == 401


class TestCandidateEndpoints:

    def test_upload_cv_texto_sucesso(self, auth_headers):
        r = client.post("/api/cv/text",
                        json={"text": CV_SENIOR, "filename": "antonio.txt"},
                        headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["name"] != ""
        assert isinstance(r.json()["skills"], list)

    def test_upload_cv_texto_curto(self, auth_headers):
        r = client.post("/api/cv/text",
                        json={"text": "Olá", "filename": "cv.txt"},
                        headers=auth_headers)
        assert r.status_code == 400

    def test_upload_sem_autenticacao(self):
        r = client.post("/api/cv/text",
                        json={"text": CV_SENIOR})
        assert r.status_code == 403

    def test_listar_candidatos(self, auth_headers):
        client.post("/api/cv/text", json={"text": CV_SENIOR}, headers=auth_headers)
        r = client.get("/api/candidates", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_obter_candidato_por_id(self, auth_headers):
        r1 = client.post("/api/cv/text", json={"text": CV_SENIOR}, headers=auth_headers)
        cid = r1.json()["id"]
        r2 = client.get(f"/api/candidates/{cid}", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["id"] == cid

    def test_obter_candidato_inexistente(self, auth_headers):
        r = client.get("/api/candidates/ID_FALSO_999", headers=auth_headers)
        assert r.status_code == 404

    def test_eliminar_candidato(self, auth_headers):
        r1 = client.post("/api/cv/text", json={"text": CV_SENIOR}, headers=auth_headers)
        cid = r1.json()["id"]
        r2 = client.delete(f"/api/candidates/{cid}", headers=auth_headers)
        assert r2.status_code == 200
        r3 = client.get(f"/api/candidates/{cid}", headers=auth_headers)
        assert r3.status_code == 404

    def test_limpar_todos_requer_admin(self, auth_headers, admin_headers):
        # recruiter não pode limpar tudo
        r = client.delete("/api/candidates", headers=auth_headers)
        assert r.status_code == 403
        # admin pode
        r = client.delete("/api/candidates", headers=admin_headers)
        assert r.status_code == 200


class TestJobEndpoints:

    def test_criar_vaga(self, auth_headers):
        r = client.post("/api/jobs", json=JOB_PYTHON, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["title"] == JOB_PYTHON["title"]
        assert isinstance(r.json()["required_skills"], list)

    def test_listar_vagas(self, auth_headers):
        client.post("/api/jobs", json=JOB_PYTHON, headers=auth_headers)
        r = client.get("/api/jobs", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_obter_vaga_por_id(self, auth_headers):
        r1 = client.post("/api/jobs", json=JOB_PYTHON, headers=auth_headers)
        jid = r1.json()["id"]
        r2 = client.get(f"/api/jobs/{jid}", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["id"] == jid

    def test_eliminar_vaga(self, auth_headers):
        r1 = client.post("/api/jobs", json=JOB_PYTHON, headers=auth_headers)
        jid = r1.json()["id"]
        r2 = client.delete(f"/api/jobs/{jid}", headers=auth_headers)
        assert r2.status_code == 200

    def test_vaga_sem_autenticacao(self):
        r = client.post("/api/jobs", json=JOB_PYTHON)
        assert r.status_code == 403


class TestMatchingEndpoints:

    def _load_cv(self, text, headers):
        return client.post("/api/cv/text", json={"text": text}, headers=headers)

    def test_matching_retorna_resultados(self, auth_headers):
        self._load_cv(CV_SENIOR, auth_headers)
        self._load_cv(CV_JUNIOR, auth_headers)
        r = client.post("/api/match", json=JOB_PYTHON, headers=auth_headers)
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) == 2
        # Ordenados por score decrescente
        assert results[0]["overall_score"] >= results[1]["overall_score"]

    def test_matching_sem_candidatos(self, auth_headers):
        r = client.post("/api/match", json=JOB_PYTHON, headers=auth_headers)
        assert r.status_code == 400

    def test_matching_nao_relacionado_score_baixo(self, auth_headers):
        self._load_cv(CV_UNRELATED, auth_headers)
        r = client.post("/api/match", json=JOB_PYTHON, headers=auth_headers)
        results = r.json()["results"]
        assert results[0]["overall_score"] < 30

    def test_matching_single(self, auth_headers):
        r1 = self._load_cv(CV_SENIOR, auth_headers)
        cid = r1.json()["id"]
        r2 = client.post(f"/api/match/single/{cid}",
                         json=JOB_PYTHON, headers=auth_headers)
        assert r2.status_code == 200
        assert "overall_score" in r2.json()

    def test_historico_matching(self, auth_headers):
        self._load_cv(CV_SENIOR, auth_headers)
        r1 = client.post("/api/match", json=JOB_PYTHON, headers=auth_headers)
        jid = r1.json()["job_id"]
        r2 = client.get(f"/api/match/history/{jid}", headers=auth_headers)
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)


class TestStatsEndpoints:

    def test_stats_com_candidatos(self, auth_headers):
        client.post("/api/cv/text", json={"text": CV_SENIOR}, headers=auth_headers)
        r = client.get("/api/stats", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total_candidates"] >= 1
        assert "top_skills" in data

    def test_stats_sem_candidatos(self, auth_headers):
        r = client.get("/api/stats", headers=auth_headers)
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 3. TESTES DE ACEITAÇÃO (fluxos completos)
# ══════════════════════════════════════════════════════════════════════════════

class TestUserJourneys:

    def test_fluxo_completo_recruiter(self):
        """
        Cenário: Um recruiter regista-se, carrega 3 CVs,
        define uma vaga, executa matching e vê o ranking.
        """
        # 1. Registo
        email = f"recruiter_journey_{int(time.time())}@test.ao"
        r = client.post("/api/auth/register", json={
            "name": "Jorge Recruiter",
            "email": email,
            "password": "Teste@456",
            "role": "recruiter"
        })
        assert r.status_code == 201
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Carrega 3 CVs
        for cv in [CV_SENIOR, CV_JUNIOR, CV_UNRELATED]:
            r = client.post("/api/cv/text", json={"text": cv}, headers=headers)
            assert r.status_code == 201

        # 3. Confirma 3 candidatos
        r = client.get("/api/candidates", headers=headers)
        assert len(r.json()) == 3

        # 4. Executa matching
        r = client.post("/api/match", json=JOB_PYTHON, headers=headers)
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) == 3

        # 5. O sénior deve ter score mais alto que não-relacionado
        scores = [res["overall_score"] for res in results]
        assert scores[0] >= scores[-1]
        assert scores[-1] < 30   # contabilista não deve ter score alto

        # 6. Vê estatísticas
        r = client.get("/api/stats", headers=headers)
        assert r.json()["total_candidates"] == 3

    def test_fluxo_admin_gestao_utilizadores(self, admin_headers):
        """
        Cenário: Admin cria uma conta, vê a lista e desactiva um utilizador.
        """
        # 1. Lista utilizadores
        r = client.get("/api/users", headers=admin_headers)
        assert r.status_code == 200
        initial_count = len(r.json())

        # 2. Recruiter regista-se
        email = f"para_desactivar_{int(time.time())}@test.ao"
        r = client.post("/api/auth/register", json={
            "name": "Utilizador Temp",
            "email": email,
            "password": "Pass@123"
        })
        uid = r.json()["user"]["id"]

        # 3. Admin confirma novo utilizador na lista
        r = client.get("/api/users", headers=admin_headers)
        assert len(r.json()) == initial_count + 1

        # 4. Admin desactiva o utilizador
        r = client.patch(f"/api/users/{uid}/toggle", headers=admin_headers)
        assert r.status_code == 200

        # 5. Utilizador desactivado não consegue fazer login
        r = client.post("/api/auth/login",
                        json={"email": email, "password": "Pass@123"})
        assert r.status_code == 403

    def test_recruiter_nao_acede_a_rotas_admin(self, auth_headers):
        """Recruiter não pode ver utilizadores nem limpar candidatos."""
        r1 = client.get("/api/users", headers=auth_headers)
        assert r1.status_code == 403

        r2 = client.delete("/api/candidates", headers=auth_headers)
        assert r2.status_code == 403

    def test_acesso_sem_token_bloqueado(self):
        """Todas as rotas protegidas devem recusar sem token."""
        endpoints = [
            ("GET",  "/api/candidates"),
            ("GET",  "/api/jobs"),
            ("GET",  "/api/stats"),
            ("POST", "/api/cv/text"),
        ]
        for method, path in endpoints:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json={})
            assert r.status_code in (403, 422), \
                f"{method} {path} deveria retornar 403, obteve {r.status_code}"


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER DIRECTO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v",
         "--tb=short", "--no-header"],
        capture_output=False
    )
    sys.exit(result.returncode)