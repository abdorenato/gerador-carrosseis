"""Serviço de integração com Google Sheets para captação de leads.

Colunas esperadas na planilha (linha 1):
A: timestamp_inicio
B: nome
C: email
D: instagram
E: ultima_atividade
F: progresso
G: voz_arquetipo
H: voz_frase_essencia
I: posicionamento
J: territorio
K: num_editorias
L: num_ideias
M: num_conteudos
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st


# Mapeamento de colunas (1-indexed para gspread)
COLUMNS = {
    "timestamp_inicio": 1,
    "nome": 2,
    "email": 3,
    "instagram": 4,
    "ultima_atividade": 5,
    "progresso": 6,
    "voz_arquetipo": 7,
    "voz_frase_essencia": 8,
    "posicionamento": 9,
    "territorio": 10,
    "num_editorias": 11,
    "num_ideias": 12,
    "num_conteudos": 13,
}


def _get_credentials():
    """Carrega credenciais da Service Account do Google Cloud."""
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


def _find_row_by_email(ws, email: str) -> Optional[int]:
    """Retorna o número da linha do lead pelo email, ou None."""
    try:
        cell = ws.find(email, in_column=COLUMNS["email"])
        return cell.row if cell else None
    except Exception:
        return None


def register_lead(name: str, email: str, instagram: str = "") -> bool:
    """Registra um lead novo ou atualiza nome/@ se já existir."""
    ws = _get_worksheet()
    if not ws:
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        row = _find_row_by_email(ws, email)
        if row:
            # Já existe: atualiza última atividade
            ws.update_cell(row, COLUMNS["ultima_atividade"], now)
            return True

        # Novo: insere linha com 13 colunas (resto vazio)
        new_row = [""] * len(COLUMNS)
        new_row[COLUMNS["timestamp_inicio"] - 1] = now
        new_row[COLUMNS["nome"] - 1] = name
        new_row[COLUMNS["email"] - 1] = email
        new_row[COLUMNS["instagram"] - 1] = instagram
        new_row[COLUMNS["ultima_atividade"] - 1] = now
        new_row[COLUMNS["progresso"] - 1] = "0/6"

        ws.append_row(new_row, value_input_option="USER_ENTERED")
        return True
    except Exception:
        return False


def _update_cells(email: str, updates: dict) -> bool:
    """Atualiza múltiplas colunas de um lead pelo email.

    updates = {"voz_arquetipo": "Especialista", "progresso": "1/6"}
    Também atualiza ultima_atividade automaticamente.
    """
    ws = _get_worksheet()
    if not ws:
        return False

    try:
        row = _find_row_by_email(ws, email)
        if not row:
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates = {**updates, "ultima_atividade": now}

        # Monta batch update
        cells_to_update = []
        for col_name, value in updates.items():
            col_idx = COLUMNS.get(col_name)
            if col_idx:
                cells_to_update.append({
                    "range": f"{_col_letter(col_idx)}{row}",
                    "values": [[str(value)]],
                })

        if cells_to_update:
            ws.batch_update(cells_to_update, value_input_option="USER_ENTERED")
        return True
    except Exception:
        return False


def _col_letter(col_idx: int) -> str:
    """Converte índice de coluna (1-based) para letra (A, B, ... Z, AA, ...)."""
    result = ""
    while col_idx > 0:
        col_idx, rem = divmod(col_idx - 1, 26)
        result = chr(65 + rem) + result
    return result


# ─── Funções públicas por etapa ────────────────────────────────────────────

def update_progress(email: str, progress: str, voz_arquetipo: str = "") -> bool:
    """Update genérico (compatibilidade). Use as funções específicas abaixo."""
    updates = {"progresso": progress}
    if voz_arquetipo:
        updates["voz_arquetipo"] = voz_arquetipo
    return _update_cells(email, updates)


def track_voz(email: str, arquetipo: str, frase_essencia: str) -> bool:
    """Marca que o usuário completou Voz da Marca."""
    return _update_cells(email, {
        "voz_arquetipo": arquetipo,
        "voz_frase_essencia": frase_essencia,
        "progresso": "1/6",
    })


def track_posicionamento(email: str, frase: str) -> bool:
    """Marca que o usuário completou Posicionamento."""
    return _update_cells(email, {
        "posicionamento": frase,
        "progresso": "2/6",
    })


def track_territorio(email: str, territorio: str) -> bool:
    """Marca que o usuário completou Território."""
    return _update_cells(email, {
        "territorio": territorio,
        "progresso": "3/6",
    })


def track_editorias(email: str, count: int) -> bool:
    """Marca que o usuário criou editorias."""
    return _update_cells(email, {
        "num_editorias": count,
        "progresso": "4/6",
    })


def track_ideias(email: str, count: int) -> bool:
    """Marca quantas ideias foram geradas."""
    return _update_cells(email, {
        "num_ideias": count,
        "progresso": "5/6",
    })


def track_conteudos(email: str, count: int) -> bool:
    """Marca quantos conteúdos foram gerados no Monoflow."""
    return _update_cells(email, {
        "num_conteudos": count,
        "progresso": "6/6",
    })
