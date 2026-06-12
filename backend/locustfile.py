from locust import HttpUser, task, between
import json

# ─── Token partilhado (obtido no login) ───────────────────────────────────────
TOKEN = None

CV_EXEMPLO = """
António Silva
antonio@email.com | Luanda
SKILLS
Python, FastAPI, PostgreSQL, Docker
EXPERIENCE
Senior Dev - EmpresaX - 2019-2024
EDUCATION
Bachelor Computer Science - UAL - 2019
LANGUAGES
Portuguese, English
"""

VAGA = {
    "title": "Python Developer",
    "required_skills": ["Python", "FastAPI"],
    "preferred_skills": ["Docker"],
    "min_experience_years": 2,
    "education_level": "bachelor",
    "location": "Luanda"
}

class RecrutaAOUser(HttpUser):
    # Simula o tempo que um utilizador real espera entre acções (1 a 3 segundos)
    wait_time = between(1, 3)

    def on_start(self):
        r = self.client.post("/api/auth/login",
            json={
                "email": "admin@recruitao.ao",
                "password": "Admin@123"
            }
        )

        if r.status_code != 200:
            raise Exception("Falha no login")

        self.token = r.json()["access_token"]

        self.headers = { "Authorization": f"Bearer {self.token}" }


    @task(3)           # peso 3 — acção mais frequente
    def listar_candidatos(self):
        self.client.get("/api/candidates", headers=self.headers)

    @task(3)
    def ver_stats(self):
        self.client.get("/api/stats", headers=self.headers)

    @task(2)
    def upload_cv(self):
        self.client.post("/api/cv/text",
            json={"text": CV_EXEMPLO, "filename": "cv_teste.txt"},
            headers=self.headers)

    @task(2)
    def executar_matching(self):
        self.client.post("/api/match",
            json=VAGA,
            headers=self.headers)

    @task(1)           # peso 1 — acção menos frequente
    def health_check(self):
        self.client.get("/health")

    