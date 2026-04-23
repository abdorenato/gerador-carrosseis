"""Voz da Marca — 6 perguntas → arquétipo + mapa de voz.

Fluxo:
1. Perguntas (se ainda não respondidas)
2. IA analisa e sugere arquétipo + mapa de voz
3. Usuário revisa/edita/regera
4. Salva na sessão e libera próximo passo
"""

from __future__ import annotations

import streamlit as st

from services.supabase_service import (
    save_voz,
    get_voz,
    is_configured as supabase_configured,
)
from services.voz_generator import (
    ARCHETYPES,
    DISCOVERY_QUESTIONS,
    descobrir_voz,
)


from utils.auth_guard import require_login

st.set_page_config(page_title="Voz da Marca — iAbdo", page_icon="🎙️", layout="wide")
user = require_login()

# ── Estado da voz (carrega do Supabase se existir) ──
voz_state = st.session_state.setdefault("voz_state", {"step": "perguntas", "answers": {}, "result": None})

# Se é a primeira vez entrando na página e temos user_id, tenta carregar do banco
if not voz_state.get("loaded_from_db") and user.get("id") and supabase_configured():
    voz_state["loaded_from_db"] = True
    try:
        existing = get_voz(user["id"])
        if existing and existing.get("arquetipo_primario"):
            voz_state["answers"] = existing.get("respostas") or {}
            voz_state["result"] = {
                "arquetipo_primario": existing["arquetipo_primario"],
                "arquetipo_secundario": existing.get("arquetipo_secundario"),
                "justificativa": existing.get("justificativa", ""),
                "mapa_voz": existing.get("mapa_voz") or {},
            }
            voz_state["step"] = "revisao"
    except Exception:
        pass

