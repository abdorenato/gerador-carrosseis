from __future__ import annotations

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from db.models import ICP
from typing import Optional

st.set_page_config(page_title="ICP", page_icon="🎯", layout="wide")
st.title("Perfil de Cliente Ideal (ICP)")

init_db()
conn = get_connection()

# ── Estado ───────────────────────────────────────────────────────────────

if "editing_icp_id" not in st.session_state:
    st.session_state["editing_icp_id"] = None

# ── Formulário ───────────────────────────────────────────────────────────


def _show_form(icp: ICP | None = None):
    """Mostra formulário para criar ou editar um ICP."""
    is_edit = icp is not None
    prefix = f"edit_{icp.id}" if is_edit else "new"

    with st.form(f"icp_form_{prefix}", clear_on_submit=not is_edit):
        st.subheader("Editar ICP" if is_edit else "Novo ICP")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome do ICP", value=icp.name if is_edit else "")
            niche = st.text_input("Nicho", value=icp.niche if is_edit else "")
        with col2:
            age_range = st.text_input(
                "Faixa etária",
                value=icp.demographics.get("age_range", "") if is_edit else "",
                placeholder="ex: 25-45",
            )
            gender = st.selectbox(
                "Gênero",
                options=["Todos", "Masculino", "Feminino"],
                index=(
                    ["Todos", "Masculino", "Feminino"].index(
                        icp.demographics.get("gender", "Todos")
                    )
                    if is_edit
                    else 0
                ),
            )
            location = st.text_input(
                "Localização",
                value=icp.demographics.get("location", "") if is_edit else "",
                placeholder="ex: Brasil",
            )

        pain_points_str = st.text_area(
            "Dores (uma por linha)",
            value="\n".join(icp.pain_points) if is_edit else "",
            height=100,
            placeholder="ex:\nNão consegue engajamento\nNão sabe o que postar",
        )
        desires_str = st.text_area(
            "Desejos (um por linha)",
            value="\n".join(icp.desires) if is_edit else "",
            height=100,
            placeholder="ex:\nCrescer seguidores organicamente\nMonetizar o perfil",
        )
        objections_str = st.text_area(
            "Objeções (uma por linha)",
            value="\n".join(icp.objections) if is_edit else "",
            height=100,
            placeholder="ex:\nNão tenho tempo\nÉ muito caro",
        )

        language_style = st.text_area(
            "Estilo de linguagem",
            value=icp.language_style if is_edit else "",
            height=80,
            placeholder="ex: Informal, direto, usa gírias, emojis moderados",
        )
        tone_keywords_str = st.text_input(
            "Palavras-chave de tom (separadas por vírgula)",
            value=", ".join(icp.tone_keywords) if is_edit else "",
            placeholder="ex: motivacional, educativo, provocativo",
        )

        submitted = st.form_submit_button(
            "Atualizar" if is_edit else "Criar ICP", type="primary"
        )

        if submitted:
            if not name or not niche:
                st.error("Nome e Nicho são obrigatórios.")
                return

            pain_points = [p.strip() for p in pain_points_str.strip().splitlines() if p.strip()]
            desires = [d.strip() for d in desires_str.strip().splitlines() if d.strip()]
            objections = [o.strip() for o in objections_str.strip().splitlines() if o.strip()]
            tone_keywords = [t.strip() for t in tone_keywords_str.split(",") if t.strip()]
            demographics = {
                "age_range": age_range,
                "gender": gender,
                "location": location,
            }

            if is_edit:
                icp.name = name
                icp.niche = niche
                icp.demographics = demographics
                icp.pain_points = pain_points
                icp.desires = desires
                icp.objections = objections
                icp.language_style = language_style
                icp.tone_keywords = tone_keywords
                repo.update_icp(conn, icp)
                st.success(f"ICP '{name}' atualizado!")
                st.session_state["editing_icp_id"] = None
                st.rerun()
            else:
                new_icp = ICP(
                    name=name,
                    niche=niche,
                    demographics=demographics,
                    pain_points=pain_points,
                    desires=desires,
                    objections=objections,
                    language_style=language_style,
                    tone_keywords=tone_keywords,
                )
                repo.create_icp(conn, new_icp)
                st.success(f"ICP '{name}' criado!")
                st.rerun()


# ── Lista de ICPs ────────────────────────────────────────────────────────

icps = repo.list_icps(conn)

if icps:
    st.subheader(f"ICPs cadastrados ({len(icps)})")
    for icp in icps:
        with st.expander(f"**{icp.name}** — {icp.niche}", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Faixa etária:** {icp.demographics.get('age_range', '-')}")
                st.markdown(f"**Gênero:** {icp.demographics.get('gender', '-')}")
                st.markdown(f"**Localização:** {icp.demographics.get('location', '-')}")
            with col2:
                st.markdown("**Dores:**")
                for p in icp.pain_points:
                    st.markdown(f"- {p}")
                st.markdown("**Desejos:**")
                for d in icp.desires:
                    st.markdown(f"- {d}")
            with col3:
                st.markdown("**Objeções:**")
                for o in icp.objections:
                    st.markdown(f"- {o}")
                st.markdown(f"**Tom:** {', '.join(icp.tone_keywords)}")
                st.markdown(f"**Linguagem:** {icp.language_style}")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Editar", key=f"edit_{icp.id}"):
                    st.session_state["editing_icp_id"] = icp.id
                    st.rerun()
            with btn_col2:
                if st.button("Excluir", key=f"del_{icp.id}"):
                    repo.delete_icp(conn, icp.id)
                    st.success(f"ICP '{icp.name}' excluído.")
                    st.rerun()

st.markdown("---")

# ── Exibir formulário ────────────────────────────────────────────────────

editing_id = st.session_state.get("editing_icp_id")
if editing_id:
    editing_icp = repo.get_icp(conn, editing_id)
    if editing_icp:
        _show_form(editing_icp)
        if st.button("Cancelar edição"):
            st.session_state["editing_icp_id"] = None
            st.rerun()
    else:
        st.session_state["editing_icp_id"] = None
else:
    _show_form()
