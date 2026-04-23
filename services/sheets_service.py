"""Serviço de integração com Google Sheets para captação de leads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st


def _get_credentials():
    """Carrega credenciais da Service Account do Google Cloud.

    Espera em st.secrets["gcp_service_account"] um dict com o JSON da key.
    """
    try:
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None

    if "gcp_service_account" not in st.secrets:
        return None

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=scopes,
        )
        return creds
    except Exception:
        return None


def _get_worksheet():
    """Retorna a worksheet de leads ou None se não configurada."""
    try:
        import gspread
    except ImportError:
        return None

    creds = _get_credentials()
    if not creds:
        return None

    sheet_url = st.secrets.get("LEADS_SHEET_URL", "")
    if not sheet_url:
        return None

    try:
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url)
        return sheet.sheet1
    except Exception:
        return None


def is_configured() -> bool:
    """Verifica se o Google Sheets está configurado."""
    return _get_worksheet() is not None


def register_lead(name: str, email: str, instagram: str = "") -> bool:
    """Registra um lead novo no Google Sheets.

    Retorna True se registrou com sucesso, False se não está configurado
    ou se falhou.
    """
    ws = _get_worksheet()
    if not ws:
        return False

    try:
        # Verifica se já existe pelo email
        try:
            existing = ws.find(email, in_column=3)  # coluna email
            if existing:
                return True  # já cadastrado, ignora silenciosamente
        except Exception:
            pass

        ws.append_row(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                email,
                instagram,
                "Iniciou",  # progresso
                "",  # voz_arquetipo
            ],
            value_input_option="USER_ENTERED",
        )
        return True
    except Exception:
        return False


def update_progress(email: str, progress: str, voz_arquetipo: str = "") -> bool:
    """Atualiza o progresso de um lead já cadastrado."""
    ws = _get_worksheet()
    if not ws:
        return False

    try:
        cell = ws.find(email, in_column=3)
        if not cell:
            return False
        row = cell.row
        ws.update_cell(row, 5, progress)  # coluna E (progresso)
        if voz_arquetipo:
            ws.update_cell(row, 6, voz_arquetipo)  # coluna F
        return True
    except Exception:
        return False
