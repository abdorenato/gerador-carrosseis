from __future__ import annotations

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from db.models import CarouselProject, SlideContent
from services.content_generator import write_carousel_copy, refine_slide, generate_caption

from utils.auth_guard import require_login

st.set_page_config(page_title="Copywriter", page_icon="✍️", layout="wide")
require_login()
st.title("Copywriter de Carrossel")

init_db()
conn = get_connection()

# ── Verificar ideia selecionada ou entrada manual ────────────────────────

idea = st.session_state.get("selected_idea")
selected_icp_id = st.session_state.get("selected_icp_id")

icps = repo.list_icps(conn)
if not icps:
    st.warning("Crie um ICP primeiro na página ICP.")
    st.stop()

icp_options = {icp.id: icp.name for icp in icps}

tab_idea, tab_manual = st.tabs(["A partir de ideia gerada", "Entrada manual"])

with tab_idea:
    if idea:
        st.success(f"Ideia selecionada: **{idea.get('topic', '')}**")
        st.markdown(f"**Hook:** {idea.get('hook', '')}")
        st.markdown(f"**Ângulo:** {idea.get('angle', '')}")
        st.markdown(f"**Estilo:** {idea.get('carousel_style', 'educational')}")
        topic = idea.get("topic", "")
        hook = idea.get("hook", "")
        style = idea.get("carousel_style", "educational")
        icp_id = selected_icp_id or icps[0].id
    else:
        st.info("Nenhuma ideia selecionada. Gere ideias na página **Ideas** ou use a aba **Entrada manual**.")
        topic, hook, style, icp_id = "", "", "educational", icps[0].id

with tab_manual:
    icp_id_manual = st.selectbox(
        "ICP",
        options=list(icp_options.keys()),
        format_func=lambda x: icp_options[x],
        key="copy_icp",
    )
    topic_manual = st.text_input("Tema do carrossel", placeholder="ex: 5 erros que matam seu engajamento")
    hook_manual = st.text_input("Hook (frase do primeiro slide)", placeholder="ex: Você está jogando seguidores fora")
    style_manual = st.selectbox(
        "Estilo",
        options=["educational", "storytelling", "listicle", "myth_busting", "before_after"],
        format_func=lambda s: {
            "educational": "Educativo",
            "storytelling": "Storytelling",
            "listicle": "Lista",
            "myth_busting": "Quebrando mitos",
            "before_after": "Antes e Depois",
        }.get(s, s),
    )

# Decidir qual fonte usar
use_manual = not idea or (topic_manual and hook_manual)
if use_manual and topic_manual:
    topic = topic_manual
    hook = hook_manual
    style = style_manual
    icp_id = icp_id_manual

if not topic or not hook:
    st.info("Selecione uma ideia na página Ideas ou preencha os campos acima.")
    st.stop()

icp = repo.get_icp(conn, icp_id)
if not icp:
    st.error("ICP não encontrado.")
    st.stop()

# ── Configurações de geração ─────────────────────────────────────────────

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    num_slides = st.slider("Número de slides", min_value=3, max_value=10, value=7)
with col2:
    st.write("")
    st.write("")
    gen_btn = st.button("Gerar Copy", type="primary", use_container_width=True)

# ── Gerar copy ───────────────────────────────────────────────────────────

if gen_btn:
    with st.spinner("Escrevendo copy com IA..."):
        try:
            result = write_carousel_copy(icp, topic, hook, num_slides, style)
            st.session_state["carousel_slides"] = result.slides
            st.session_state["carousel_caption"] = result.caption
            st.session_state["carousel_hashtags"] = result.hashtags
            st.session_state["carousel_topic"] = topic
            st.session_state["carousel_hook"] = hook
        except Exception as e:
            st.error(f"Erro ao gerar copy: {e}")
            st.stop()

# ── Editor de slides ─────────────────────────────────────────────────────

slides = st.session_state.get("carousel_slides", [])
caption = st.session_state.get("carousel_caption", "")
hashtags = st.session_state.get("carousel_hashtags", [])

if not slides:
    st.stop()

st.markdown("---")
st.subheader("Slides do Carrossel")

updated_slides = []
for s in slides:
    with st.expander(
        f"Slide {s.index + 1} — {s.slide_type.upper()}: {s.headline[:50]}",
        expanded=True,
    ):
        col_type, col_head = st.columns([1, 3])
        with col_type:
            new_type = st.selectbox(
                "Tipo",
                options=["hook", "content", "listicle", "quote", "cta"],
                index=["hook", "content", "listicle", "quote", "cta"].index(s.slide_type)
                if s.slide_type in ["hook", "content", "listicle", "quote", "cta"]
                else 1,
                key=f"type_{s.index}",
            )
        with col_head:
            new_headline = st.text_input("Headline", value=s.headline, key=f"head_{s.index}")

        new_body = st.text_area("Corpo", value=s.body, height=80, key=f"body_{s.index}")

        # Refinar com IA
        refine_col1, refine_col2 = st.columns([3, 1])
        with refine_col1:
            refine_instruction = st.text_input(
                "Instrução para refinar",
                placeholder="ex: mais direto, com dado estatístico",
                key=f"refine_instr_{s.index}",
            )
        with refine_col2:
            st.write("")
            st.write("")
            if st.button("Refinar com IA", key=f"refine_{s.index}"):
                if refine_instruction:
                    with st.spinner("Refinando..."):
                        try:
                            current = SlideContent(
                                index=s.index,
                                slide_type=new_type,
                                headline=new_headline,
                                body=new_body,
                            )
                            refined = refine_slide(current, refine_instruction)
                            new_headline = refined.headline
                            new_body = refined.body
                            st.success("Slide refinado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

        updated_slides.append(
            SlideContent(
                index=s.index,
                slide_type=new_type,
                headline=new_headline,
                body=new_body,
                image_path=s.image_path,
            )
        )

# ── Legenda ──────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Legenda do Post")

edited_caption = st.text_area("Legenda", value=caption, height=150, key="caption_edit")
char_count = len(edited_caption)
st.caption(f"{char_count}/2200 caracteres")

if st.button("Regenerar legenda com IA"):
    with st.spinner("Gerando legenda..."):
        try:
            new_caption = generate_caption(updated_slides, icp)
            st.session_state["carousel_caption"] = new_caption
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

edited_hashtags = st.text_input(
    "Hashtags (separadas por vírgula)",
    value=", ".join(hashtags),
    key="hashtags_edit",
)

# ── Salvar projeto ───────────────────────────────────────────────────────

st.markdown("---")

if st.button("Salvar e continuar para Design →", type="primary", use_container_width=True):
    hashtags_list = [h.strip().lstrip("#") for h in edited_hashtags.split(",") if h.strip()]
    hashtags_str = " ".join(f"#{h}" for h in hashtags_list)

    project = CarouselProject(
        icp_id=icp.id,
        title=st.session_state.get("carousel_topic", topic),
        topic=st.session_state.get("carousel_topic", topic),
        hook=st.session_state.get("carousel_hook", hook),
        slides=updated_slides,
        caption=edited_caption,
        hashtags=hashtags_str,
        status="copy_done",
    )
    project_id = repo.create_project(conn, project)
    st.session_state["current_project_id"] = project_id
    st.success(f"Projeto salvo (ID: {project_id})! Vá para a página **Design**.")
