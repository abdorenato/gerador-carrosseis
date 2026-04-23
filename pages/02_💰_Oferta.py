from __future__ import annotations

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from db.models import Offer
from services.content_generator import (
    generate_full_offer,
    suggest_offer_component,
    generate_offer_summary,
)

from utils.auth_guard import require_login

st.set_page_config(page_title="Oferta", page_icon="💰", layout="wide")
require_login()
st.title("Construção de Oferta Irresistível")

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

# ── Equação de Valor ─────────────────────────────────────────────────────

st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px;
         border-radius: 12px; margin-bottom: 24px; text-align: center;">
        <p style="color: #ccc; font-size: 14px; margin-bottom: 8px;">Equação de Valor</p>
        <p style="color: white; font-size: 22px; font-weight: bold;">
            Valor = (Sonho &times; Probabilidade de Sucesso) &divide; (Tempo &times; Esforço)
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Session state ────────────────────────────────────────────────────────

if "offer_step" not in st.session_state:
    st.session_state["offer_step"] = "input"
if "editing_offer_id" not in st.session_state:
    st.session_state["editing_offer_id"] = None
if "generated_offer" not in st.session_state:
    st.session_state["generated_offer"] = None

# Se estiver editando, pular direto para review
editing_id = st.session_state["editing_offer_id"]
if editing_id:
    editing_offer = repo.get_offer(conn, editing_id)
    if editing_offer and not st.session_state.get("generated_offer"):
        st.session_state["generated_offer"] = {
            "name": editing_offer.name,
            "dream": editing_offer.dream,
            "success_proofs": editing_offer.success_proofs,
            "time_to_result": editing_offer.time_to_result,
            "effort_level": editing_offer.effort_level,
            "core_promise": editing_offer.core_promise,
            "bonuses": editing_offer.bonuses,
            "scarcity": editing_offer.scarcity,
            "guarantee": editing_offer.guarantee,
            "method_name": editing_offer.method_name,
        }
        st.session_state["offer_step"] = "review"

# ══════════════════════════════════════════════════════════════════════════
# ETAPA 1: Perguntas essenciais
# ══════════════════════════════════════════════════════════════════════════

if st.session_state["offer_step"] == "input":
    st.subheader("Me conte sobre seu negócio")
    st.caption("Responda 3 perguntas e a IA vai construir sua oferta irresistível.")

    product = st.text_area(
        "🛍️ O que você vende?",
        placeholder="Descreva seu produto ou serviço.\nEx: Mentoria de emagrecimento para mulheres 30+",
        height=80,
        key="input_product",
    )

    differentiator = st.text_area(
        "⭐ Qual seu diferencial?",
        placeholder="O que te diferencia dos concorrentes?\nEx: Método sem dieta restritiva, baseado em neurociência",
        height=80,
        key="input_differentiator",
    )

    price_range = st.selectbox(
        "💰 Faixa de preço",
        options=[
            "Gratuito / Isca digital",
            "Até R$100 (produto de entrada)",
            "R$100 - R$500 (ticket médio)",
            "R$500 - R$2.000 (ticket alto)",
            "R$2.000+ (high ticket)",
        ],
        key="input_price",
    )

    st.markdown("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        generate_btn = st.button(
            "🚀 Gerar oferta com IA",
            type="primary",
            use_container_width=True,
            disabled=not (product and differentiator),
        )
    with col2:
        manual_btn = st.button("Preencher manualmente", use_container_width=True)

    if generate_btn:
        with st.spinner("Construindo sua oferta irresistível..."):
            try:
                result = generate_full_offer(icp, product, differentiator, price_range)
                st.session_state["generated_offer"] = result
                st.session_state["offer_step"] = "review"
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gerar oferta: {e}")

    if manual_btn:
        st.session_state["generated_offer"] = {
            "name": "", "dream": "", "success_proofs": [],
            "time_to_result": "", "effort_level": "",
            "core_promise": "", "bonuses": [],
            "scarcity": "", "guarantee": "", "method_name": "",
        }
        st.session_state["offer_step"] = "review"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# ETAPA 2: Revisar e ajustar
# ══════════════════════════════════════════════════════════════════════════

