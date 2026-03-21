from __future__ import annotations

import json

import anthropic

import config
from db.models import ICP, Offer


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)


def _format_icp_context(icp: ICP) -> str:
    return (
        f"Nome: {icp.name}\n"
        f"Nicho: {icp.niche}\n"
        f"Demografia: {icp.demographics}\n"
        f"Dores: {', '.join(icp.pain_points)}\n"
        f"Desejos: {', '.join(icp.desires)}\n"
        f"Objeções: {', '.join(icp.objections)}\n"
        f"Estilo de linguagem: {icp.language_style}\n"
        f"Tom: {', '.join(icp.tone_keywords)}"
    )


def _call_claude(system: str, user_message: str) -> str:
    client = _get_client()
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines = []
        inside = False
        for line in lines:
            if line.strip().startswith("```") and not inside:
                inside = True
                continue
            if line.strip() == "```" and inside:
                break
            if inside:
                json_lines.append(line)
        text = "\n".join(json_lines)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Texto-mãe
# ---------------------------------------------------------------------------

def generate_mother_text(
    icp: ICP,
    idea: dict,
    offer: Offer | None = None,
) -> str:
    """Gera texto-mãe completo a partir da ideia + ICP + oferta."""
    offer_block = ""
    if offer:
        offer_block = (
            f"\n\nOFERTA ATIVA:\n"
            f"Nome: {offer.name}\n"
            f"Core Promise: {offer.core_promise}\n"
            f"Sonho: {offer.dream}\n"
            f"Garantia: {offer.guarantee}\n"
            f"Nome do método: {offer.method_name}\n"
        )

    system = (
        "Você é um estrategista de conteúdo sênior. Sua tarefa é criar um TEXTO-MÃE: "
        "um texto completo e rico sobre um tema, que servirá de base para ser desdobrado "
        "em múltiplos formatos de conteúdo (reels, posts, carrosséis, stories, LinkedIn, TikTok).\n\n"
        "O texto-mãe deve:\n"
        "- Ter entre 500-800 palavras\n"
        "- Conter uma narrativa completa com início, meio e fim\n"
        "- Incluir dados, exemplos concretos e analogias\n"
        "- Ter frases de impacto que podem virar headlines\n"
        "- Usar a linguagem e tom do público-alvo\n"
        "- Ter uma tese clara e um ponto de vista forte\n"
        "- Incluir pelo menos 1 história/exemplo real ou hipotético\n"
        "- Terminar com uma reflexão ou CTA\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n"
        f"{offer_block}\n\n"
        "Responda APENAS com o texto-mãe, sem JSON, sem formatação markdown."
    )

    topic = idea.get("topic", "")
    hook = idea.get("hook", "")
    angle = idea.get("angle", "")
    emotion = idea.get("target_emotion", "")

    user_msg = (
        f"Crie um texto-mãe sobre:\n"
        f"Tema: {topic}\n"
        f"Hook: {hook}\n"
        f"Ângulo: {angle}\n"
        f"Emoção alvo: {emotion}"
    )

    return _call_claude(system, user_msg)


# ---------------------------------------------------------------------------
# Instagram Reels
# ---------------------------------------------------------------------------

def generate_instagram_reels(icp: ICP, mother_text: str) -> dict:
    """Gera roteiro de Reels a partir do texto-mãe."""
    system = (
        "Você é um roteirista de Reels virais para Instagram.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        "TEXTO-MÃE (base para o roteiro):\n"
        f"{mother_text}\n\n"
        "Crie um roteiro de Reels viral baseado nesse texto-mãe.\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "title": "Título interno do Reels",\n'
        '  "duration": "30s | 60s | 90s",\n'
        '  "hook": "Frase de abertura (primeiros 3 segundos, CRUCIAL)",\n'
        '  "scenes": [\n'
        '    {"time": "0-3s", "action": "o que fazer/falar", "text_overlay": "texto na tela"},\n'
        '    {"time": "3-10s", "action": "...", "text_overlay": "..."}\n'
        "  ],\n"
        '  "cta": "Call-to-action final",\n'
        '  "caption": "Legenda do Reels com emojis e hashtags",\n'
        '  "audio_suggestion": "Tipo de áudio/música sugerido",\n'
        '  "trend_tip": "Dica de trend que pode ser usada"\n'
        "}"
    )

    result = _call_claude(system, "Crie o roteiro do Reels.")
    return _parse_json(result)


