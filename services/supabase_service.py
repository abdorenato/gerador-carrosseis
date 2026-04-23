"""Serviço de persistência no Supabase.

Substitui sheets_service.py. Armazena leads e todo o conteúdo do flow
(voz, posicionamento, território, editorias, ideias, conteúdos).

Tabelas esperadas (criadas via SQL no Supabase):
- users (id, email, name, instagram, created_at, ultima_atividade)
- vozes (user_id, arquetipo_primario, arquetipo_secundario, justificativa, mapa_voz, respostas)
- posicionamentos (user_id, frase)
- territorios (user_id, nome, descricao)
- editorias (id, user_id, nome, descricao, ordem)
- ideias (id, user_id, editoria_id, topic, hook, angle, carousel_style)
- conteudos (id, user_id, ideia_id, platform, data)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import streamlit as st


_CLIENT = None


def _get_client():
    """Retorna cliente Supabase (singleton) ou None se não configurado."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    try:
        from supabase import create_client
    except ImportError:
        return None

    url = st.secrets.get("SUPABASE_URL") or ""
    key = st.secrets.get("SUPABASE_KEY") or ""

    if not url or not key:
        return None

    try:
        _CLIENT = create_client(url, key)
        return _CLIENT
    except Exception:
        return None


def is_configured() -> bool:
    """Verifica se o Supabase está configurado."""
    return _get_client() is not None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── USERS ─────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    """Retorna o registro do usuário pelo email."""
    client = _get_client()
    if not client:
        return None
    try:
        resp = client.table("users").select("*").eq("email", email).limit(1).execute()
        if resp.data:
            return resp.data[0]
        return None
    except Exception:
        return None


def register_lead(name: str, email: str, instagram: str = "") -> Optional[dict]:
    """Registra um lead novo ou atualiza se já existir.

    Retorna o dict do usuário (com id) ou None se falhou.
    """
    client = _get_client()
    if not client:
        return None

    email = email.lower().strip()

    try:
        existing = get_user_by_email(email)
        if existing:
            # Atualiza nome/instagram/ultima_atividade
            client.table("users").update({
                "name": name,
                "instagram": instagram,
                "ultima_atividade": _now(),
            }).eq("id", existing["id"]).execute()
            return {**existing, "name": name, "instagram": instagram}

        # Insere novo
        resp = client.table("users").insert({
            "email": email,
            "name": name,
            "instagram": instagram,
        }).execute()

        if resp.data:
            return resp.data[0]
        return None
    except Exception:
        return None


def _touch_activity(user_id: str):
    """Atualiza ultima_atividade do usuário."""
    client = _get_client()
    if not client:
        return
    try:
        client.table("users").update({"ultima_atividade": _now()}).eq("id", user_id).execute()
    except Exception:
        pass


# ─── VOZ DA MARCA ──────────────────────────────────────────────────────────

def save_voz(user_id: str, data: dict) -> bool:
    """Salva ou atualiza a Voz da Marca do usuário.

    data = {
        "arquetipo_primario": "especialista",
        "arquetipo_secundario": "protetor",
        "justificativa": "...",
        "mapa_voz": {...},
        "respostas": {...}
    }
    """
    client = _get_client()
    if not client:
        return False

    try:
        payload = {
            "user_id": user_id,
            "arquetipo_primario": data.get("arquetipo_primario"),
            "arquetipo_secundario": data.get("arquetipo_secundario"),
            "justificativa": data.get("justificativa"),
            "mapa_voz": data.get("mapa_voz", {}),
            "respostas": data.get("respostas", {}),
            "updated_at": _now(),
        }
        # Upsert (insert ou update se já existe)
        client.table("vozes").upsert(payload, on_conflict="user_id").execute()
        _touch_activity(user_id)
        return True
    except Exception:
        return False


def get_voz(user_id: str) -> Optional[dict]:
    client = _get_client()
    if not client:
        return None
    try:
        resp = client.table("vozes").select("*").eq("user_id", user_id).limit(1).execute()
        if resp.data:
            return resp.data[0]
        return None
    except Exception:
        return None


# ─── POSICIONAMENTO ────────────────────────────────────────────────────────

def save_posicionamento(user_id: str, frase: str) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        client.table("posicionamentos").upsert({
            "user_id": user_id,
            "frase": frase,
            "updated_at": _now(),
        }, on_conflict="user_id").execute()
        _touch_activity(user_id)
        return True
    except Exception:
        return False


