import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo

st.set_page_config(
    page_title="Gerador de Carrosséis",
    page_icon="🎠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa banco de dados
init_db()

# ── Sidebar ──────────────────────────────────────────────────────────────

st.sidebar.title("Gerador de Carrosséis")
st.sidebar.markdown("---")

# Seletor de ICP ativo
conn = get_connection()
icps = repo.list_icps(conn)

if icps:
    icp_options = {icp.id: icp.name for icp in icps}
    selected_id = st.sidebar.selectbox(
        "ICP Ativo",
        options=list(icp_options.keys()),
        format_func=lambda x: icp_options[x],
        key="active_icp_id",
    )
    st.session_state["active_icp"] = repo.get_icp(conn, selected_id)
else:
    st.sidebar.info("Nenhum ICP cadastrado. Crie um na página ICP.")
    st.session_state["active_icp"] = None

st.sidebar.markdown("---")
st.sidebar.caption("Navegue pelas páginas no menu acima.")

# ── Página principal ─────────────────────────────────────────────────────

st.title("Gerador de Carrosséis para Instagram")
st.markdown(
    """
    Bem-vindo! Use o menu lateral para navegar entre as etapas:

    1. **ICP** — Cadastre seu cliente ideal
    2. **Oferta** — Construa sua oferta irresistível
    3. **Pitch** — Gere seu pitch de vendas
    4. **Ideas** — Gere ideias de carrosséis
    5. **Copywriter** — Escreva o copy de cada slide
    6. **Design** — Crie o visual dos slides
    7. **Settings** — Configure APIs e conexões
    """
)

if st.session_state.get("active_icp"):
    icp = st.session_state["active_icp"]
    st.subheader(f"ICP Ativo: {icp.name}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nicho:** {icp.niche}")
        st.markdown(f"**Estilo de linguagem:** {icp.language_style}")
    with col2:
        st.markdown(f"**Dores:** {', '.join(icp.pain_points[:3])}")
        st.markdown(f"**Desejos:** {', '.join(icp.desires[:3])}")
