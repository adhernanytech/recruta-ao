"""
locustfile.py — Testes de Carga e Stress do RecrutaAO
======================================================

Métricas recolhidas automaticamente pelo Locust:
  - RPS (Requests Per Second)
  - Tempo de resposta: médio, mínimo, máximo, percentis (50%, 95%, 99%)
  - Taxa de falhas (%)
  - Utilizadores simultâneos

Métricas calculadas manualmente (ver classe MetricsCollector):
  - MTTR  (Mean Time To Recover)   — tempo médio para recuperar de uma falha
  - MTBF  (Mean Time Between Failures) — tempo médio entre falhas consecutivas
  - CES   (Customer Effort Score)  — estimado pelo tempo de resposta
  - CSAT  (Customer Satisfaction)  — % de respostas dentro do limite aceitável
  - Erro % por endpoint

Como correr:
    pip install locust
    locust -f locustfile.py --host=http://localhost:8000

    Depois abre: http://localhost:8089
    Define: Users=50, Spawn Rate=5, Duration=2m

Linha de comandos (sem interface):
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 50 --spawn-rate 5 --run-time 2m --headless --csv=resultados
"""

import time
import json
import csv
import os
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner

# ─── CVs e Vaga de teste ─────────────────────────────────────────────────────

CV_SENIOR = """António Silva
antonio@email.com | +244 923 456 789 | Luanda
SUMMARY
Senior Software Engineer with 7 years of experience.
SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, React, Machine Learning
EXPERIENCE
Senior Developer - Sonangol Digital - Luanda
2017 - 2024
EDUCATION
Bachelor in Computer Science - UAL - 2017
LANGUAGES
Portuguese, English
"""

CV_JUNIOR = """Carlos Nkosi
carlos@email.com | Luanda
SKILLS
HTML, CSS, JavaScript, React, Python, SQL
EXPERIENCE
Web Developer Intern - StartupAO - 2023 (6 months)
EDUCATION
Bachelor IT - Instituto Politecnico - 2023
LANGUAGES
Portuguese, English
"""

VAGA_PYTHON = {
    "title": "Senior Python Developer",
    "description": "Backend developer com APIs REST",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "AWS"],
    "min_experience_years": 3,
    "education_level": "bachelor",
    "location": "Luanda"
}

# ─── Colector de Métricas MTTR / MTBF / CSAT / CES ───────────────────────────