# ---------------------------------------------------------------------------
# Instagram Post
# ---------------------------------------------------------------------------

def generate_instagram_post(icp: ICP, mother_text: str) -> dict:
    """Gera post de Instagram (legenda) a partir do texto-mãe."""
    system = (
        "Você é um copywriter de Instagram especialista em posts que geram engajamento.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        "TEXTO-MÃE (base para o post):\n"
        f"{mother_text}\n\n"
        "Crie uma legenda de post para Instagram (feed) baseada nesse texto-mãe.\n\n"
        "REGRAS:\n"
        "- Primeira linha: hook irresistível (aparece no preview)\n"
        "- Máximo 2200 caracteres\n"
        "- Use quebras de linha para legibilidade\n"
        "- Inclua CTA (salvar, compartilhar, comentar)\n"
        "- Emojis moderados\n"
        "- Separe hashtags no final\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "caption": "Legenda completa do post",\n'
        '  "hashtags": ["hashtag1", "hashtag2"],\n'
        '  "best_time": "Melhor horário sugerido para postar",\n'
        '  "image_suggestion": "Descrição da imagem ideal para acompanhar",\n'
        '  "image_keywords": ["keyword1 em inglês", "keyword2 em inglês"],\n'
        '  "headline_on_image": "Frase curta e impactante para sobrepor na imagem (máx 8 palavras)"\n'
        "}"
    )

    result = _call_claude(system, "Crie o post para Instagram.")
    return _parse_json(result)


# ---------------------------------------------------------------------------
# Instagram Carrossel
# ---------------------------------------------------------------------------

def generate_instagram_carousel(
    icp: ICP, mother_text: str, num_slides: int = 7
) -> dict:
    """Gera carrossel de Instagram a partir do texto-mãe."""
    system = (
        "Você é um copywriter especialista em carrosséis virais para Instagram.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        "TEXTO-MÃE (base para o carrossel):\n"
        f"{mother_text}\n\n"
        f"Crie um carrossel de {num_slides} slides baseado nesse texto-mãe.\n\n"
        "REGRAS:\n"
        "- Slide 1: Hook irresistível (nunca revele a resposta)\n"
        "- Slides do meio: Um conceito por slide, frases curtas\n"
        "- Último slide: CTA claro\n"
        "- Máximo 40 palavras por slide\n"
        "- Headlines de 3-7 palavras\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "slides": [\n'
        '    {"index": 0, "slide_type": "hook|content|listicle|quote|cta", "headline": "...", "body": "..."}\n'
        "  ],\n"
        '  "caption": "Legenda do carrossel",\n'
        '  "hashtags": ["hashtag1", "hashtag2"],\n'
        '  "image_keywords": ["keyword1 em inglês para buscar foto de fundo", "keyword2"]\n'
        "}"
    )

    result = _call_claude(system, f"Crie o carrossel com {num_slides} slides.")
    return _parse_json(result)


# ---------------------------------------------------------------------------
# Instagram Stories
# ---------------------------------------------------------------------------

def generate_instagram_stories(icp: ICP, mother_text: str) -> dict:
    """Gera sequência de Stories com perguntas ou enquetes."""
    system = (
        "Você é um estrategista de Instagram Stories que maximiza engajamento.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        "TEXTO-MÃE (base para os stories):\n"
        f"{mother_text}\n\n"
        "Crie uma sequência de 3-5 Stories interativos baseados nesse texto-mãe.\n"
        "Use stickers de interação (enquete, pergunta, quiz, slider).\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "stories": [\n'
        "    {\n"
        '      "order": 1,\n'
        '      "type": "text | poll | question | quiz | slider",\n'
        '      "text": "Texto principal do story",\n'
        '      "sticker": {\n'
        '        "type": "poll | question | quiz | slider",\n'
        '        "question": "Pergunta do sticker",\n'
        '        "options": ["Opção A", "Opção B"]\n'
        "      },\n"
        '      "visual_tip": "Dica visual (cor de fundo, foto sugerida)"\n'
        "    }\n"
        "  ],\n"
        '  "strategy": "Estratégia por trás da sequência"\n'
        "}"
    )

    result = _call_claude(system, "Crie a sequência de Stories.")
    return _parse_json(result)


