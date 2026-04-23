from __future__ import annotations

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from services.content_generator import generate_pitch, generate_pitch_final

from utils.auth_guard import require_login

st.set_page_config(page_title="Pitch", page_icon="🎤", layout="wide")
require_login()
st.title("Construção do Pitch")

init_db()
conn = get_connection()

# ── Selecionar ICP ───────────────────────────────────────────────────────

icps = repo.list_icps(conn)
if not icps:
    st.warning("Crie um ICP primeiro na página ICP.")
    st.stop()

icp_options = {i.id: i.name for i in icps}
selected_id = st.selectbox(
    "Selecione o ICP",
    options=list(icp_options.keys()),
    format_func=lambda x: icp_options[x],
)
icp = repo.get_icp(conn, selected_id)

# ── Selecionar Oferta ────────────────────────────────────────────────────

offers = repo.list_offers_by_icp(conn, icp.id)
if not offers:
    st.warning("Crie uma oferta primeiro na página Oferta.")
    st.stop()

offer_options = {o.id: o.name for o in offers}
selected_offer_id = st.selectbox(
    "Selecione a Oferta",
    options=list(offer_options.keys()),
    format_func=lambda x: offer_options[x],
)
offer = repo.get_offer(conn, selected_offer_id)

# Resumo da oferta
with st.expander("Resumo da oferta", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Core Promise:** {offer.core_promise}")
        st.markdown(f"**Sonho:** {offer.dream}")
        st.markdown(f"**Garantia:** {offer.guarantee}")
    with col2:
        st.markdown(f"**Escassez:** {offer.scarcity}")
        st.markdown(f"**Método:** {offer.method_name}")
        st.markdown(f"**Bônus:** {', '.join(offer.bonuses)}")

# ── As 5 perguntas ───────────────────────────────────────────────────────

st.markdown("---")

PITCH_QUESTIONS = [
    "Por que a pessoa tem que comprar de você?",
    "Por que comprar agora?",
    "Por que você vai se ferrar se não comprar agora?",
    "Por que eu sou a pessoa indicada para vender esse produto?",
    "Por que estou entregando mais com um valor menor?",
]

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px;
         border-radius: 12px; margin-bottom: 24px;">
        <p style="color: white; font-size: 18px; font-weight: bold; margin-bottom: 12px;">
            🎤 As 5 Perguntas do Pitch
        </p>
        <ol style="color: #ccc; font-size: 14px; margin: 0; padding-left: 20px;">
            <li>Por que comprar de <strong>você</strong>?</li>
            <li>Por que comprar <strong>agora</strong>?</li>
            <li>Por que vai se ferrar se <strong>não</strong> comprar agora?</li>
            <li>Por que <strong>eu</strong> sou a pessoa indicada para vender?</li>
            <li>Por que estou entregando <strong>mais</strong> com um valor <strong>menor</strong>?</li>
        </ol>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Gerar Pitch ──────────────────────────────────────────────────────────

if st.button("🚀 Gerar Pitch com IA", type="primary", use_container_width=True):
    with st.spinner("Construindo seu pitch de vendas..."):
        try:
            result = generate_pitch(icp, offer)
            st.session_state["pitch_answers"] = result.get("answers", [])
            st.session_state["pitch_final"] = result.get("pitch", "")
        except Exception as e:
            st.error(f"Erro ao gerar pitch: {e}")

# ── Revisão das respostas ────────────────────────────────────────────────

answers = st.session_state.get("pitch_answers", [])

if answers:
    st.markdown("---")
    st.subheader("Respostas do Pitch")
    st.caption("Revise e ajuste cada resposta. Depois gere o pitch final.")

    updated_answers = []
    for i, item in enumerate(answers):
        question = item.get("question", PITCH_QUESTIONS[i] if i < len(PITCH_QUESTIONS) else f"Pergunta {i+1}")
        answer = item.get("answer", "")

        st.markdown(f"**{i+1}. {question}**")
        edited = st.text_area(
            f"Resposta {i+1}",
            value=answer,
            height=80,
            key=f"pitch_answer_{i}",
            label_visibility="collapsed",
        )
        updated_answers.append({"question": question, "answer": edited})

    # ── Pitch Final ──────────────────────────────────────────────────────

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎤 Gerar pitch vendedor final", type="primary", use_container_width=True):
            with st.spinner("Gerando pitch final..."):
                try:
                    pitch_text = generate_pitch_final(icp, offer, updated_answers)
                    st.session_state["pitch_final"] = pitch_text
                except Exception as e:
                    st.error(f"Erro: {e}")
    with col2:
        if st.button("🔄 Regenerar tudo", use_container_width=True):
            with st.spinner("Regenerando..."):
                try:
                    result = generate_pitch(icp, offer)
                    st.session_state["pitch_answers"] = result.get("answers", [])
                    st.session_state["pitch_final"] = result.get("pitch", "")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    # Exibir pitch final
    pitch_final = st.session_state.get("pitch_final", "")
    if pitch_final:
        st.markdown("---")
        st.subheader("Pitch de Vendas")
        st.markdown(
            f"""
            <div style="background: #111; padding: 30px; border-radius: 12px;
                 border-left: 4px solid #FFD700; margin: 16px 0;">
                <div style="color: white; font-size: 16px; line-height: 1.8; white-space: pre-wrap;">{pitch_final}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Botão copiar
        st.code(pitch_final, language=None)
        st.caption("☝️ Clique no ícone de cópia no canto superior direito para copiar o pitch.")
