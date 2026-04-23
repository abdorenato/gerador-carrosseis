"""Helper para proteger páginas que exigem login."""

from __future__ import annotations

import streamlit as st


def require_login():
    """Verifica se o usuário está logado. Se não estiver, mostra mensagem
    e bloqueia o resto da página."""
    user = st.session_state.get("user")
    if not user:
        # Esconde a sidebar inteira
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown(
                """
                <div style="text-align: center; padding: 80px 0;">
                    <div style="font-size: 64px;">🔒</div>
                    <h2>Ei, antes de entrar aqui...</h2>
                    <p style="color: #888; font-size: 16px;">
                        Preciso te conhecer antes. Volta pra entrada que eu te guio em 6 passos.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link("app.py", label="← Voltar para o iAbdo", icon="🚀")
        st.stop()
    return user