# ── Header ──
st.markdown(
    """
    <div style="padding: 10px 0;">
        <h1 style="margin: 0;">🎙️ Voz da Marca</h1>
        <p style="color: #888; font-size: 16px; margin: 4px 0;">
            Antes de falar, precisamos descobrir <b>como</b> você fala.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 1: PERGUNTAS
# ═══════════════════════════════════════════════════════════════════════════

if voz_state["step"] == "perguntas":
    st.markdown(
        f"""
        ### Oi {user['name'].split()[0]}, aqui é o iAbdo 👋

        Vou te fazer **6 perguntas curtas** pra descobrir seu arquétipo de voz.
        Responde do jeito que te vier — **não precisa ser perfeito**, precisa ser verdadeiro.

        Depois eu analiso tudo e te entrego seu **Mapa de Voz Autêntica**.
        """
    )
    st.markdown("")

    with st.form("voz_form"):
        answers = {}
        for i, q in enumerate(DISCOVERY_QUESTIONS, 1):
            st.markdown(f"**{i}. {q['question']}**")
            answers[q["key"]] = st.text_area(
                q["question"],
                value=voz_state["answers"].get(q["key"], ""),
                help=q.get("help", ""),
                label_visibility="collapsed",
                height=80,
                key=f"voz_q_{q['key']}",
            )
            st.markdown("")

        submit = st.form_submit_button(
            "🔮 Descobrir minha voz",
            type="primary",
            use_container_width=True,
        )

    if submit:
        # Valida: pelo menos 4 respostas com conteúdo
        filled = sum(1 for v in answers.values() if v.strip())
        if filled < 4:
            st.error(
                "Responde pelo menos 4 perguntas pra eu conseguir fazer uma análise decente. "
                f"Você preencheu {filled} de 6."
            )
        else:
            voz_state["answers"] = answers
            with st.spinner("Analisando sua voz..."):
                try:
                    result = descobrir_voz(answers)
                    voz_state["result"] = result
                    voz_state["step"] = "revisao"
                    st.rerun()
                except Exception as e:
                    st.error(f"Deu ruim na análise: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# ETAPA 2: REVISÃO
# ═══════════════════════════════════════════════════════════════════════════

elif voz_state["step"] == "revisao":
    result = voz_state["result"]
    if not result:
        voz_state["step"] = "perguntas"
        st.rerun()

    prim_key = result.get("arquetipo_primario", "especialista")
    sec_key = result.get("arquetipo_secundario", "especialista")
    prim = ARCHETYPES.get(prim_key, ARCHETYPES["especialista"])
    sec = ARCHETYPES.get(sec_key, ARCHETYPES["especialista"])
    mapa = result.get("mapa_voz", {})

    # ── Arquétipos ──
    st.markdown("### 🔮 Sua Identificação Arquetípica")
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown(f"#### PRIMÁRIO\n{prim['name']}")
            st.caption(prim["subtitle"])
            st.markdown(prim["description"])
            st.caption(f"Energia: {prim['energy']}")
    with col_b:
        with st.container(border=True):
            st.markdown(f"#### SECUNDÁRIO\n{sec['name']}")
            st.caption(sec["subtitle"])
            st.markdown(sec["description"])
            st.caption(f"Energia: {sec['energy']}")

    with st.expander("💭 Por que esses arquétipos?"):
        st.write(result.get("justificativa", ""))

    st.markdown("---")

    # ── Mapa de Voz ──
    st.markdown("### 🎤 Seu Mapa de Voz Autêntica")

    with st.container(border=True):
        st.markdown(f"**Energia Arquetípica:** {mapa.get('energia_arquetipica', '')}")
        st.markdown(f"**Tom de Voz:** {mapa.get('tom_de_voz', '')}")
        st.markdown(f"**Frase de Essência:** *\"{mapa.get('frase_essencia', '')}\"*")
        st.markdown(f"**Frase de Impacto:** *\"{mapa.get('frase_impacto', '')}\"*")

        col_u, col_e = st.columns(2)
        with col_u:
            st.markdown("**Palavras que eu uso:**")
            for w in mapa.get("palavras_usar", []):
                st.markdown(f"- {w}")
        with col_e:
            st.markdown("**Palavras que eu evito:**")
            for w in mapa.get("palavras_evitar", []):
                st.markdown(f"- {w}")

    st.markdown("---")

    # ── Ações ──
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Editar respostas", use_container_width=True):
            voz_state["step"] = "perguntas"
            st.rerun()
    with col2:
        if st.button("🔄 Regerar análise", use_container_width=True):
            with st.spinner("Regerando..."):
                try:
                    voz_state["result"] = descobrir_voz(voz_state["answers"])
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
    with col3:
        if st.button("✅ Essa é minha voz", type="primary", use_container_width=True):
            # Salva no Supabase
            saved = False
            if user.get("id") and supabase_configured():
                try:
                    saved = save_voz(user["id"], {
                        "arquetipo_primario": prim_key,
                        "arquetipo_secundario": sec_key,
                        "justificativa": result.get("justificativa", ""),
                        "mapa_voz": mapa,
                        "respostas": voz_state["answers"],
                    })
                except Exception as e:
                    st.warning(f"Salvei na sessão mas falhou no banco: {e}")

            # Salva na sessão
            st.session_state.setdefault("progress", {})["voz"] = True
            st.session_state["voz_salva"] = {
                "arquetipo_primario": prim_key,
                "arquetipo_secundario": sec_key,
                "mapa_voz": mapa,
                "justificativa": result.get("justificativa", ""),
            }
            if saved:
                st.success("🎉 Voz salva no banco! Vamos pro próximo passo.")
            else:
                st.success("🎉 Voz salva! (apenas na sessão)")
            st.balloons()

    # ── Edição manual do mapa (opcional) ──
    with st.expander("✏️ Quero editar manualmente o mapa de voz"):
        new_energia = st.text_input("Energia arquetípica", value=mapa.get("energia_arquetipica", ""))
        new_tom = st.text_input("Tom de voz", value=mapa.get("tom_de_voz", ""))
        new_essencia = st.text_input("Frase de essência", value=mapa.get("frase_essencia", ""))
        new_impacto = st.text_input("Frase de impacto", value=mapa.get("frase_impacto", ""))
        new_usar = st.text_input(
            "Palavras que eu uso (separadas por vírgula)",
            value=", ".join(mapa.get("palavras_usar", [])),
        )
        new_evitar = st.text_input(
            "Palavras que eu evito (separadas por vírgula)",
            value=", ".join(mapa.get("palavras_evitar", [])),
        )

        if st.button("💾 Salvar edições"):
            result["mapa_voz"] = {
                "energia_arquetipica": new_energia,
                "tom_de_voz": new_tom,
                "frase_essencia": new_essencia,
                "frase_impacto": new_impacto,
                "palavras_usar": [w.strip() for w in new_usar.split(",") if w.strip()],
                "palavras_evitar": [w.strip() for w in new_evitar.split(",") if w.strip()],
            }
            voz_state["result"] = result
            st.rerun()
