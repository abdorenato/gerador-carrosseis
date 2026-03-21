from __future__ import annotations

import json
from dataclasses import dataclass

import anthropic

import config
from db.models import ICP, SlideContent, Offer


@dataclass
class CarouselCopy:
    slides: list[SlideContent]
    caption: str
    hashtags: list[str]


SYSTEM_PROMPT_IDEAS = """Você é um estrategista de conteúdo para Instagram especializado em carrosséis virais.

Seu objetivo é gerar ideias de carrosséis que maximizem engajamento (saves, shares, comentários).

REGRAS:
- Cada ideia deve ter um gancho forte (hook) que gere curiosidade ou urgência
- Os temas devem resolver dores reais do público-alvo
- Use ângulos contraintuitivos, polêmicos ou surpreendentes quando possível
- Considere os padrões de performance dos posts anteriores (se fornecidos)
- Responda SEMPRE em JSON válido

PERFIL DO PÚBLICO (ICP):
{icp_context}

{analytics_context}

Gere {count} ideias de carrosséis. Responda EXCLUSIVAMENTE com JSON no formato:
{{
  "ideas": [
    {{
      "topic": "tema do carrossel",
      "hook": "frase de gancho para o primeiro slide",
      "angle": "ângulo ou abordagem do conteúdo",
      "target_emotion": "emoção principal que queremos provocar",
      "carousel_style": "educational|storytelling|listicle|myth_busting|before_after"
    }}
  ]
}}"""

SYSTEM_PROMPT_COPYWRITER = """Você é um copywriter especialista em carrosséis virais para Instagram.

REGRAS DE CARROSSEL VIRAL:
1. SLIDE 1 (hook): Gancho irresistível. Frase curta, bold, que gera curiosidade. Nunca revele a resposta no hook.
2. SLIDES DO MEIO (content): Um conceito por slide. Frases curtas e diretas. Use contraste, números e exemplos concretos.
3. ÚLTIMO SLIDE (cta): Call-to-action claro. Peça save, compartilhamento ou comentário. Gere senso de comunidade.

DIRETRIZES DE COPY:
- Máximo 40 palavras por slide (headlines curtos, corpo conciso)
- Headlines de 3-7 palavras com impacto
- Use linguagem do público-alvo
- Evite jargões desnecessários
- Cada slide deve fazer sentido sozinho mas criar curiosidade para o próximo

PERFIL DO PÚBLICO (ICP):
{icp_context}

Escreva o copy de um carrossel com {num_slides} slides sobre:
Tema: {topic}
Hook: {hook}
Estilo: {style}

Responda EXCLUSIVAMENTE com JSON no formato:
{{
  "slides": [
    {{
      "index": 0,
      "slide_type": "hook|content|listicle|quote|cta",
      "headline": "título do slide",
      "body": "corpo do slide (pode ser vazio no hook)"
    }}
  ],
  "caption": "legenda do post com quebras de linha, CTA e emojis moderados",
  "hashtags": ["hashtag1", "hashtag2"]
}}"""

SYSTEM_PROMPT_REFINE = """Você é um copywriter especialista em carrosséis virais para Instagram.

O usuário quer refinar um slide específico de um carrossel. Mantenha a consistência com o tom e tema geral.

Slide atual:
Tipo: {slide_type}
Headline: {headline}
Body: {body}

Instrução do usuário: {instruction}

Responda EXCLUSIVAMENTE com JSON no formato:
{{
  "headline": "novo título",
  "body": "novo corpo"
}}"""


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


