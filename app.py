"""Growth Studio — tela de entrada com iAbdo.

Usa st.navigation para controlar o menu lateral em wizard progressivo:
- Antes do login: só a tela de entrada
- Após login: grupos (Conteúdo → Produto → Sistema)
- Cada próxima página só libera após a anterior ser completada
"""

import streamlit as st

from db.database import init_db, get_connection
from services.supabase_service import (
    register_lead,
    is_configured as supabase_configured,
    get_full_progress,
)

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

def render_login():
    """Tela de entrada com iAbdo se apresentando."""
    # Esconde sidebar na tela de login
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col_main, _ = st.columns([1, 3, 1])

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

            Vou te guiar pra você sair daqui com:

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

            _, col_btn = st.columns([1, 1])
            with col_btn:
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

            ig = instagram.strip().lstrip("@") if instagram else ""

            user_record = None
            if supabase_configured():
                try:
                    user_record = register_lead(name.strip(), email.strip().lower(), ig)
                except Exception as e:
                    st.warning(f"Não consegui salvar no banco: {e}. Seguindo em modo local.")

            st.session_state["user"] = {
                "id": user_record.get("id") if user_record else None,
                "name": name.strip(),
                "email": email.strip().lower(),
                "instagram": ig,
            }

            if user_record:
                try:
                    st.session_state["progress"] = get_full_progress(user_record["id"])
                except Exception:
                    pass

            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD (Home após login)
# ═══════════════════════════════════════════════════════════════════════════

def render_dashboard():
    """Dashboard principal com saudação do iAbdo e próximos passos."""
    user = st.session_state["user"]
    progress = st.session_state.get("progress", {})

    # Sidebar: perfil + logout
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.caption(user["email"])
        if user.get("instagram"):
            st.caption(f"@{user['instagram']}")
        st.markdown("---")
        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Header
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

    # Próximo passo sugerido
    if not progress.get("voz"):
        next_step = ("🎙️", "Voz da Marca", "Tudo começa descobrindo como você soa de verdade.")
    elif not progress.get("posicionamento"):
        next_step = ("📍", "Posicionamento", "Em breve — vou te ajudar a cravar sua frase de posicionamento.")
    elif not progress.get("territorio"):
        next_step = ("🗺️", "Território", "Em breve — definir o território principal de conteúdo.")
    elif not progress.get("editorias"):
        next_step = ("📚", "Editorias", "Em breve — macro-temas do seu território.")
    elif not progress.get("ideias"):
        next_step = ("💡", "Ideias", "Bora gerar ideias a partir das suas editorias.")
    else:
        next_step = ("🔄", "Monoflow", "Transformar ideias em conteúdos pra todas as plataformas.")

    st.markdown(f"### 🎯 Próximo passo: {next_step[0]} {next_step[1]}")
    st.markdown(next_step[2])
    st.markdown("")

    # Progresso geral
    total_steps = 6  # voz, posicionamento, territorio, editorias, ideias, monoflow
    completed = sum(1 for k in ["voz", "posicionamento", "territorio", "editorias", "ideias", "conteudos"] if progress.get(k))
    pct = int((completed / total_steps) * 100)
    st.progress(pct / 100, text=f"Progresso: {completed}/{total_steps} etapas ({pct}%)")

    st.markdown("---")
    st.markdown(
        """
        ### 🧭 Como navegar

        No menu lateral você vê os 3 grupos:

        - **✨ Conteúdo** — sua voz, editorias, ideias e geração de conteúdo
        - **📦 Produto** — ICP, Oferta e Pitch (para quando for oferecer algo)
        - **⚙️ Sistema** — configurações

        Eu vou **liberar as etapas à medida que você for completando**. Bora pelo primeiro passo?
        """
    )


# ═══════════════════════════════════════════════════════════════════════════
# ROTEAMENTO COM ST.NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════

user = st.session_state.get("user")

if not user:
    # Antes do login: só a tela de entrada
    pg = st.navigation([st.Page(render_login, title="Entrada", default=True, icon="🚀")])
else:
    progress = st.session_state.get("progress", {})

    # ── Início (sempre disponível) ──
    home_pages = [st.Page(render_dashboard, title="Início", default=True, icon="🏠")]

    # ── ✨ Conteúdo (wizard progressivo) ──
    content_pages = []
    # 1. Voz da Marca — sempre disponível (primeiro passo)
    content_pages.append(
        st.Page("pages/10_🎙️_Voz_da_Marca.py", title="Voz da Marca", icon="🎙️")
    )
    # 2. Posicionamento, Território, Editorias — em breve (ainda não implementados)
    # 3. Ideias — libera após Voz
    if progress.get("voz"):
        content_pages.append(
            st.Page("pages/04_💡_Ideas.py", title="Ideias", icon="💡")
        )
    # 4. Monoflow — libera após Voz também (pra dar flexibilidade)
    if progress.get("voz"):
        content_pages.append(
            st.Page("pages/05_🔄_Monoflow.py", title="Monoflow", icon="🔄")
        )

    # ── 📦 Produto (wizard progressivo) ──
    product_pages = []
    # 1. ICP — sempre disponível (primeiro passo do Produto)
    product_pages.append(
        st.Page("pages/01_🎯_ICP.py", title="ICP", icon="🎯")
    )
    # 2. Oferta — libera após ICP
    if progress.get("icp"):
        product_pages.append(
            st.Page("pages/02_💰_Oferta.py", title="Oferta", icon="💰")
        )
    # 3. Pitch — libera após Oferta
    if progress.get("oferta"):
        product_pages.append(
            st.Page("pages/03_🎤_Pitch.py", title="Pitch", icon="🎤")
        )

    # ── ⚙️ Sistema (sempre disponível) ──
    system_pages = [
        st.Page("pages/08_⚙️_Settings.py", title="Configurações", icon="⚙️"),
    ]

    # Monta navegação agrupada (ordem: Conteúdo vem antes de Produto)
    pg = st.navigation(
        {
            "🏠 Início": home_pages,
            "✨ Conteúdo": content_pages,
            "📦 Produto": product_pages,
            "⚙️ Sistema": system_pages,
        }
    )

pg.run()
