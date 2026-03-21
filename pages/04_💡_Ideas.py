from __future__ import annotations

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from services.content_generator import generate_ideas

st.set_page_config(page_title="Ideas", page_icon="💡", layout="wide")
st.title("Geração de Ideias")

init_db()
conn = get_connection()

# ── Verificar ICP ativo ──────────────────────────────────────────────────

icps = repo.list_icps(conn)
if not icps:
    st.warning("Crie um ICP primeiro na página ICP.")
    st.stop()

icp_options = {icp.id: icp.name for icp in icps}
selected_id = st.selectbox(
    "Selecione o ICP",
    options=list(icp_options.keys()),
    format_func=lambda x: icp_options[x],
)
icp = repo.get_icp(conn, selected_id)

# ── Resumo do ICP ────────────────────────────────────────────────────────

with st.expander("Resumo do ICP", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nicho:** {icp.niche}")
        st.markdown(f"**Linguagem:** {icp.language_style}")
        st.markdown(f"**Tom:** {', '.join(icp.tone_keywords)}")
    with col2:
        st.markdown(f"**Dores:** {', '.join(icp.pain_points[:3])}")
        st.markdown(f"**Desejos:** {', '.join(icp.desires[:3])}")

# ── Padrões de analytics (se disponíveis) ────────────────────────────────

patterns = st.session_state.get("analytics_patterns")
if patterns:
    st.info("Padrões de analytics detectados — serão usados na geração de ideias.")

active_offer = st.session_state.get("active_offer")
if active_offer:
    st.info(f"Oferta ativa: **{active_offer.name}** — será usada na geração de ideias.")

# ── Geração ──────────────────────────────────────────────────────────────

st.markdown("---")

col_count, col_btn = st.columns([1, 2])
with col_count:
    count = st.slider("Quantidade de ideias", min_value=3, max_value=10, value=5)

with col_btn:
    st.write("")  # espaçamento
    st.write("")
    generate_btn = st.button("Gerar Ideias", type="primary", use_container_width=True)

if generate_btn:
    with st.spinner("Gerando ideias com IA..."):
        try:
            ideas = generate_ideas(icp, patterns=patterns, count=count, offer=active_offer)
            st.session_state["generated_ideas"] = ideas
        except Exception as e:
            st.error(f"Erro ao gerar ideias: {e}")
            st.info("Verifique sua API key na página Settings.")
            st.stop()

# ── Exibir ideias ────────────────────────────────────────────────────────

ideas = st.session_state.get("generated_ideas", [])

if ideas:
    st.subheader(f"{len(ideas)} ideias geradas")

    for i, idea in enumerate(ideas):
        with st.container():
            st.markdown(f"### {i + 1}. {idea.get('topic', 'Sem tema')}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Hook:** {idea.get('hook', '-')}")
            with col2:
                st.markdown(f"**Ângulo:** {idea.get('angle', '-')}")
            with col3:
                st.markdown(f"**Emoção:** {idea.get('target_emotion', '-')}")

            style_label = {
                "educational": "Educativo",
                "storytelling": "Storytelling",
                "listicle": "Lista",
                "myth_busting": "Quebrando mitos",
                "before_after": "Antes e Depois",
            }
            st.caption(
                f"Estilo: {style_label.get(idea.get('carousel_style', ''), idea.get('carousel_style', '-'))}"
            )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🔄 Usar no Monoflow", key=f"monoflow_idea_{i}", type="primary", use_container_width=True):
                    st.session_state["monoflow_idea"] = idea
                    st.session_state["selected_icp_id"] = icp.id
                    st.success("Ideia selecionada! Vá para a página **Monoflow**.")
            with btn_col2:
                if st.button("✍️ Usar no Copywriter", key=f"use_idea_{i}", use_container_width=True):
                    st.session_state["selected_idea"] = idea
                    st.session_state["selected_icp_id"] = icp.id
                    st.success("Ideia selecionada! Vá para a página **Copywriter**.")

            st.markdown("---")