elif st.session_state["offer_step"] == "review":
    offer_data = st.session_state["generated_offer"]

    is_edit = editing_id is not None
    st.subheader("Revise e ajuste sua oferta" if not is_edit else "Editando oferta")

    col_back, col_regen = st.columns([1, 1])
    with col_back:
        if st.button("← Voltar"):
            st.session_state["offer_step"] = "input"
            st.session_state["generated_offer"] = None
            st.session_state["editing_offer_id"] = None
            st.rerun()
    with col_regen:
        if not is_edit:
            if st.button("🔄 Regenerar com IA"):
                st.session_state["offer_step"] = "input"
                st.session_state["generated_offer"] = None
                st.rerun()

    st.markdown("---")

    # Nome
    offer_name = st.text_input(
        "Nome da oferta",
        value=offer_data.get("name", ""),
        key="review_name",
    )

    # ── Equação de Valor ─────────────────────────────────────────────────
    st.markdown("### 📐 Equação de Valor")
    st.markdown("**📈 Maximize o numerador**")

    col1, col2 = st.columns([4, 1])
    with col1:
        dream = st.text_area(
            "🌟 Sonho",
            value=offer_data.get("dream", ""),
            height=60, key="review_dream",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_dream"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_dream"] = suggest_offer_component(icp, "dream", dream)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_dream"):
        for s in st.session_state["sug_dream"]:
            st.info(f"💡 {s}")

    col1, col2 = st.columns([4, 1])
    with col1:
        proofs_text = "\n".join(offer_data.get("success_proofs", []))
        proofs = st.text_area(
            "✅ Probabilidade de Sucesso",
            value=proofs_text,
            height=60, key="review_proofs",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_proofs"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_proofs"] = suggest_offer_component(icp, "success_proofs", proofs)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_proofs"):
        for s in st.session_state["sug_proofs"]:
            st.info(f"💡 {s}")

    st.markdown("**📉 Minimize o denominador**")

    col1, col2 = st.columns([4, 1])
    with col1:
        time_result = st.text_area(
            "⏱️ Tempo",
            value=offer_data.get("time_to_result", ""),
            height=50, key="review_time",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_time"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_time"] = suggest_offer_component(icp, "time_to_result", time_result)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_time"):
        for s in st.session_state["sug_time"]:
            st.info(f"💡 {s}")

    col1, col2 = st.columns([4, 1])
    with col1:
        effort = st.text_area(
            "💪 Esforço & Sacrifício",
            value=offer_data.get("effort_level", ""),
            height=50, key="review_effort",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_effort"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_effort"] = suggest_offer_component(icp, "effort_level", effort)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_effort"):
        for s in st.session_state["sug_effort"]:
            st.info(f"💡 {s}")

    # ── Componentes da Oferta ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🧱 Componentes da Oferta")

    col1, col2 = st.columns([4, 1])
    with col1:
        core_promise = st.text_area(
            "🎯 Core Promise",
            value=offer_data.get("core_promise", ""),
            height=50, key="review_promise",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_promise"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_promise"] = suggest_offer_component(icp, "core_promise", core_promise)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_promise"):
        for s in st.session_state["sug_promise"]:
            st.info(f"💡 {s}")

    col1, col2 = st.columns([4, 1])
    with col1:
        bonuses_text = "\n".join(offer_data.get("bonuses", []))
        bonuses = st.text_area(
            "🎁 Bônus (um por linha)",
            value=bonuses_text,
            height=60, key="review_bonuses",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_bonuses"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_bonuses"] = suggest_offer_component(icp, "bonuses", bonuses)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_bonuses"):
        for s in st.session_state["sug_bonuses"]:
            st.info(f"💡 {s}")

    col1, col2 = st.columns([4, 1])
    with col1:
        scarcity = st.text_area(
            "⏳ Escassez & Urgência",
            value=offer_data.get("scarcity", ""),
            height=50, key="review_scarcity",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_scarcity"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_scarcity"] = suggest_offer_component(icp, "scarcity", scarcity)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_scarcity"):
        for s in st.session_state["sug_scarcity"]:
            st.info(f"💡 {s}")

    col1, col2 = st.columns([4, 1])
    with col1:
        guarantee = st.text_area(
            "🛡️ Garantia",
            value=offer_data.get("guarantee", ""),
            height=50, key="review_guarantee",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("IA", key="s_guarantee"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_guarantee"] = suggest_offer_component(icp, "guarantee", guarantee)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_guarantee"):
        for s in st.session_state["sug_guarantee"]:
            st.info(f"💡 {s}")

    col1, col2 = st.columns([4, 1])
    with col1:
        method_name = st.text_input(
            "✨ Nome do Método",
            value=offer_data.get("method_name", ""),
            key="review_method",
        )
    with col2:
        if st.button("IA", key="s_method"):
            with st.spinner("..."):
                try:
                    st.session_state["sug_method"] = suggest_offer_component(icp, "method_name", method_name)
                except Exception as e:
                    st.error(str(e))
    if st.session_state.get("sug_method"):
        for s in st.session_state["sug_method"]:
            st.info(f"💡 {s}")

    # ── Salvar ───────────────────────────────────────────────────────────
    st.markdown("---")

    proofs_list = [p.strip() for p in proofs.splitlines() if p.strip()]
    bonuses_list = [b.strip() for b in bonuses.splitlines() if b.strip()]

    col_save, col_summary = st.columns(2)

    with col_save:
        save_btn = st.button(
            "💾 Salvar oferta",
            type="primary",
            use_container_width=True,
        )
    with col_summary:
        summary_btn = st.button(
            "📝 Gerar resumo com IA",
            use_container_width=True,
            disabled=not (offer_name and dream),
        )

    if save_btn:
        if not offer_name or not dream:
            st.error("Preencha pelo menos o nome e o sonho da oferta.")
        else:
            offer = Offer(
                icp_id=icp.id,
                name=offer_name,
                dream=dream,
                success_proofs=proofs_list,
                time_to_result=time_result,
                effort_level=effort,
                core_promise=core_promise,
                bonuses=bonuses_list,
                scarcity=scarcity,
                guarantee=guarantee,
                method_name=method_name,
                summary=st.session_state.get("offer_summary_text", ""),
                id=editing_id,
            )
            if is_edit:
                repo.update_offer(conn, offer)
                st.success("Oferta atualizada!")
            else:
                new_id = repo.create_offer(conn, offer)
                offer.id = new_id
                # Marca progresso para desbloquear Pitch
                st.session_state.setdefault("progress", {})["oferta"] = True
                st.success("Oferta salva!")

            st.session_state["active_offer"] = offer
            st.session_state["offer_step"] = "input"
            st.session_state["generated_offer"] = None
            st.session_state["editing_offer_id"] = None
            for k in list(st.session_state.keys()):
                if k.startswith("sug_"):
                    del st.session_state[k]
            st.rerun()

    if summary_btn:
        temp_offer = Offer(
            icp_id=icp.id, name=offer_name, dream=dream,
            success_proofs=proofs_list, time_to_result=time_result,
            effort_level=effort, core_promise=core_promise,
            bonuses=bonuses_list, scarcity=scarcity,
            guarantee=guarantee, method_name=method_name,
        )
        with st.spinner("Gerando resumo..."):
            try:
                st.session_state["offer_summary_text"] = generate_offer_summary(icp, temp_offer)
            except Exception as e:
                st.error(f"Erro: {e}")

    if st.session_state.get("offer_summary_text"):
        st.markdown("### Resumo da Oferta")
        st.markdown(st.session_state["offer_summary_text"])

# ══════════════════════════════════════════════════════════════════════════
# Ofertas salvas (sempre visível)
# ══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("Ofertas salvas")

offers = repo.list_offers_by_icp(conn, icp.id)

# Se já tem ofertas, marca progresso como feito
if offers:
    st.session_state.setdefault("progress", {})["oferta"] = True

if not offers:
    st.info("Nenhuma oferta salva para este ICP.")
else:
    for offer in offers:
        with st.expander(f"💰 {offer.name}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Core Promise:** {offer.core_promise}")
                st.markdown(f"**Sonho:** {offer.dream}")
                st.markdown(f"**Provas:** {', '.join(offer.success_proofs)}")
                st.markdown(f"**Tempo:** {offer.time_to_result}")
                st.markdown(f"**Esforço:** {offer.effort_level}")
            with col2:
                st.markdown(f"**Bônus:** {', '.join(offer.bonuses)}")
                st.markdown(f"**Escassez:** {offer.scarcity}")
                st.markdown(f"**Garantia:** {offer.guarantee}")
                st.markdown(f"**Método:** {offer.method_name}")

            if offer.summary:
                st.markdown("**Resumo:**")
                st.markdown(offer.summary)

            col_use, col_edit, col_del = st.columns(3)
            with col_use:
                if st.button("Usar esta oferta", key=f"use_{offer.id}", type="primary"):
                    st.session_state["active_offer"] = offer
                    st.success("Oferta ativa! Vá para **Ideas**.")
            with col_edit:
                if st.button("Editar", key=f"edit_{offer.id}"):
                    st.session_state["editing_offer_id"] = offer.id
                    st.session_state["generated_offer"] = None
                    st.session_state.pop("offer_summary_text", None)
                    st.rerun()
            with col_del:
                if st.button("Excluir", key=f"del_{offer.id}"):
                    repo.delete_offer(conn, offer.id)
                    if st.session_state.get("active_offer") and st.session_state["active_offer"].id == offer.id:
                        st.session_state.pop("active_offer", None)
                    st.rerun()