# ---------------------------------------------------------------------------
# LinkedIn Post
# ---------------------------------------------------------------------------

def generate_linkedin_post(icp: ICP, mother_text: str) -> dict:
    """Gera post para LinkedIn a partir do texto-mãe."""
    system = (
        "Você é um ghostwriter de LinkedIn especialista em posts que viralizam.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        "TEXTO-MÃE (base para o post):\n"
        f"{mother_text}\n\n"
        "Crie um post para LinkedIn baseado nesse texto-mãe.\n\n"
        "REGRAS DE LINKEDIN:\n"
        "- Primeira linha: hook forte (aparece antes do 'ver mais')\n"
        "- Tom profissional mas humano (storytelling)\n"
        "- Use quebras de linha curtas (1-2 frases por parágrafo)\n"
        "- Máximo 3 hashtags no final\n"
        "- Sem emojis excessivos (máximo 3-4 no post inteiro)\n"
        "- Inclua uma lição ou insight acionável\n"
        "- Termine com pergunta para gerar comentários\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "post": "Texto completo do post LinkedIn",\n'
        '  "hashtags": ["hashtag1", "hashtag2", "hashtag3"]\n'
        "}"
    )

    result = _call_claude(system, "Crie o post para LinkedIn.")
    return _parse_json(result)


# ---------------------------------------------------------------------------
# TikTok
# ---------------------------------------------------------------------------

def generate_tiktok_video(icp: ICP, reels_content: dict) -> dict:
    """Adapta roteiro do Reels para formato TikTok."""
    system = (
        "Você é um criador de conteúdo viral no TikTok.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        "ROTEIRO ORIGINAL (Reels Instagram):\n"
        f"{json.dumps(reels_content, ensure_ascii=False, indent=2)}\n\n"
        "Adapte este roteiro para o formato TikTok.\n\n"
        "DIFERENÇAS TIKTOK vs REELS:\n"
        "- TikTok é mais informal e autêntico\n"
        "- Trends e sons do momento são essenciais\n"
        "- Hook nos primeiros 1-2 segundos (mais rápido que Reels)\n"
        "- Textos na tela mais diretos\n"
        "- CTA focado em seguir e compartilhar\n"
        "- Duração ideal: 15-30s para viralizar\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "title": "Título do TikTok",\n'
        '  "duration": "15s | 30s | 60s",\n'
        '  "hook": "Hook adaptado (1-2 segundos)",\n'
        '  "scenes": [\n'
        '    {"time": "0-2s", "action": "...", "text_overlay": "..."}\n'
        "  ],\n"
        '  "cta": "CTA adaptado",\n'
        '  "caption": "Legenda TikTok com hashtags",\n'
        '  "sound_suggestion": "Som/trend sugerido",\n'
        '  "tiktok_tips": "Dicas específicas para TikTok"\n'
        "}"
    )

    result = _call_claude(system, "Adapte para TikTok.")
    return _parse_json(result)


# ---------------------------------------------------------------------------
# Refinamento genérico
# ---------------------------------------------------------------------------

def refine_content(
    icp: ICP,
    platform: str,
    current_content: str,
    instruction: str,
) -> str:
    """Refina conteúdo de qualquer plataforma com instrução do usuário."""
    system = (
        f"Você é um especialista em conteúdo para {platform}.\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        f"CONTEÚDO ATUAL:\n{current_content}\n\n"
        f"INSTRUÇÃO DO USUÁRIO: {instruction}\n\n"
        "Refine o conteúdo conforme a instrução. Mantenha o formato original.\n"
        "Responda APENAS com o conteúdo refinado no mesmo formato JSON original."
    )

    return _call_claude(system, f"Refine: {instruction}")
