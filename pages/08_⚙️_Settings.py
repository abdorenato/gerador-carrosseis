import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("Configurações")

ENV_PATH = Path(__file__).parent.parent / ".env"


def _load_env() -> dict[str, str]:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _save_env(env: dict[str, str]) -> None:
    lines = []
    for key, value in env.items():
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


env = _load_env()

# ── Claude API ───────────────────────────────────────────────────────────

st.subheader("Claude API (Anthropic)")
claude_key = st.text_input(
    "API Key",
    value=env.get("CLAUDE_API_KEY", ""),
    type="password",
    help="Chave da API Anthropic (sk-ant-...)",
)
claude_model = st.selectbox(
    "Modelo",
    options=["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
    index=0 if env.get("CLAUDE_MODEL", "") not in [
        "claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"
    ] else [
        "claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"
    ].index(env.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")),
)

st.markdown("---")

# ── Meta / Instagram ────────────────────────────────────────────────────

st.subheader("Instagram (Meta Graph API)")
meta_app_id = st.text_input("App ID", value=env.get("META_APP_ID", ""))
meta_app_secret = st.text_input(
    "App Secret", value=env.get("META_APP_SECRET", ""), type="password"
)
ig_account_id = st.text_input(
    "Instagram Account ID", value=env.get("INSTAGRAM_ACCOUNT_ID", "")
)
meta_token = st.text_input(
    "Access Token",
    value=env.get("META_ACCESS_TOKEN", ""),
    type="password",
    help="Token de longa duração (60 dias). Gere pelo Facebook Developer.",
)

if meta_token:
    st.success("Token configurado")
else:
    st.warning("Token não configurado — analytics e publicação não funcionarão.")

st.markdown("---")

# ── Canva ────────────────────────────────────────────────────────────────

st.subheader("Canva Connect API (opcional)")
st.caption("Requer conta Canva Enterprise para autofill de templates.")
canva_client_id = st.text_input("Client ID", value=env.get("CANVA_CLIENT_ID", ""))
canva_client_secret = st.text_input(
    "Client Secret", value=env.get("CANVA_CLIENT_SECRET", ""), type="password"
)

st.markdown("---")

# ── Salvar ───────────────────────────────────────────────────────────────

if st.button("Salvar Configurações", type="primary"):
    new_env = {
        "CLAUDE_API_KEY": claude_key,
        "CLAUDE_MODEL": claude_model,
        "META_APP_ID": meta_app_id,
        "META_APP_SECRET": meta_app_secret,
        "INSTAGRAM_ACCOUNT_ID": ig_account_id,
        "META_ACCESS_TOKEN": meta_token,
        "CANVA_CLIENT_ID": canva_client_id,
        "CANVA_CLIENT_SECRET": canva_client_secret,
    }
    _save_env(new_env)
    st.success("Configurações salvas com sucesso!")
    st.info("Reinicie o app para aplicar as novas configurações.")
