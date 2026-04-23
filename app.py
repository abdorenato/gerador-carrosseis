"""Growth Studio — tela de entrada com iAbdo.

Tela inicial:
- Se não tem sessão ativa: mostra o iAbdo se apresentando + formulário de login
- Se tem sessão: mostra dashboard de progresso + atalhos pras etapas
"""

import streamlit as st

from db.database import init_db, get_connection
from db import repositories as repo
from services.sheets_service import register_lead, is_configured as sheets_configured

st.set_page_config(
    page_title="Growth Studio — iAbdo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
conn = get_connection()

# ═══════════════════════════════════════════════════════════════════════════
# TELA DE LOGIN (iAbdo)
# ═══════════════════════════════════════════════════════════════════════════

def _show_login():
    """Tela de entrada com iAbdo se apresentando."""
    st.sidebar.empty()  # limpa sidebar na tela de login

    col_left, col_main, col_right = st.columns([1, 3, 1])

    with col_main:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px 0 20px 0;">
                <div style="font-size: 80px;">🚀</div>
                <h1 style="margin: 0; font-size: 48px;">Growth Studio</h1>
                <p style="color: #888; font-size: 18px; margin-top: 8px;">
                    Comigo, você sai daqui com voz, posicionamento e ideias prontas.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.markdown(
            """
            ### 👋 Oi, eu sou o **iAbdo**.

            Sou o agente que vai te guiar em **6 passos** pra você sair daqui com:

            - 🎙️ Sua **voz autêntica** definida (arquétipo + mapa de voz)
            - 📍 Um **posicionamento** claro em 1 frase
            - 🗺️ Seu **território** de conteúdo principal
            - 📚 Suas **editorias** (macro-temas)
            - 💡 **Ideias** prontas pra postar
            - 🔄 **Conteúdos** gerados em múltiplos formatos (Reels, Carrossel, Post, Stories)

            Eu gero tudo com IA, mas você ajusta, regera, ou edita à vontade.

            **Topa? Me conta quem é você:**
            """
        )

        with st.form("login_form", clear_on_submit=False):
            name = st.text_input("Seu nome", placeholder="Ex: Renato Abdo")
            email = st.text_input("Seu email", placeholder="voce@email.com")
            instagram = st.text_input(
                "Seu @ do Instagram (opcional)", placeholder="@seuinsta"
            )

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn2:
                submit = st.form_submit_button(
                    "🚀 Começar minha jornada",
                    type="primary",
                    use_container_width=True,
                )

        if submit:
            if not name.strip() or not email.strip():
                st.error("Preciso do seu nome e email pra começar.")
                return

            if "@" not in email:
                st.error("Esse email não parece válido. Dá uma olhadinha.")
                return

            # Normalizar instagram
            ig = instagram.strip().lstrip("@") if instagram else ""

            # Salva na sessão
            st.session_state["user"] = {
                "name": name.strip(),
                "email": email.strip().lower(),
                "instagram": ig,
            }

            # Registra no Google Sheets
            if sheets_configured():
                try:
                    register_lead(name.strip(), email.strip().lower(), ig)
                except Exception:
                    pass  # não bloqueia o fluxo

            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD (logado)
# ═══════════════════════════════════════════════════════════════════════════

STEPS = [
    {"key": "voz", "icon": "🎙️", "title": "Voz da Marca", "page": "pages/10_🎙️_Voz_da_Marca.py"},
    {"key": "posicionamento", "icon": "📍", "title": "Posicionamento", "page": None},
    {"key": "territorio", "icon": "🗺️", "title": "Território", "page": None},
    {"key": "editorias", "icon": "📚", "title": "Editorias", "page": None},
    {"key": "icp", "icon": "🎯", "title": "ICP", "page": "pages/01_🎯_ICP.py"},
    {"key": "oferta", "icon": "💰", "title": "Oferta", "page": "pages/02_💰_Oferta.py"},
    {"key": "pitch", "icon": "🎤", "title": "Pitch", "page": "pages/03_🎤_Pitch.py"},
    {"key": "ideias", "icon": "💡", "title": "Ideias", "page": "pages/04_💡_Ideas.py"},
    {"key": "monoflow", "icon": "🔄", "title": "Monoflow", "page": "pages/05_🔄_Monoflow.py"},
]


def _show_sidebar(user: dict):
    """Sidebar com perfil + mapa de progresso."""
    st.sidebar.markdown(f"### 👤 {user['name']}")
    st.sidebar.caption(user["email"])
    if user.get("instagram"):
        st.sidebar.caption(f"@{user['instagram']}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Sua jornada")

    progress = st.session_state.get("progress", {})
    completed = sum(1 for s in STEPS if progress.get(s["key"]))
    pct = int((completed / len(STEPS)) * 100)

    st.sidebar.progress(pct / 100, text=f"{completed}/{len(STEPS)} etapas ({pct}%)")
    st.sidebar.markdown("")

    for step in STEPS:
        done = progress.get(step["key"], False)
        marker = "✅" if done else "⚪"
        st.sidebar.markdown(f"{marker} {step['icon']} {step['title']}")

    st.sidebar.markdown("---")

    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()


def _show_dashboard(user: dict):
    """Dashboard principal com saudação do iAbdo e atalhos."""
    st.markdown(
        f"""
        <div style="padding: 20px 0 10px 0;">
            <h1 style="margin: 0;">E aí, {user['name'].split()[0]}! 👋</h1>
            <p style="color: #888; font-size: 18px;">
                Sou o iAbdo. Vamos construir sua máquina de conteúdo?
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    progress = st.session_state.get("progress", {})
    first_undone = next((s for s in STEPS if not progress.get(s["key"])), None)

    if first_undone:
        st.markdown(f"### 🎯 Próximo passo: {first_undone['icon']} {first_undone['title']}")
        if first_undone["page"]:
            st.markdown(
                f"Comece por aqui para dar o próximo passo na sua jornada."
            )
            if st.button(f"Ir para {first_undone['title']} →", type="primary"):
                st.switch_page(first_undone["page"])
        else:
            st.info(f"Estamos trabalhando na etapa **{first_undone['title']}**. Em breve!")
    else:
        st.success("🎉 Você completou todas as etapas! Bora gerar conteúdo?")

    st.markdown("---")
    st.markdown("### 🧭 Todas as etapas")

    cols = st.columns(3)
    for i, step in enumerate(STEPS):
        with cols[i % 3]:
            done = progress.get(step["key"], False)
            marker = "✅" if done else "⚪"
            with st.container(border=True):
                st.markdown(f"#### {step['icon']} {step['title']} {marker}")
                if step["page"]:
                    if st.button(f"Abrir", key=f"open_{step['key']}", use_container_width=True):
                        st.switch_page(step["page"])
                else:
                    st.caption("Em breve")


# ═══════════════════════════════════════════════════════════════════════════
# ROTEAMENTO
# ═══════════════════════════════════════════════════════════════════════════

user = st.session_state.get("user")

if not user:
    _show_login()
else:
    _show_sidebar(user)
    _show_dashboard(user)