def _format_analytics_context(patterns: dict | None) -> str:
    if not patterns:
        return ""
    lines = ["PADRÕES DE PERFORMANCE DOS POSTS ANTERIORES:"]
    if patterns.get("avg_caption_length"):
        lines.append(f"- Tamanho médio de legenda: {patterns['avg_caption_length']} caracteres")
    if patterns.get("common_hooks"):
        lines.append(f"- Hooks comuns nos top posts: {', '.join(patterns['common_hooks'][:5])}")
    if patterns.get("top_hashtags"):
        lines.append(f"- Hashtags mais usadas: {', '.join(patterns['top_hashtags'][:10])}")
    if patterns.get("avg_slides_count"):
        lines.append(f"- Número médio de slides: {patterns['avg_slides_count']}")
    if patterns.get("best_posting_times"):
        lines.append(f"- Melhores horários: {', '.join(patterns['best_posting_times'])}")
    return "\n".join(lines)


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
    """Extrai JSON da resposta, mesmo se vier com markdown."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove primeira e última linha (```json e ```)
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


def _format_offer_context(offer: Offer) -> str:
    return (
        "OFERTA ATIVA:\n"
        f"Nome: {offer.name}\n"
        f"Sonho do cliente: {offer.dream}\n"
        f"Provas de sucesso: {', '.join(offer.success_proofs)}\n"
        f"Tempo para resultado: {offer.time_to_result}\n"
        f"Esforço necessário: {offer.effort_level}\n"
    )


def generate_full_offer(
    icp: ICP,
    product: str,
    differentiator: str,
    price_range: str,
) -> dict:
    """Gera uma oferta completa baseada no ICP e inputs do usuário."""
    system = (
        "Você é um estrategista de marketing especialista em construção de ofertas irresistíveis.\n\n"
        "Use a equação de valor: Valor = (Sonho × Probabilidade de Sucesso) ÷ (Tempo × Esforço)\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        f"PRODUTO/SERVIÇO: {product}\n"
        f"DIFERENCIAL: {differentiator}\n"
        f"FAIXA DE PREÇO: {price_range}\n\n"
        "Com base no perfil do público e no produto, gere uma oferta irresistível completa.\n"
        "Pense nas dores, desejos e objeções do ICP para construir cada componente.\n\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        "{\n"
        '  "name": "Nome da oferta (curto e impactante)",\n'
        '  "dream": "O resultado que o cliente deseja alcançar",\n'
        '  "success_proofs": ["prova 1", "prova 2", "prova 3"],\n'
        '  "time_to_result": "Em quanto tempo o cliente vê resultado",\n'
        '  "effort_level": "O que o cliente NÃO precisa fazer (minimizar sacrifício)",\n'
        '  "core_promise": "Promessa principal da oferta em uma frase",\n'
        '  "bonuses": ["bônus 1 que ataca objeção X", "bônus 2 que ataca objeção Y"],\n'
        '  "scarcity": "Elemento de escassez ou urgência",\n'
        '  "guarantee": "Garantia que reverte o risco do cliente",\n'
        '  "method_name": "Nome exclusivo do método/sistema"\n'
        "}"
    )

    result = _call_claude(
        system,
        f"Crie uma oferta irresistível para: {product}. Diferencial: {differentiator}. Preço: {price_range}.",
    )
    return _parse_json(result)


def suggest_offer_component(
    icp: ICP,
    component: str,
    current_value: str = "",
) -> list[str]:
    """Sugere preenchimento para um componente da oferta baseado no ICP."""
    component_labels = {
        "dream": "Sonho / Resultado desejado do cliente",
        "success_proofs": "Provas de sucesso, garantias e autoridade",
        "time_to_result": "Tempo para o cliente perceber resultado",
        "effort_level": "Esforço e sacrifício necessários (quanto MENOS melhor)",
        "core_promise": "Core Promise / Promessa principal da oferta",
        "bonuses": "Bônus que atacam objeções e medos do cliente",
        "scarcity": "Escassez e urgência para acelerar a decisão",
        "guarantee": "Garantia que reverte o risco do cliente",
        "method_name": "Nome exclusivo e memorável para o método/sistema",
    }

    label = component_labels.get(component, component)

    system = (
        "Você é um estrategista de marketing especialista em construção de ofertas irresistíveis.\n\n"
        "Use a equação de valor: Valor = (Sonho × Probabilidade de Sucesso) ÷ (Tempo × Esforço)\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        f"O usuário precisa de sugestões para o componente: {label}\n"
        f"{'Valor atual: ' + current_value if current_value else ''}\n\n"
        "Gere 3 sugestões práticas e específicas para este componente.\n"
        "Responda EXCLUSIVAMENTE com JSON no formato:\n"
        '{"suggestions": ["sugestão 1", "sugestão 2", "sugestão 3"]}'
    )

    result = _call_claude(system, f"Sugira 3 opções para: {label}")
    data = _parse_json(result)
    return data.get("suggestions", [])


def generate_offer_summary(icp: ICP, offer: Offer) -> str:
    """Gera um resumo estruturado da oferta irresistível."""
    system = (
        "Você é um especialista em construção de ofertas irresistíveis.\n\n"
        "Baseado na equação de valor:\n"
        "Valor = (Sonho × Probabilidade de Sucesso) ÷ (Tempo × Esforço & Sacrifício)\n\n"
        f"PERFIL DO PÚBLICO (ICP):\n{_format_icp_context(icp)}\n\n"
        f"OFERTA:\n"
        f"Nome: {offer.name}\n"
        f"Sonho: {offer.dream}\n"
        f"Provas de sucesso: {', '.join(offer.success_proofs)}\n"
        f"Tempo para resultado: {offer.time_to_result}\n"
        f"Esforço necessário: {offer.effort_level}\n\n"
        "Gere um resumo estruturado da oferta com:\n"
        "1. Posicionamento da oferta (1 frase poderosa)\n"
        "2. Promessa principal\n"
        "3. Pontos de prova (bullets)\n"
        "4. Redutores de risco (o que facilita para o cliente)\n"
        "5. Sugestão de headline para usar em conteúdo\n\n"
        "Responda em markdown formatado, SEM JSON."
    )

    return _call_claude(system, "Gere o resumo estruturado desta oferta.")


def generate_ideas(
    icp: ICP,
    patterns: dict | None = None,
    count: int = 5,
    offer: Offer | None = None,
) -> list[dict]:
    """Gera ideias de carrosséis baseadas no ICP e padrões de analytics."""
    icp_context = _format_icp_context(icp)
    analytics_context = _format_analytics_context(patterns)
    offer_context = _format_offer_context(offer) if offer else ""

    system = SYSTEM_PROMPT_IDEAS.format(
        icp_context=icp_context,
        analytics_context=analytics_context,
        count=count,
    )

    if offer_context:
        system += f"\n\n{offer_context}\nUse a oferta ativa como base para gerar ideias de carrosséis que promovam esta oferta."

    result = _call_claude(system, f"Gere {count} ideias de carrosséis para o nicho: {icp.niche}")
    data = _parse_json(result)
    return data.get("ideas", [])


def write_carousel_copy(
    icp: ICP,
    topic: str,
    hook: str,
    num_slides: int = 7,
    style: str = "educational",
) -> CarouselCopy:
    """Escreve o copy completo de um carrossel."""
    icp_context = _format_icp_context(icp)

    system = SYSTEM_PROMPT_COPYWRITER.format(
        icp_context=icp_context,
        num_slides=num_slides,
        topic=topic,
        hook=hook,
        style=style,
    )

    result = _call_claude(
        system,
        f"Escreva o copy do carrossel com {num_slides} slides. Tema: {topic}. Hook: {hook}. Estilo: {style}.",
    )
    data = _parse_json(result)

    slides = [
        SlideContent(
            index=s["index"],
            slide_type=s["slide_type"],
            headline=s["headline"],
            body=s.get("body", ""),
        )
        for s in data.get("slides", [])
    ]

    return CarouselCopy(
        slides=slides,
        caption=data.get("caption", ""),
        hashtags=data.get("hashtags", []),
    )


def refine_slide(slide: SlideContent, instruction: str) -> SlideContent:
    """Refina um slide individual com base em instrução do usuário."""
    system = SYSTEM_PROMPT_REFINE.format(
        slide_type=slide.slide_type,
        headline=slide.headline,
        body=slide.body,
        instruction=instruction,
    )

    result = _call_claude(system, instruction)
    data = _parse_json(result)

    return SlideContent(
        index=slide.index,
        slide_type=slide.slide_type,
        headline=data.get("headline", slide.headline),
        body=data.get("body", slide.body),
        image_path=slide.image_path,
    )


def generate_caption(slides: list[SlideContent], icp: ICP) -> str:
    """Gera uma legenda otimizada para o carrossel."""
    slides_summary = "\n".join(
        f"Slide {s.index + 1} ({s.slide_type}): {s.headline}" for s in slides
    )
    icp_context = _format_icp_context(icp)

    system = (
        "Você é um copywriter de Instagram. Gere uma legenda otimizada para um carrossel.\n\n"
        f"PERFIL DO PÚBLICO:\n{icp_context}\n\n"
        "REGRAS:\n"
        "- Primeira linha: hook que complementa o carrossel\n"
        "- Use quebras de linha para legibilidade\n"
        "- Inclua CTA (salvar, compartilhar, comentar)\n"
        "- Máximo 2200 caracteres\n"
        "- Emojis moderados\n"
        "- Responda APENAS com o texto da legenda, sem JSON"
    )

    return _call_claude(system, f"Slides do carrossel:\n{slides_summary}")
