# 🤖 RecruitAI — CV Intelligence Platform

Plataforma de recrutamento com IA para extracção de informação de CVs e matching de candidatos com vagas.

---

## 📐 Arquitectura

```
cv-recruiter/
├── backend/
│   ├── main.py              # FastAPI app — API + NLP Engine + Matching Engine
│   ├── requirements.txt     # Dependências Python
│   └── sample_cvs/          # CVs de teste
│       ├── cv_antonio_silva.txt
│       ├── cv_maria_ferreira.txt
│       └── cv_carlos_nkosi.txt
│
└── frontend/
    ├── package.json
    ├── public/index.html
    └── src/
        ├── index.js         # Entry point React
        └── App.jsx          # Aplicação completa (UI + lógica)
```

---

## 🚀 Arranque Rápido

### 1. Backend (Python)

```bash
cd backend
pip install -r requirements.txt
python main.py
# → API disponível em http://localhost:8000
# → Documentação Swagger em http://localhost:8000/docs
```

### 2. Frontend (React)

```bash
cd frontend
npm install
npm start
# → App disponível em http://localhost:3000
```

---

## 🧠 Motor NLP — Como Funciona

### Extracção de Informação (`NLPEngine`)

O motor usa **expressões regulares + análise de padrões lexicais** para extrair:

| Campo              | Técnica                                        |
|--------------------|------------------------------------------------|
| Nome               | Detecção de linhas com palavras capitalizadas  |
| Email / Telefone   | Regex patterns RFC-5321 e E.164               |
| Skills             | Taxonomia de 80+ skills por categoria         |
| Experiência        | Regex de anos explícitos + cálculo por datas  |
| Educação           | Pattern matching em títulos académicos        |
| Idiomas            | Dicionário multilíngue de 14 idiomas         |
| Certificações      | Detecção de emissores conhecidos (AWS, etc.)  |

### Taxonomia de Skills

```python
TECH_SKILLS = {
    "programming": ["python", "java", "javascript", ...],
    "web":         ["react", "angular", "vue", "node.js", ...],
    "data":        ["pandas", "tensorflow", "scikit-learn", ...],
    "cloud":       ["aws", "azure", "docker", "kubernetes", ...],
    "databases":   ["postgresql", "mongodb", "redis", ...],
    "soft":        ["leadership", "agile", "scrum", ...]
}
```

---

## 🎯 Motor de Matching (`MatchingEngine`)

### Fórmula de Scoring

```
Score = Skills×0.45 + Experiência×0.25 + Educação×0.15 + Idiomas×0.10 + Localização×0.05
```

### Skills Score
- **Required skills**: peso 75% — skills obrigatórias definidas na vaga
- **Preferred skills**: peso 25% — skills preferenciais
- **Matching semântico**: aliases (ml↔machine learning, js↔javascript, etc.)

### Experience Score
- Score linear até ao mínimo exigido
- Bónus até +20% para excesso de experiência

### Education Score
- Hierarquia: PhD(5) > Master(4) > Bachelor(3) > Diploma(2) > Secondary(1)
- Score proporcional ao nível do candidato vs. nível exigido

### Recomendação
| Score    | Recomendação                              |
|----------|-------------------------------------------|
| ≥ 85%    |  Fortemente Recomendado                 |
| 70–84%   |  Recomendado                            |
| 55–69%   |  Considerar                             |
| 40–54%   |  Revisão Necessária                     |
| < 40%    |  Não Adequado                           |

---

## 📡 API Endpoints

| Método | Endpoint                      | Descrição                          |
|--------|-------------------------------|-------------------------------------|
| POST   | `/api/cv/upload`              | Upload ficheiro CV                 |
| POST   | `/api/cv/text`                | Parse CV via texto raw             |
| GET    | `/api/candidates`             | Listar todos os candidatos         |
| GET    | `/api/candidates/{id}`        | Detalhes de um candidato           |
| DELETE | `/api/candidates/{id}`        | Remover candidato                  |
| DELETE | `/api/candidates`             | Limpar todos os candidatos         |
| POST   | `/api/match`                  | Matching de todos os candidatos    |
| POST   | `/api/match/single/{id}`      | Matching de candidato específico   |
| GET    | `/api/stats`                  | Estatísticas do pool               |
| GET    | `/health`                     | Health check                       |

### Exemplo — Criar Vaga e Fazer Matching

```bash
curl -X POST http://localhost:8000/api/match \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "Backend developer com ML",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "AWS"],
    "min_experience_years": 3,
    "education_level": "bachelor",
    "location": "Luanda"
  }'
```

---

## 🖥️ Frontend — Funcionalidades

### Separadores

1. **Upload CVs** — Drag & drop ou colar texto. NLP extrai info automaticamente.
2. **Matching** — Define a vaga (skills, experiência, educação). Executa matching.
3. **Candidatos** — Pool completo com perfil detalhado de cada candidato.
4. **Resultados** — Ranking por score com barras de skills, experiência, educação.
5. **Analytics** — Estatísticas do pool: top skills, experiência média.

---

## 🔧 Extensões Futuras

- [ ] Suporte a PDF com `PyMuPDF` / `pdfminer`
- [ ] Embeddings semânticos com `sentence-transformers`
- [ ] Persistência com PostgreSQL + SQLAlchemy
- [ ] Autenticação JWT para múltiplos recruiters
- [ ] Export de resultados para Excel/PDF
- [ ] Integração com LinkedIn / APIs de emprego
- [ ] Modelo de ML treinado em dados de recrutamento

---

## 🛠️ Stack Tecnológico

| Camada    | Tecnologia                              |
|-----------|-----------------------------------------|
| Backend   | Python 3.11 · FastAPI · Uvicorn        |
| NLP       | Regex · Pattern Matching · TF-IDF like |
| Frontend  | React 18 · CSS-in-JS · Inter + Syne   |
| API       | REST JSON · CORS habilitado            |
| Dev       | Hot reload (uvicorn --reload + CRA)    |
