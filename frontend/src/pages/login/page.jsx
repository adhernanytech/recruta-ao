import { useState, useEffect, useCallback, createContext, useContext } from "react";

export default function LoginPage({ onSwitch }) {
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
          <div style={{ marginTop: 20, padding: "12px", background: "#1e293b", borderRadius: 8, fontSize: 12, color: "#64748b", textAlign: "center" }}>
            Demo admin: <span style={{ color: "#94a3b8" }}>admin@recruitao.ao</span> / <span style={{ color: "#94a3b8" }}>Admin@123</span>
          </div>
        </div>
      </div>
    </div>
  );
}