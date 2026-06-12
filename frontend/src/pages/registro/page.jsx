export default function RegisterPage({ onSwitch }) {
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