def get_posicionamento(user_id: str) -> Optional[str]:
    client = _get_client()
    if not client:
        return None
    try:
        resp = client.table("posicionamentos").select("frase").eq("user_id", user_id).limit(1).execute()
        if resp.data:
            return resp.data[0]["frase"]
        return None
    except Exception:
        return None


# ─── TERRITÓRIO ────────────────────────────────────────────────────────────

def save_territorio(user_id: str, nome: str, descricao: str = "") -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        client.table("territorios").upsert({
            "user_id": user_id,
            "nome": nome,
            "descricao": descricao,
            "updated_at": _now(),
        }, on_conflict="user_id").execute()
        _touch_activity(user_id)
        return True
    except Exception:
        return False


def get_territorio(user_id: str) -> Optional[dict]:
    client = _get_client()
    if not client:
        return None
    try:
        resp = client.table("territorios").select("*").eq("user_id", user_id).limit(1).execute()
        if resp.data:
            return resp.data[0]
        return None
    except Exception:
        return None


# ─── EDITORIAS ─────────────────────────────────────────────────────────────

def save_editorias(user_id: str, editorias: list[dict]) -> bool:
    """Substitui todas as editorias do usuário (delete + insert).

    editorias = [{"nome": "...", "descricao": "...", "ordem": 0}, ...]
    """
    client = _get_client()
    if not client:
        return False
    try:
        # Apaga as existentes
        client.table("editorias").delete().eq("user_id", user_id).execute()
        # Insere as novas
        if editorias:
            payload = [
                {
                    "user_id": user_id,
                    "nome": e.get("nome", ""),
                    "descricao": e.get("descricao", ""),
                    "ordem": e.get("ordem", i),
                }
                for i, e in enumerate(editorias)
            ]
            client.table("editorias").insert(payload).execute()
        _touch_activity(user_id)
        return True
    except Exception:
        return False


def get_editorias(user_id: str) -> list[dict]:
    client = _get_client()
    if not client:
        return []
    try:
        resp = (
            client.table("editorias")
            .select("*")
            .eq("user_id", user_id)
            .order("ordem")
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


# ─── IDEIAS ────────────────────────────────────────────────────────────────

def save_ideia(user_id: str, editoria_id: Optional[str], idea_data: dict) -> Optional[dict]:
    client = _get_client()
    if not client:
        return None
    try:
        resp = client.table("ideias").insert({
            "user_id": user_id,
            "editoria_id": editoria_id,
            "topic": idea_data.get("topic"),
            "hook": idea_data.get("hook"),
            "angle": idea_data.get("angle"),
            "carousel_style": idea_data.get("carousel_style"),
        }).execute()
        _touch_activity(user_id)
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def get_ideias(user_id: str, editoria_id: Optional[str] = None) -> list[dict]:
    client = _get_client()
    if not client:
        return []
    try:
        query = client.table("ideias").select("*").eq("user_id", user_id)
        if editoria_id:
            query = query.eq("editoria_id", editoria_id)
        resp = query.order("created_at", desc=True).execute()
        return resp.data or []
    except Exception:
        return []


# ─── CONTEÚDOS ─────────────────────────────────────────────────────────────

def save_conteudo(
    user_id: str, platform: str, data: dict, ideia_id: Optional[str] = None
) -> Optional[dict]:
    client = _get_client()
    if not client:
        return None
    try:
        resp = client.table("conteudos").insert({
            "user_id": user_id,
            "ideia_id": ideia_id,
            "platform": platform,
            "data": data,
        }).execute()
        _touch_activity(user_id)
        return resp.data[0] if resp.data else None
    except Exception:
        return None


def count_conteudos(user_id: str) -> int:
    client = _get_client()
    if not client:
        return 0
    try:
        resp = client.table("conteudos").select("id", count="exact").eq("user_id", user_id).execute()
        return resp.count or 0
    except Exception:
        return 0


# ─── DASHBOARD / ADMIN ─────────────────────────────────────────────────────

def list_all_users() -> list[dict]:
    """Lista todos os usuários para a view de admin."""
    client = _get_client()
    if not client:
        return []
    try:
        resp = client.table("users").select("*").order("created_at", desc=True).execute()
        return resp.data or []
    except Exception:
        return []


def get_full_progress(user_id: str) -> dict:
    """Retorna o progresso completo do usuário para o dashboard."""
    return {
        "voz": get_voz(user_id) is not None,
        "posicionamento": get_posicionamento(user_id) is not None,
        "territorio": get_territorio(user_id) is not None,
        "editorias": len(get_editorias(user_id)) > 0,
        "ideias": len(get_ideias(user_id)) > 0,
        "conteudos": count_conteudos(user_id) > 0,
    }