class MetricsCollector:
    """
    Recolhe eventos de falha/recuperação para calcular MTTR e MTBF.

    MTBF = Tempo Total de Operação / Número de Falhas
    MTTR = Soma dos Tempos de Recuperação / Número de Recuperações

    CES  = estimado pelo tempo de resposta médio:
           < 200ms  → Esforço Baixo  (muito fácil de usar)
           200-500ms → Esforço Médio
           > 500ms  → Esforço Alto   (utilizador sente lentidão)

    CSAT = % de pedidos com resposta em menos de 500ms (limiar aceitável)
    """

    def __init__(self):
        self.failures = []           # lista de timestamps de falhas
        self.recoveries = []         # lista de timestamps de recuperações
        self.response_times = []     # todos os tempos de resposta (ms)
        self.total_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
        self._in_failure = False
        self._failure_start = None
        self._recovery_times = []

    def record_request(self, success: bool, response_time_ms: float):
        self.total_requests += 1
        self.response_times.append(response_time_ms)

        if not success:
            self.failed_requests += 1
            self.failures.append(time.time())
            if not self._in_failure:
                self._in_failure = True
                self._failure_start = time.time()
        else:
            if self._in_failure:
                # recuperou de uma falha
                recovery_duration = time.time() - self._failure_start
                self._recovery_times.append(recovery_duration)
                self.recoveries.append(time.time())
                self._in_failure = False
                self._failure_start = None

    def calculate(self) -> dict:
        elapsed = time.time() - self.start_time
        n_failures = len(self.failures)
        avg_rt = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        csat_count = sum(1 for rt in self.response_times if rt < 500)
        csat = (csat_count / len(self.response_times) * 100) if self.response_times else 0

        # MTBF
        if n_failures > 1:
            intervals = [self.failures[i+1] - self.failures[i]
                         for i in range(len(self.failures)-1)]
            mtbf = sum(intervals) / len(intervals)
        elif n_failures == 0:
            mtbf = elapsed   # sem falhas = uptime total
        else:
            mtbf = elapsed

        # MTTR
        mttr = (sum(self._recovery_times) / len(self._recovery_times)
                if self._recovery_times else 0)

        # CES
        if avg_rt < 200:
            ces_label = "Baixo ✅ (sistema rápido)"
        elif avg_rt < 500:
            ces_label = "Médio ⚠️ (aceitável)"
        else:
            ces_label = "Alto ❌ (lento para o utilizador)"

        return {
            "duracao_teste_s":     round(elapsed, 1),
            "total_requests":      self.total_requests,
            "failed_requests":     self.failed_requests,
            "taxa_erro_pct":       round(self.failed_requests / max(self.total_requests,1) * 100, 2),
            "MTBF_s":              round(mtbf, 2),
            "MTTR_s":              round(mttr, 2),
            "CSAT_pct":            round(csat, 1),
            "CES_label":           ces_label,
            "tempo_resposta_medio_ms": round(avg_rt, 1),
            "tempo_resposta_max_ms":   round(max(self.response_times, default=0), 1),
            "n_falhas_detectadas": n_failures,
            "n_recuperacoes":      len(self._recovery_times),
        }

    def print_report(self):
        m = self.calculate()
        print("\n" + "="*60)
        print("  📊 RELATÓRIO DE MÉTRICAS — RecrutaAO")
        print("="*60)
        print(f"  Duração do teste         : {m['duracao_teste_s']}s")
        print(f"  Total de pedidos         : {m['total_requests']}")
        print(f"  Pedidos falhados         : {m['failed_requests']}")
        print(f"  Taxa de erro             : {m['taxa_erro_pct']}%")
        print("-"*60)
        print(f"  MTBF (entre falhas)      : {m['MTBF_s']}s")
        print(f"  MTTR (recuperação)       : {m['MTTR_s']}s")
        print(f"  CSAT (respostas <500ms)  : {m['CSAT_pct']}%")
        print(f"  CES  (esforço estimado)  : {m['CES_label']}")
        print(f"  Tempo resposta médio     : {m['tempo_resposta_medio_ms']}ms")
        print(f"  Tempo resposta máximo    : {m['tempo_resposta_max_ms']}ms")
        print("="*60)

    def save_csv(self, filename="metricas_recruitao.csv"):
        m = self.calculate()
        m["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=m.keys())
            writer.writeheader()
            writer.writerow(m)
        print(f"\n  ✅ Métricas guardadas em: {path}")


# Instância global do colector
metrics = MetricsCollector()


# ─── Hooks Locust (eventos globais) ──────────────────────────────────────────

@events.request.add_listener
def on_request(request_type, name, response_time, response_length,
               exception, **kwargs):
    success = exception is None
    metrics.record_request(success, response_time)


@events.quitting.add_listener
def on_quit(environment, **kwargs):
    metrics.print_report()
    metrics.save_csv()


# ─── Cenários de Utilizadores ─────────────────────────────────────────────────

class RecruiterUser(HttpUser):
    """
    Simula um recruiter típico:
    - Faz login
    - Carrega CVs
    - Executa matching
    - Consulta candidatos e estatísticas
    """
    wait_time = between(1, 3)   # espera realista entre acções

    def on_start(self):
        """Login automático ao iniciar o utilizador virtual."""
        r = self.client.post("/api/auth/login", json={
            "email": "admin@recruitao.ao",
            "password": "Admin@123"
        }, name="[AUTH] Login")

        if r.status_code == 200:
            self.token = r.json().get("access_token", "")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            self.token = ""
            self.headers = {}

    # ── Tarefas com pesos (número = frequência relativa) ──────────────────

    @task(4)
    def listar_candidatos(self):
        """Acção mais frequente — recruiter consulta o pool."""
        self.client.get("/api/candidates",
                        headers=self.headers,
                        name="[CANDIDATOS] Listar todos")

    @task(4)
    def ver_estatisticas(self):
        self.client.get("/api/stats",
                        headers=self.headers,
                        name="[STATS] Ver estatísticas")

    @task(3)
    def upload_cv_texto(self):
        """Carrega um CV em texto — activa o motor NLP."""
        self.client.post("/api/cv/text",
            json={"text": CV_SENIOR, "filename": "cv_carga.txt"},
            headers=self.headers,
            name="[CV] Upload via texto (NLP)")

    @task(3)
    def executar_matching(self):
        """Acção mais pesada — activa NLP + MatchingEngine para todos os CVs."""
        self.client.post("/api/match",
            json=VAGA_PYTHON,
            headers=self.headers,
            name="[MATCH] Matching completo")

    @task(2)
    def listar_vagas(self):
        self.client.get("/api/jobs",
                        headers=self.headers,
                        name="[VAGAS] Listar vagas")

    @task(2)
    def criar_vaga(self):
        self.client.post("/api/jobs",
            json=VAGA_PYTHON,
            headers=self.headers,
            name="[VAGAS] Criar vaga")

    @task(1)
    def health_check(self):
        """Acção leve — simula monitorização."""
        self.client.get("/health", name="[SISTEMA] Health check")

    @task(1)
    def ver_perfil_proprio(self):
        self.client.get("/api/auth/me",
                        headers=self.headers,
                        name="[AUTH] Ver perfil")


class StressUser(HttpUser):
    """
    Utilizador de stress — sem espera, máxima pressão.
    Usar apenas no cenário de stress (não no de carga normal).
    Descomenta a linha weight= abaixo para incluir no mix.
    """
    wait_time = between(0, 0.5)
    # weight = 0    # ← muda para 1 para activar no teste de stress

    def on_start(self):
        r = self.client.post("/api/auth/login", json={
            "email": "admin@recruitao.ao", "password": "Admin@123"
        }, name="[STRESS] Login")
        self.token = r.json().get("access_token", "") if r.status_code == 200 else ""
        self.headers = {"Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"}

    @task(5)
    def stress_matching(self):
        """Endpoint mais pesado — martela o motor de matching."""
        self.client.post("/api/match",
            json=VAGA_PYTHON,
            headers=self.headers,
            name="[STRESS] Matching")

    @task(3)
    def stress_upload(self):
        self.client.post("/api/cv/text",
            json={"text": CV_JUNIOR, "filename": "stress.txt"},
            headers=self.headers,
            name="[STRESS] Upload CV")

    @task(2)
    def stress_list(self):
        self.client.get("/api/candidates",
                        headers=self.headers,
                        name="[STRESS] Listar candidatos")