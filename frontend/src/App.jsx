import { useState, useEffect, useCallback, createContext, useContext } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Auth Context ─────────────────────────────────────────────────────────────
const AuthContext = createContext(null);

function useAuth() { return useContext(AuthContext); }

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));

  useEffect(() => {
    if (token) {
      fetch(`${API}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(u => u ? setUser(u) : logout())
        .catch(logout);
    }
  }, []);

  const login = (tkn, userData) => {
    localStorage.setItem("token", tkn);
    setToken(tkn);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const authFetch = useCallback(async (url, opts = {}) => {
    const res = await fetch(`${API}${url}`, {
      ...opts,
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json", ...(opts.headers || {}) }
    });
    if (res.status === 401 || res.status === 403) { logout(); return null; }
    return res;
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, authFetch, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Icons ────────────────────────────────────────────────────────────────────
const Icon = ({ d, size = 18, color = "currentColor" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);
const IC = {
  upload: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
  search: "M11 17.25a6.25 6.25 0 1 1 0-12.5 6.25 6.25 0 0 1 0 12.5M16 16l4.5 4.5",
  user: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8",
  briefcase: "M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16",
  chart: "M18 20V10M12 20V4M6 20v-6",
  logout: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9",
  lock: "M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2zM7 11V7a5 5 0 0 1 10 0v4",
  mail: "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6",
  eye: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6",
  eyeoff: "M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24M1 1l22 22",
  star: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
  trash: "M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2",
  lightning: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  users: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function ScoreRing({ score, size = 80 }) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  const color = score >= 85 ? "#22c55e" : score >= 70 ? "#3b82f6" : score >= 55 ? "#f59e0b" : score >= 40 ? "#ef4444" : "#6b7280";
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)", flexShrink: 0 }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="8"
        strokeDasharray={circ} strokeDashoffset={offset}
        style={{ transition: "stroke-dashoffset 1s ease", strokeLinecap: "round" }} />
      <text x={size / 2} y={size / 2 + 6} textAnchor="middle" fill={color}
        style={{ transform: `rotate(90deg) translate(0,-${size}px)`, fontSize: size * 0.22, fontWeight: 700, fontFamily: "inherit" }}>
        {score}%
      </text>
    </svg>
  );
}

function SkillTag({ skill, matched, missing }) {
  const bg = matched ? "#166534" : missing ? "#7f1d1d" : "#1e293b";
  const border = matched ? "#22c55e" : missing ? "#ef4444" : "#334155";
  const color = matched ? "#86efac" : missing ? "#fca5a5" : "#94a3b8";
  return (
    <span style={{ background: bg, border: `1px solid ${border}`, color, padding: "2px 10px", borderRadius: 20, fontSize: 12, fontWeight: 500 }}>
      {matched && "✓ "}{missing && "✗ "}{skill}
    </span>
  );
}

function Toast({ msg, type, onClose }) {
  if (!msg) return null;
  const bg = type === "error" ? "#7f1d1d" : type === "success" ? "#14532d" : "#1e3a5f";
  const border = type === "error" ? "#ef4444" : type === "success" ? "#22c55e" : "#3b82f6";
  return (
    <div style={{
      position: "fixed", bottom: 24, right: 24, zIndex: 1000, background: bg, border: `1px solid ${border}`,
      borderRadius: 12, padding: "14px 20px", color: "#f1f5f9", maxWidth: 340,
      display: "flex", alignItems: "center", gap: 12, fontSize: 14, animation: "slideIn 0.3s ease"
    }}>
      <span style={{ flex: 1 }}>{msg}</span>
      <button onClick={onClose} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: 18 }}>×</button>
    </div>
  );
}

function Input({ label, type = "text", value, onChange, placeholder, icon }) {
  const [show, setShow] = useState(false);
  const isPass = type === "password";
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: "block", fontSize: 11, color: "#94a3b8", marginBottom: 6, fontWeight: 600, letterSpacing: 0.5 }}>{label.toUpperCase()}</label>}
      <div style={{ position: "relative" }}>
        {icon && <div style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "#475569" }}>
          <Icon d={icon} size={16} /></div>}
        <input type={isPass && show ? "text" : type} value={value} onChange={onChange} placeholder={placeholder}
          style={{
            width: "100%", padding: `12px ${isPass ? "44px" : "16px"} 12px ${icon ? "44px" : "16px"}`,
            background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, fontSize: 14,
            outline: "none", fontFamily: "inherit", color: "#f1f5f9", transition: "border-color 0.2s", boxSizing: "border-box"
          }}
          onFocus={e => e.target.style.borderColor = "#3b82f6"}
          onBlur={e => e.target.style.borderColor = "#1e293b"} />
        {isPass && <button type="button" onClick={() => setShow(!show)}
          style={{
            position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
            background: "none", border: "none", color: "#475569", cursor: "pointer"
          }}>
          <Icon d={show ? IC.eyeoff : IC.eye} size={16} />
        </button>}
      </div>
    </div>
  );
}

// ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
function LoginPage({ onSwitch }) {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError(""); setLoading(true);
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });
      const data = await r.json();
      if (!r.ok) { setError(data.detail || "Erro no login"); return; }
      login(data.access_token, data.user);
    } catch { setError("Servidor indisponível"); }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#020617", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16, background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px"
          }}>
            <Icon d={IC.lightning} size={28} color="#fff" />
          </div>
          <div style={{ fontFamily: "'Syne',sans-serif", fontWeight: 800, fontSize: 28, color: "#f1f5f9" }}>RecrutaAO</div>
          <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>Plataforma de Recrutamento Inteligente</div>
        </div>

        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 20, padding: 32 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24, textAlign: "center" }}>Entrar na conta</h2>
          {error && <div style={{
            background: "#7f1d1d22", border: "1px solid #ef444466", borderRadius: 8,
            padding: "10px 14px", color: "#fca5a5", fontSize: 13, marginBottom: 16
          }}>{error}</div>}
          <Input label="Email" type="email" value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
            placeholder="nome@exemplo.ao" icon={IC.mail} />
          <Input label="Password" type="password" value={form.password}
            onChange={e => setForm({ ...form, password: e.target.value })}
            placeholder="••••••••" icon={IC.lock} />
          <button onClick={handleSubmit} disabled={loading}
            style={{
              width: "100%", padding: "13px", background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
              border: "none", borderRadius: 10, color: "#fff", fontSize: 15, fontWeight: 700,
              cursor: "pointer", fontFamily: "inherit", marginTop: 8, opacity: loading ? 0.6 : 1
            }}>
            {loading ? "A entrar..." : "Entrar"}
          </button>
          <p style={{ textAlign: "center", marginTop: 20, color: "#64748b", fontSize: 13 }}>
            Não tens conta?{" "}
            <button onClick={onSwitch} style={{ background: "none", border: "none", color: "#3b82f6", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600 }}>
              Criar conta
            </button>
          </p>

          {/* PARA APAGAR DEPOIS*/}
          <div style={{ marginTop: 20, padding: "12px", background: "#1e293b", borderRadius: 8, fontSize: 12, color: "#64748b", textAlign: "center" }}>
            Demo admin: <span style={{ color: "#94a3b8" }}>admin@recruitao.ao</span> / <span style={{ color: "#94a3b8" }}>Admin@123</span>
          </div>

        </div>
      </div>
    </div>
  );
}

// ─── REGISTER PAGE ────────────────────────────────────────────────────────────
function RegisterPage({ onSwitch }) {
  const { login } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "", role: "recruiter" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    if (form.password !== form.confirm) { setError("As passwords não coincidem"); return; }
    if (form.password.length < 6) { setError("Password deve ter pelo menos 6 caracteres"); return; }
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/auth/register`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.name, email: form.email, password: form.password, role: form.role })
      });
      const data = await r.json();
      if (!r.ok) { setError(data.detail || "Erro no registo"); return; }
      login(data.access_token, data.user);
    } catch { setError("Servidor indisponível"); }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#020617", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ width: "100%", maxWidth: 460 }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16, background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px"
          }}>
            <Icon d={IC.lightning} size={28} color="#fff" />
          </div>
          <div style={{ fontFamily: "'Syne',sans-serif", fontWeight: 800, fontSize: 28, color: "#f1f5f9" }}>RecrutaAO</div>
          <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>Criar nova conta</div>
        </div>

        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 20, padding: 32 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24, textAlign: "center" }}>Criar Conta</h2>
          {error && <div style={{
            background: "#7f1d1d22", border: "1px solid #ef444466", borderRadius: 8,
            padding: "10px 14px", color: "#fca5a5", fontSize: 13, marginBottom: 16
          }}>{error}</div>}
          <Input label="Nome completo" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Ex: João Silva" icon={IC.user} />
          <Input label="Email" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="nome@empresa.ao" icon={IC.mail} />
          <Input label="Password" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="Mínimo 6 caracteres" icon={IC.lock} />
          <Input label="Confirmar Password" type="password" value={form.confirm} onChange={e => setForm({ ...form, confirm: e.target.value })} placeholder="Repete a password" icon={IC.lock} />

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 11, color: "#94a3b8", marginBottom: 6, fontWeight: 600, letterSpacing: 0.5 }}>PERFIL</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {["recruiter", "admin"].map(role => (
                <button key={role} type="button" onClick={() => setForm({ ...form, role })}
                  style={{
                    padding: "10px", borderRadius: 8, border: `1px solid ${form.role === role ? "#3b82f6" : "#1e293b"}`,
                    background: form.role === role ? "#1e3a5f" : "#1e293b", color: form.role === role ? "#93c5fd" : "#64748b",
                    cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: form.role === role ? 600 : 400
                  }}>
                  {role === "recruiter" ? "👤 Recruiter" : "🔧 Admin"}
                </button>
              ))}
            </div>
          </div>

          <button onClick={handleSubmit} disabled={loading}
            style={{
              width: "100%", padding: "13px", background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
              border: "none", borderRadius: 10, color: "#fff", fontSize: 15, fontWeight: 700,
              cursor: "pointer", fontFamily: "inherit", marginTop: 8, opacity: loading ? 0.6 : 1
            }}>
            {loading ? "A criar conta..." : "Criar Conta"}
          </button>
          <p style={{ textAlign: "center", marginTop: 20, color: "#64748b", fontSize: 13 }}>
            Já tens conta?{" "}
            <button onClick={onSwitch} style={{ background: "none", border: "none", color: "#3b82f6", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600 }}>
              Entrar
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── MAIN APP (autenticado) ───────────────────────────────────────────────────
function MainApp() {
  const { user, logout, authFetch, isAdmin } = useAuth();
  const [tab, setTab] = useState("upload");
  const [candidates, setCandidates] = useState([]);
  const [matches, setMatches] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState({ msg: "", type: "info" });
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [cvText, setCvText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [users, setUsers] = useState([]);
  const [jobForm, setJobForm] = useState({
    title: "Senior Python Developer",
    description: "Backend developer com experiência em APIs e cloud.",
    required_skills: "Python, FastAPI, PostgreSQL",
    preferred_skills: "Docker, AWS, React",
    min_experience_years: 3, education_level: "bachelor", location: "Luanda"
  });

  const notify = (msg, type = "info") => {
    setToast({ msg, type });
    setTimeout(() => setToast({ msg: "" }), 4000);
  };

  const load = useCallback(async () => {
    const r = await authFetch("/api/candidates");
    if (r) setCandidates(await r.json());
    const s = await authFetch("/api/stats");
    if (s) setStats(await s.json());
    if (isAdmin) {
      const u = await authFetch("/api/users");
      if (u) setUsers(await u.json());
    }
  }, [authFetch, isAdmin]);

  useEffect(() => { load(); }, [load]);

  const handleFileUpload = async (file) => {
    setLoading(true);
    const form = new FormData(); form.append("file", file);
    const r = await fetch(`${API}/api/cv/upload`, {
      method: "POST", body: form, headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    if (r.ok) {
      const p = await r.json();
      notify(`✅ CV de ${p.name} carregado!`, "success");
      load();
    } else {
      const e = await r.json();
      notify(`Erro: ${e.detail}`, "error");
    }
    setLoading(false);
  };

  /*
  const handleTextParse = async () => {
    if (cvText.trim().length < 50) { notify("Texto muito curto", "error"); return; }
    setLoading(true);
    const r = await authFetch("/api/cv/text", { method:"POST", body: JSON.stringify({ text:cvText }) });
    if (r?.ok) {
      const p = await r.json();
      notify(`✅ CV de ${p.name} processado!`, "success");
      setCvText(""); load();
    } else {
      const e = await r?.json();
      notify(`Erro: ${e?.detail}`, "error");
    }
    setLoading(false);
  };
*/
  const handleMatch = async () => {
    if (!candidates.length) { notify("Carregue CVs primeiro", "error"); return; }
    setLoading(true);
    const payload = {
      ...jobForm,
      required_skills: jobForm.required_skills.split(",").map(s => s.trim()).filter(Boolean),
      preferred_skills: jobForm.preferred_skills.split(",").map(s => s.trim()).filter(Boolean),
      min_experience_years: parseInt(jobForm.min_experience_years) || 0,
    };
    const r = await authFetch("/api/match", { method: "POST", body: JSON.stringify(payload) });
    if (r?.ok) {
      const data = await r.json();
      setMatches(data.results);
      setTab("results");
      notify(`🎯 ${data.results.length} candidato(s) analisado(s)`, "success");
    }
    setLoading(false);
  };

  const deleteCandidate = async (id) => {
    await authFetch(`/api/candidates/${id}`, { method: "DELETE" });
    load(); notify("Candidato removido", "info");
  };

  const deleteAllCandidates = async () => {
    if (!isAdmin) { notify("Apenas admins podem apagar todos os candidatos", "error"); return; }
    if (!candidates.length) { notify("Nenhum candidato para apagar", "error"); return; }
    if (!confirm("Tem certeza que deseja apagar todos os candidatos? Esta ação é irreversível.")) return;
    const r = await authFetch(`/api/candidates`, { method: "DELETE" });
    if (r?.ok) { load(); notify("Todos os candidatos removidos", "success"); }
    else { notify("Erro ao apagar candidatos", "error"); }
  };

  const toggleUser = async (uid) => {
    await authFetch(`/api/users/${uid}/toggle`, { method: "PATCH" });
    load(); notify("Estado actualizado", "success");
  };

  const tabs = [
    { id: "upload", label: "Upload CVs", icon: IC.upload },
    { id: "match", label: "Matching", icon: IC.search },
    { id: "candidates", label: "Candidatos", icon: IC.user, badge: candidates.length },
    { id: "results", label: "Resultados", icon: IC.star, badge: matches.length },
    { id: "analytics", label: "Análises", icon: IC.chart },
    ...(isAdmin ? [{ id: "users", label: "Utilizadores", icon: IC.users, badge: users.length }] : [])
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#020617", color: "#f1f5f9", fontFamily: "'Inter',sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        ::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:#0f172a}::-webkit-scrollbar-thumb{background:#334155;border-radius:3px}
        @keyframes slideIn{from{transform:translateX(100px);opacity:0}to{transform:translateX(0);opacity:1}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
        .hover-card{transition:all .2s}.hover-card:hover{transform:translateY(-2px);border-color:#334155!important}
        input,textarea,select{color:#f1f5f9!important;background:#0f172a!important}
      `}</style>

      {/* Header */}
      <header style={{ borderBottom: "1px solid #1e293b", padding: "0 32px", background: "#020617", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", height: 64 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon d={IC.lightning} size={20} color="#fff" />
            </div>
            <div>
              <div style={{ fontFamily: "'Syne',sans-serif", fontWeight: 800, fontSize: 17 }}>RecrutaAO</div>
              <div style={{ fontSize: 10, color: "#64748b", letterSpacing: 1.5, textTransform: "uppercase" }}>CV Intelligence</div>
            </div>
          </div>

          <nav style={{ display: "flex", gap: 2 }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                style={{
                  padding: "8px 14px", borderRadius: 8, border: "none", cursor: "pointer",
                  background: tab === t.id ? "#1e293b" : "transparent", color: tab === t.id ? "#f1f5f9" : "#64748b",
                  fontSize: 13, fontWeight: tab === t.id ? 600 : 400, fontFamily: "inherit",
                  display: "flex", alignItems: "center", gap: 6,
                  borderBottom: tab === t.id ? "2px solid #3b82f6" : "2px solid transparent"
                }}>
                <Icon d={t.icon} size={14} /> {t.label}
                {t.badge > 0 && <span style={{ background: "#3b82f6", color: "#fff", borderRadius: 10, padding: "1px 7px", fontSize: 11 }}>{t.badge}</span>}
              </button>
            ))}
          </nav>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{user?.name}</div>
              <div style={{ fontSize: 11, color: user?.role === "admin" ? "#f59e0b" : "#64748b", textTransform: "uppercase", letterSpacing: 0.5 }}>
                {user?.role === "admin" ? "⚙️ Admin" : "👤 Recruiter"}
              </div>
            </div>
            <button onClick={logout}
              style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, padding: "8px 12px", color: "#94a3b8", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontFamily: "inherit" }}>
              <Icon d={IC.logout} size={15} /> Sair
            </button>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1280, margin: "0 auto", padding: 32 }}>

        {/* ── UPLOAD ── */}
        {tab === "upload" && (
          <div style={{ animation: "fadeIn .5s ease" }}>
            <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 30, fontWeight: 800, marginBottom: 8 }}>Upload de CVs</h1>
            <p style={{ color: "#64748b", marginBottom: 32 }}>Arraste ficheiros ou cole o texto do CV para extracção automática com NLP.</p>
            <div style={{}}>
              <div>
                <h3 style={{ fontSize: 12, color: "#94a3b8", marginBottom: 12, fontWeight: 600, letterSpacing: 0.5 }}>FICHEIRO .TXT</h3>
                <div onDragOver={e => { e.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)}
                  onDrop={e => { e.preventDefault(); setDragOver(false); handleFileUpload(e.dataTransfer.files[0]) }}
                  onClick={() => document.getElementById("fi").click()}
                  style={{
                    border: `2px dashed ${dragOver ? "#3b82f6" : "#1e293b"}`, borderRadius: 16, padding: "48px 24px",
                    textAlign: "center", cursor: "pointer", background: dragOver ? "#1e3a5f22" : "#0f172a",
                    minHeight: 220, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", transition: "all .2s"
                  }}>
                  <div style={{ width: 60, height: 60, borderRadius: 14, background: dragOver ? "#1e3a5f" : "#1e293b", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
                    <Icon d={IC.upload} size={26} color={dragOver ? "#3b82f6" : "#64748b"} /></div>
                  <p style={{ color: dragOver ? "#93c5fd" : "#94a3b8", fontSize: 14, marginBottom: 4 }}>
                    {loading ? "A processar..." : "Arraste o CV aqui"}</p>
                  <p style={{ color: "#475569", fontSize: 12 }}>ou clique para seleccionar .txt</p>
                </div>
                <input id="fi" type="file" accept=".txt" style={{ display: "none" }} onChange={e => handleFileUpload(e.target.files[0])} />
              </div>

              {
              /*
                <div>
                <h3 style={{ fontSize: 12, color: "#94a3b8", marginBottom: 12, fontWeight: 600, letterSpacing: 0.5 }}>COLAR TEXTO</h3>
                <textarea value={cvText} onChange={e => setCvText(e.target.value)}
                  placeholder="Cole aqui o conteúdo do CV..." rows={8}
                  style={{ width: "100%", padding: 16, border: "1px solid #1e293b", borderRadius: 12, fontSize: 13, fontFamily: "monospace", lineHeight: 1.6, outline: "none", resize: "vertical" }}
                  onFocus={e => e.target.style.borderColor = "#3b82f6"} onBlur={e => e.target.style.borderColor = "#1e293b"} />
                <button onClick={handleTextParse} disabled={loading}
                  style={{
                    marginTop: 12, width: "100%", padding: "12px", background: "linear-gradient(135deg,#3b82f6,#8b5cf6)",
                    border: "none", borderRadius: 10, color: "#fff", fontSize: 14, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", opacity: loading ? .6 : 1
                  }}>
                  {loading ? "A processar..." : "Extrair Informação do CV"}
                </button>
              </div>
              */}
            </div>
          </div>
        )}

        {/* ── MATCH ── */}
        {tab === "match" && (
          <div style={{ animation: "fadeIn .4s ease" }}>
            <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 30, fontWeight: 800, marginBottom: 8 }}>Definir Vaga</h1>
            <p style={{ color: "#64748b", marginBottom: 32 }}>Configure os requisitos. O motor NLP calcula o score de matching para cada candidato.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[{ l: "Título da Vaga", k: "title" }, { l: "Nível Educação", k: "education_level" }, { l: "Localização", k: "location" }].map(f => (
                  <div key={f.k}>
                    <label style={{ display: "block", fontSize: 11, color: "#94a3b8", marginBottom: 6, fontWeight: 600, letterSpacing: .5 }}>{f.l.toUpperCase()}</label>
                    <input value={jobForm[f.k]} onChange={e => setJobForm({ ...jobForm, [f.k]: e.target.value })}
                      style={{ width: "100%", padding: "12px 16px", border: "1px solid #1e293b", borderRadius: 10, fontSize: 14, outline: "none", fontFamily: "inherit" }}
                      onFocus={e => e.target.style.borderColor = "#3b82f6"} onBlur={e => e.target.style.borderColor = "#1e293b"} />
                  </div>
                ))}
                <div>
                  <label style={{ display: "block", fontSize: 11, color: "#94a3b8", marginBottom: 6, fontWeight: 600, letterSpacing: .5 }}>ANOS EXPERIÊNCIA MÍNIMOS</label>
                  <input type="number" min={0} value={jobForm.min_experience_years}
                    onChange={e => setJobForm({ ...jobForm, min_experience_years: e.target.value })}
                    style={{ width: "100%", padding: "12px 16px", border: "1px solid #1e293b", borderRadius: 10, fontSize: 14, outline: "none", fontFamily: "inherit" }} />
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[{ l: "Skills Obrigatórias (vírgula)", k: "required_skills" }, { l: "Skills Preferenciais (vírgula)", k: "preferred_skills" }, { l: "Descrição da Vaga", k: "description" }].map(f => (
                  <div key={f.k}>
                    <label style={{ display: "block", fontSize: 11, color: "#94a3b8", marginBottom: 6, fontWeight: 600, letterSpacing: .5 }}>{f.l.toUpperCase()}</label>
                    <textarea value={jobForm[f.k]} onChange={e => setJobForm({ ...jobForm, [f.k]: e.target.value })} rows={3}
                      style={{ width: "100%", padding: "12px 16px", border: "1px solid #1e293b", borderRadius: 10, fontSize: 14, outline: "none", fontFamily: "inherit", resize: "vertical" }}
                      onFocus={e => e.target.style.borderColor = "#3b82f6"} onBlur={e => e.target.style.borderColor = "#1e293b"} />
                  </div>
                ))}
              </div>
            </div>
            <button onClick={handleMatch} disabled={loading || !candidates.length}
              style={{
                marginTop: 28, padding: "15px 40px",
                background: !candidates.length ? "#1e293b" : "linear-gradient(135deg,#3b82f6,#8b5cf6)",
                border: "none", borderRadius: 12, color: !candidates.length ? "#64748b" : "#fff",
                fontSize: 16, fontWeight: 700, cursor: !candidates.length ? "not-allowed" : "pointer",
                fontFamily: "inherit", display: "flex", alignItems: "center", gap: 10
              }}>
              <Icon d={IC.lightning} size={20} />
              {loading ? "A calcular..." : `Executar Matching (${candidates.length} candidatos)`}
            </button>
          </div>
        )}

        {/* ── CANDIDATES ── */}
        {tab === "candidates" && (
          <div style={{ animation: "fadeIn .4s ease" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 30, fontWeight: 800, marginBottom: 8 }}>Candidatos</h1>
                <p style={{ color: "#64748b", marginBottom: 32 }}>{candidates.length} CV(s) carregado(s) e analisados</p>
              </div>
              {isAdmin && (
                <button onClick={deleteAllCandidates}
                  style={{ padding: "10px 14px", background: "#7f1d1d", border: "1px solid #4c1010", borderRadius: 10, color: "#fff", cursor: "pointer", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                  <Icon d={IC.trash} size={16} /> Apagar Todos
                </button>
              )}
            </div>
            {!candidates.length
              ? <div style={{ textAlign: "center", padding: "80px 20px", color: "#475569" }}>
                <Icon d={IC.user} size={48} color="#334155" /><p style={{ marginTop: 16 }}>Nenhum candidato ainda</p></div>
              : <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: 20 }}>
                {candidates.map(c => (
                  <div key={c.id} className="hover-card" style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 22 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ width: 42, height: 42, borderRadius: 10, background: "linear-gradient(135deg,#3b82f6,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 16 }}>
                          {c.name.charAt(0)}</div>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 14 }}>{c.name}</div>
                          <div style={{ color: "#64748b", fontSize: 11 }}>{c.email}</div>
                        </div>
                      </div>
                      <button onClick={() => deleteCandidate(c.id)} style={{ background: "none", border: "none", color: "#475569", cursor: "pointer" }}>
                        <Icon d={IC.trash} size={15} /></button>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 12 }}>
                      {c.skills.slice(0, 5).map(s => <SkillTag key={s} skill={s} />)}
                      {c.skills.length > 5 && <span style={{ color: "#64748b", fontSize: 12 }}>+{c.skills.length - 5}</span>}
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 12 }}>
                      <div style={{ background: "#1e293b", borderRadius: 8, padding: "8px 10px" }}>
                        <div style={{ color: "#64748b", marginBottom: 2 }}>Experiência</div>
                        <div>{c.total_experience_years || 0} anos</div>
                      </div>
                      <div style={{ background: "#1e293b", borderRadius: 8, padding: "8px 10px" }}>
                        <div style={{ color: "#64748b", marginBottom: 2 }}>Localização</div>
                        <div>{c.location || "N/A"}</div>
                      </div>
                    </div>
                    <button onClick={() => setSelectedCandidate(c)}
                      style={{
                        marginTop: 12, width: "100%", padding: "9px", background: "#1e293b", border: "1px solid #334155",
                        borderRadius: 8, color: "#94a3b8", cursor: "pointer", fontSize: 12, fontFamily: "inherit"
                      }}>
                      Ver Perfil Completo
                    </button>
                  </div>
                ))}
              </div>}
          </div>
        )}

        {/* ── RESULTS ── */}
        {tab === "results" && (
          <div style={{ animation: "fadeIn .4s ease" }}>
            <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 30, fontWeight: 800, marginBottom: 8 }}>Resultados</h1>
            <p style={{ color: "#64748b", marginBottom: 32 }}>Ranking por score de compatibilidade</p>
            {!matches.length
              ? <div style={{ textAlign: "center", padding: "80px 20px", color: "#475569" }}>
                <Icon d={IC.search} size={48} color="#334155" /><p style={{ marginTop: 16 }}>Execute o matching primeiro</p></div>
              : <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                {matches.map((m, i) => (
                  <div key={m.candidate.id} className="hover-card"
                    style={{
                      background: "#0f172a", border: "1px solid #1e293b", borderRadius: 20, padding: 26,
                      borderLeft: `4px solid ${m.overall_score >= 85 ? "#22c55e" : m.overall_score >= 70 ? "#3b82f6" : m.overall_score >= 55 ? "#f59e0b" : "#ef4444"}`
                    }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                      <div style={{ fontSize: 26, fontWeight: 900, color: i === 0 ? "#fbbf24" : i === 1 ? "#94a3b8" : i === 2 ? "#cd7c2e" : "#334155", minWidth: 30 }}>#{i + 1}</div>
                      <ScoreRing score={m.overall_score} size={86} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 4 }}>{m.candidate.name}</div>
                        <div style={{ color: "#94a3b8", fontSize: 13, marginBottom: 12 }}>{m.recommendation}</div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
                          {[{ l: "Skills", v: m.skill_score, c: "#3b82f6" }, { l: "Experiência", v: m.experience_score, c: "#8b5cf6" },
                          { l: "Educação", v: m.education_score, c: "#06b6d4" }, { l: "Localização", v: m.location_score, c: "#f59e0b" }
                          ].map(bar => (
                            <div key={bar.l}>
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#64748b", marginBottom: 3 }}>
                                <span>{bar.l}</span><span style={{ color: bar.c }}>{bar.v}%</span></div>
                              <div style={{ height: 4, background: "#1e293b", borderRadius: 2 }}>
                                <div style={{ height: "100%", width: `${bar.v}%`, background: bar.c, borderRadius: 2, transition: "width 1s ease" }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div style={{ minWidth: 200 }}>
                        <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6, fontWeight: 600 }}>SKILLS</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                          {m.matched_skills.map(s => <SkillTag key={s} skill={s} matched />)}
                          {m.missing_skills.slice(0, 3).map(s => <SkillTag key={s} skill={s} missing />)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>}
          </div>
        )}

        {/* ── ANALYTICS ── */}
        {tab === "analytics" && (
          <div style={{ animation: "fadeIn .4s ease" }}>
            <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 30, fontWeight: 800, marginBottom: 8 }}>Análises</h1>
            <p style={{ color: "#64748b", marginBottom: 32 }}>Visão geral do pool de candidatos</p>
            {!stats?.total_candidates
              ? <div style={{ textAlign: "center", padding: "80px 20px", color: "#475569" }}>
                <Icon d={IC.chart} size={48} color="#334155" /><p style={{ marginTop: 16 }}>Carregue CVs para ver estatísticas</p></div>
              : <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 28 }}>
                  {[
                    { label: "Candidatos", value: stats.total_candidates, color: "#3b82f6", icon: IC.user },
                    { label: "Exp. Média", value: `${stats.avg_experience_years} anos`, color: "#8b5cf6", icon: IC.briefcase },
                    { label: "Top Skills", value: stats.top_skills?.length || 0, color: "#f59e0b", icon: IC.star },
                  ].map(s => (
                    <div key={s.label} style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: "20px 24px", display: "flex", alignItems: "center", gap: 16 }}>
                      <div style={{ width: 46, height: 46, borderRadius: 12, background: `${s.color}22`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <Icon d={s.icon} size={22} color={s.color} /></div>
                      <div>
                        <div style={{ color: "#64748b", fontSize: 12, marginBottom: 2 }}>{s.label}</div>
                        <div style={{ fontSize: 22, fontWeight: 700 }}>{s.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 20, padding: 28 }}>
                  <h3 style={{ marginBottom: 20, fontSize: 15, fontWeight: 700 }}>Top Skills no Pool</h3>
                  {(stats.top_skills || []).map((sk, i) => (
                    <div key={sk.skill} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
                      <span style={{ width: 110, fontSize: 13, color: "#94a3b8" }}>{sk.skill}</span>
                      <div style={{ flex: 1, height: 8, background: "#1e293b", borderRadius: 4, overflow: "hidden" }}>
                        <div style={{
                          height: "100%", width: `${(sk.count / stats.total_candidates) * 100}%`,
                          background: `hsl(${210 + i * 20},75%,55%)`, borderRadius: 4, transition: "width 1s ease"
                        }} /></div>
                      <span style={{ width: 20, fontSize: 12, color: "#64748b", textAlign: "right" }}>{sk.count}</span>
                    </div>
                  ))}
                </div>
              </>}
          </div>
        )}

        {/* ── USERS (admin) ── */}
        {tab === "users" && isAdmin && (
          <div style={{ animation: "fadeIn .4s ease" }}>
            <h1 style={{ fontFamily: "'Syne',sans-serif", fontSize: 30, fontWeight: 800, marginBottom: 8 }}>Gestão de Utilizadores</h1>
            <p style={{ color: "#64748b", marginBottom: 32 }}>Activar / desactivar contas de acesso ao sistema</p>
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 20, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #1e293b" }}>
                    {["Nome", "Email", "Perfil", "Estado", "Criado em", "Acção"].map(h => (
                      <th key={h} style={{ padding: "14px 20px", textAlign: "left", fontSize: 11, color: "#64748b", fontWeight: 600, letterSpacing: .5 }}>{h.toUpperCase()}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} style={{ borderBottom: "1px solid #1e293b22" }}>
                      <td style={{ padding: "14px 20px", fontWeight: 600 }}>{u.name}</td>
                      <td style={{ padding: "14px 20px", color: "#64748b", fontSize: 13 }}>{u.email}</td>
                      <td style={{ padding: "14px 20px" }}>
                        <span style={{
                          background: u.role === "admin" ? "#78350f22" : "#1e3a5f",
                          border: `1px solid ${u.role === "admin" ? "#f59e0b66" : "#3b82f666"}`,
                          color: u.role === "admin" ? "#fbbf24" : "#93c5fd", padding: "2px 10px", borderRadius: 20, fontSize: 12
                        }}>
                          {u.role}</span></td>
                      <td style={{ padding: "14px 20px" }}>
                        <span style={{
                          background: u.active ? "#14532d" : "#450a0a",
                          border: `1px solid ${u.active ? "#22c55e66" : "#ef444466"}`,
                          color: u.active ? "#86efac" : "#fca5a5", padding: "2px 10px", borderRadius: 20, fontSize: 12
                        }}>
                          {u.active ? "Activo" : "Inactivo"}</span></td>
                      <td style={{ padding: "14px 20px", color: "#64748b", fontSize: 12 }}>{u.created_at?.slice(0, 10)}</td>
                      <td style={{ padding: "14px 20px" }}>
                        <button onClick={() => toggleUser(u.id)}
                          style={{
                            padding: "6px 14px", background: "#1e293b", border: "1px solid #334155",
                            borderRadius: 7, color: "#94a3b8", cursor: "pointer", fontSize: 12, fontFamily: "inherit"
                          }}>
                          {u.active ? "Desactivar" : "Activar"}</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Candidate Modal */}
      {selectedCandidate && (
        <div onClick={() => setSelectedCandidate(null)}
          style={{ position: "fixed", inset: 0, background: "#00000088", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 24, maxWidth: 600, width: "100%", maxHeight: "80vh", overflow: "auto", padding: 32 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 22 }}>
              <div>
                <h2 style={{ fontFamily: "'Syne',sans-serif", fontSize: 22, fontWeight: 800 }}>{selectedCandidate.name}</h2>
                <p style={{ color: "#64748b", fontSize: 13 }}>{selectedCandidate.email}{selectedCandidate.phone && ` · ${selectedCandidate.phone}`}</p>
              </div>
              <button onClick={() => setSelectedCandidate(null)}
                style={{ background: "#1e293b", border: "none", borderRadius: 8, width: 34, height: 34, cursor: "pointer", color: "#94a3b8", fontSize: 18 }}>×</button>
            </div>
            {selectedCandidate.summary && <p style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6, marginBottom: 18 }}>{selectedCandidate.summary}</p>}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 18 }}>
              {selectedCandidate.skills.map(s => <SkillTag key={s} skill={s} />)}
            </div>
            {selectedCandidate.education.map((e, i) => (
              <div key={i} style={{ background: "#1e293b", borderRadius: 10, padding: "12px 14px", marginBottom: 8 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{e.degree}</div>
                <div style={{ color: "#64748b", fontSize: 12 }}>{e.institution}{e.year && ` · ${e.year}`}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <Toast msg={toast.msg} type={toast.type} onClose={() => setToast({ msg: "" })} />
    </div>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function App_v2() {
  const [page, setPage] = useState("login");
  return (
    <AuthProvider>
      <AppRouter page={page} setPage={setPage} />
    </AuthProvider>
  );
}

function AppRouter({ page, setPage }) {
  const { user } = useAuth();
  if (user) return <MainApp />;
  if (page === "login") return <LoginPage onSwitch={() => setPage("register")} />;
  if (page === "register") return <RegisterPage onSwitch={() => setPage("login")} />;
}