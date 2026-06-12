"""
nlp_engine.py — Motor NLP de extracção e matching de CVs (RecrutaAO)
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class NLPEngine:
    TECH_SKILLS = {
        "programming": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
                        "kotlin", "swift", "php", "ruby", "scala", "matlab"],
        "web": ["react", "angular", "vue", "node.js", "nodejs", "django", "flask", "fastapi",
                "spring", "laravel", "express", "html", "css", "sass", "webpack"],
        "data": ["pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "keras", "spark",
                 "hadoop", "tableau", "power bi", "sql", "nosql", "machine learning",
                 "deep learning", "nlp", "computer vision", "data science", "analytics"],
        "cloud": ["aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
                  "ansible", "jenkins", "ci/cd", "devops", "linux", "bash"],
        "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "oracle",
                      "sqlite", "cassandra", "dynamodb", "firebase"],
        "soft": ["leadership", "communication", "teamwork", "problem solving",
                 "critical thinking", "project management", "agile", "scrum",
                 "kanban", "time management"]
    }

    EDUCATION_LEVELS = {
        "phd": 5, "doctorate": 5, "doutoramento": 5, "doutorado": 5,
        "master": 4, "masters": 4, "mestrado": 4, "mba": 4, "msc": 4, "m.sc": 4,
        "bachelor": 3, "licence": 3, "licenciatura": 3, "bsc": 3, "b.sc": 3, "degree": 3,
        "associate": 2, "diploma": 2, "hnd": 2,
        "high school": 1, "secondary": 1, "ensino secundário": 1
    }

    EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_RE = re.compile(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}')
    EXP_RE   = re.compile(
        r'(\d+)\+?\s*(?:years?|anos?|yrs?)\s*(?:of\s+)?(?:experience|experiência|exp)',
        re.IGNORECASE
    )
    DATE_RANGE_RE = re.compile(
        r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec'
        r'|janeiro|fevereiro|março|abril|maio|junho|julho|agosto'
        r'|setembro|outubro|novembro|dezembro)[\w]*[\s,]*\d{4}|\d{4})'
        r'\s*[-–—]\s*'
        r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec'
        r'|janeiro|fevereiro|março|abril|maio|junho|julho|agosto'
        r'|setembro|outubro|novembro|dezembro)[\w]*[\s,]*\d{4}|\d{4}|present|atual|current)',
        re.IGNORECASE
    )

    def extract_info(self, text: str, filename: str = "") -> dict:
        tl = text.lower()
        lines = text.split('\n')
        cid = f"CV_{datetime.now().strftime('%Y%m%d%H%M%S')}_{abs(hash(text[:50])) % 10000}"

        return {
            "id": cid,
            "name": self._name(lines, filename),
            "email": self._email(text),
            "phone": self._phone(text),
            "location": self._location(tl),
            "summary": self._summary(text, lines),
            "skills": self._skills(tl),
            "experience": self._experience(text),
            "education": self._education(text),
            "languages": self._languages(tl),
            "certifications": self._certs(text),
            "total_experience_years": self._exp_years(text, tl),
            "raw_text": text[:500]
        }

    # ── extractors ────────────────────────────────────────────────

    def _name(self, lines, filename):
        for line in lines[:8]:
            line = line.strip()
            if 2 <= len(line.split()) <= 5 and not any(
                kw in line.lower() for kw in
                ['email','phone','tel','address','cv','resume','curriculum','vitae','@','http','www']
            ) and not re.search(r'\d{4}', line):
                words = line.split()
                if all(w[0].isupper() for w in words if w):
                    return line
        n = filename.replace('.txt','').replace('.pdf','').replace('_',' ').replace('-',' ')
        return n.title() if n else "Candidato Desconhecido"

    def _email(self, t):
        m = self.EMAIL_RE.search(t); return m.group(0) if m else ""

    def _phone(self, t):
        m = self.PHONE_RE.search(t); return m.group(0) if m else ""

    def _location(self, tl):
        cities = ["luanda","lobito","benguela","huambo","namibe","malanje","cabinda",
                  "lisbon","porto","london","paris","berlin","madrid","new york",
                  "são paulo","maputo","nairobi","johannesburg"]
        for c in cities:
            if c in tl: return c.title()
        return ""

    def _skills(self, tl):
        found = []
        for _, skills in self.TECH_SKILLS.items():
            for s in skills:
                escaped = re.escape(s)
                pattern = rf'(?<![a-z0-9]){escaped}(?![a-z0-9])'
                if re.search(pattern, tl):
                    found.append(s.upper() if len(s) <= 3 else s.title())
        return list(set(found))

    def _exp_years(self, text, tl):
        m = self.EXP_RE.search(text)
        if m: return float(m.group(1))
        ranges = self.DATE_RANGE_RE.findall(text)
        if ranges:
            total = 0
            for start, end in ranges:
                sy = self._year(start); ey = self._year(end)
                if sy and ey: total += (ey - sy) * 12
            if total > 0: return round(total / 12, 1)
        years = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
        if len(years) >= 2:
            ys = [int(y) for y in years]
            return float(min(max(ys) - min(ys), 30))
        return 0.0

    def _year(self, s):
        m = re.search(r'\b(20\d{2}|19\d{2})\b', s)
        if m: return int(m.group(1))
        if s.lower() in ('present','atual','current'): return datetime.now().year
        return None

    def _experience(self, text):
        entries = []
        pat = re.compile(
            r'([A-Z][^\n]{2,50})\n\s*([^\n]{2,60})\n\s*'
            r'((?:\d{4}|present).*?(?:\d{4}|present|current|atual))',
            re.IGNORECASE
        )
        for title, company, period in pat.findall(text[:3000])[:5]:
            entries.append({"title": title.strip(), "company": company.strip(),
                            "period": period.strip(), "description": ""})
        return entries

    def _education(self, text):
        entries = []
        pat = re.compile(
            r'(bachelor|master|phd|doctorate|mba|licenciatura|mestrado'
            r'|doutoramento|degree|diploma)[^\n]*\n[^\n]*', re.IGNORECASE
        )
        for m in pat.finditer(text):
            lines = m.group(0).split('\n')
            yr = re.search(r'\b(20\d{2}|19\d{2})\b', m.group(0))
            entries.append({
                "degree": lines[0].strip(),
                "institution": lines[1].strip() if len(lines) > 1 else "",
                "year": yr.group(0) if yr else ""
            })
        return entries[:3]

    def _languages(self, tl):
        langs = ["portuguese","english","french","spanish","german","italian","arabic",
                 "português","inglês","francês","espanhol","alemão"]
        return [l.title() for l in langs if l in tl]

    def _certs(self, text):
        pat = re.compile(
            r'\b(AWS|Azure|GCP|PMP|CISSP|CPA|CFA|Cisco|CCNA|CCNP|Google|Microsoft'
            r'|Salesforce|Oracle|CompTIA|Scrum|PMI|ISO|ITIL)[^\n]*', re.IGNORECASE
        )
        return list(set(m.group(0).strip()[:80] for m in pat.finditer(text)))[:5]

    def _summary(self, text, lines):
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in
                   ['summary','objective','profile','about','resumo','perfil','objetivo']):
                parts = [lines[j].strip()
                         for j in range(i+1, min(i+6, len(lines))) if lines[j].strip()]
                if parts: return ' '.join(parts)[:400]
        return ""


class MatchingEngine:
    WEIGHTS = {"skills": 0.45, "experience": 0.25, "education": 0.15,
               "location": 0.05, "language": 0.10}
    EDU = NLPEngine.EDUCATION_LEVELS

    def match(self, candidate: dict, job: dict) -> dict:
        skill_score, matched, missing = self._skills(candidate, job)
        exp   = self._experience(candidate, job)
        edu   = self._education(candidate, job)
        loc   = self._location(candidate, job)
        lang  = self._languages(candidate)

        overall = round(min(
            (skill_score * self.WEIGHTS["skills"] +
             exp   * self.WEIGHTS["experience"] +
             edu   * self.WEIGHTS["education"] +
             loc   * self.WEIGHTS["location"] +
             lang  * self.WEIGHTS["language"]) * 100, 100
        ), 1)

        return {
            "candidate": candidate,
            "overall_score": overall,
            "skill_score": round(skill_score * 100, 1),
            "experience_score": round(exp * 100, 1),
            "education_score": round(edu * 100, 1),
            "location_score": round(loc * 100, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "recommendation": self._recommend(overall),
            "highlights": self._highlights(candidate, matched, exp)
        }

    def _skill_match(self, skill: str, cset: set) -> bool:
        if skill in cset: return True
        for cs in cset:
            if len(skill) >= 4 and len(cs) >= 4:
                if skill in cs or cs in skill: return True
        aliases = {
            "machine learning": {"deep learning"},
            "javascript": {"node.js", "nodejs"},
            "react": {"reactjs", "react.js"},
        }
        return bool(aliases.get(skill, set()) & cset)

    def _skills(self, candidate, job):
        cs = {s.lower() for s in candidate.get("skills", [])}
        req  = [s.lower() for s in job.get("required_skills", [])]
        pref = [s.lower() for s in job.get("preferred_skills", [])]
        mr = [s for s in req  if self._skill_match(s, cs)]
        mp = [s for s in pref if self._skill_match(s, cs)]
        missing = [s for s in req if not self._skill_match(s, cs)]
        rs = len(mr) / max(len(req), 1)
        ps = len(mp) / max(len(pref), 1) if pref else 0.0
        score = 0.0 if (req and not mr) else (rs * 0.80 + ps * 0.20)
        return score, [s.title() for s in mr + mp], [s.title() for s in missing]

    def _experience(self, candidate, job):
        req    = job.get("min_experience_years", 0) or 0
        actual = candidate.get("total_experience_years", 0) or 0
        if req == 0: return 1.0
        return min(actual / req, 1.0)

    def _education(self, candidate, job):
        req_text = (job.get("education_level") or "").lower()
        if not req_text: return 1.0
        req_rank = max((v for k, v in self.EDU.items() if k in req_text), default=0)
        if req_rank == 0: return 1.0
        crank = 0
        for edu in candidate.get("education", []):
            d = edu.get("degree", "").lower()
            r = max((v for k, v in self.EDU.items() if k in d), default=0)
            crank = max(crank, r)
        return min(crank / req_rank, 1.0)

    def _location(self, candidate, job):
        jloc = job.get("location", "")
        cloc = candidate.get("location", "")
        if not jloc: return 1.0
        if not cloc: return 0.0
        return 1.0 if cloc.lower() == jloc.lower() else 0.2

    def _languages(self, candidate):
        langs = candidate.get("languages", [])
        if not langs: return 0.0
        return min(0.4 + (len(langs) - 1) * 0.30, 1.0)

    def _recommend(self, s):
        if s >= 85: return "✅ Fortemente Recomendado — Perfil excepcional para a vaga"
        if s >= 70: return "👍 Recomendado — Bom alinhamento com os requisitos"
        if s >= 55: return "🔄 Considerar — Potencial com gaps identificados"
        if s >= 40: return "⚠️ Revisão Necessária — Gaps significativos no perfil"
        return "❌ Não Adequado — Perfil não alinha com os requisitos"

    def _highlights(self, candidate, matched, exp_score):
        h = []
        if matched:
            h.append(f"✓ Domina {len(matched)} skill(s): {', '.join(matched[:3])}")
        exp = candidate.get("total_experience_years", 0)
        if exp_score >= 1.0 and exp:
            h.append(f"✓ {exp:.0f} anos de experiência")
        edu = candidate.get("education", [])
        if edu:
            h.append(f"✓ {edu[0].get('degree','')[:50]}")
        langs = candidate.get("languages", [])
        if len(langs) > 1:
            h.append(f"✓ Multilíngue: {', '.join(langs[:3])}")
        return h[:4]