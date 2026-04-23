"""Gerador de Voz da Marca — descobre arquétipo primário e secundário."""

from __future__ import annotations

import json

import anthropic

import config


ARCHETYPES = {
    "especialista": {
        "name": "O Especialista",
        "subtitle": "Autoridade Intelectual",
        "description": "Profundidade, lógica e domínio técnico.",
        "energy": "Analítica, didática, orientada a resultado",
    },
    "protetor": {
        "name": "O Protetor",
        "subtitle": "Autoridade de Cuidado",
        "description": "Estrutura, segurança e empatia.",
        "energy": "Acolhedora, estruturada, orientada a cuidado",
    },
    "proximo": {
        "name": "O Próximo",
        "subtitle": "Autoridade de Conexão",
        "description": "Autenticidade, vulnerabilidade e presença humana.",
        "energy": "Humana, vulnerável, orientada a vínculo",
    },
    "desbravador": {
        "name": "O Desbravador",
        "subtitle": "Autoridade de Ruptura",
        "description": "Velocidade, coragem e impacto.",
        "energy": "Ousada, contrária, orientada a transformação",
    },
}


DISCOVERY_QUESTIONS = [
    {
        "key": "origem",
        "question": "O que te moveu a começar o que você faz hoje?",
        "help": "O motivo que colocou você nessa jornada.",
    },
    {
        "key": "virada",
        "question": "Qual foi o ponto de virada — quando algo te quebrou, te virou ou te fez mudar o jogo?",
        "help": "Um momento de ruptura ou insight que mudou seu caminho.",
    },
    {
        "key": "impacto",
        "question": "O que está em jogo hoje — o que você quer que o mundo sinta quando te ouve ou te vê?",
        "help": "A marca que você quer deixar nas pessoas.",
    },
    {
        "key": "motivo_agora",
        "question": "Por que você quer começar (ou fortalecer) a criação de conteúdo agora?",
        "help": "O que te trouxe aqui neste momento específico.",
    },
    {
        "key": "pessoa_ou_marca",
        "question": "Você fala mais como marca (empresa) ou como pessoa (profissional)?",
        "help": "Ajuda a calibrar o nível de informalidade e exposição pessoal.",
    },
    {
        "key": "referencia",
        "question": "Se pudesse escolher um personagem fictício ou pessoa pública com quem mais se identifica no estilo ou energia, quem seria?",
        "help": "Uma referência de voz e presença que ressoa com você.",
    },
]


SYSTEM_PROMPT = """Você é um especialista em branding pessoal e análise de arquétipos de marca.

Sua tarefa é analisar as respostas do usuário e identificar seu ARQUÉTIPO PRIMÁRIO e SECUNDÁRIO entre os 4 arquétipos do sistema (não use outros arquétipos fora dessa lista).

OS 4 ARQUÉTIPOS:

1. ESPECIALISTA (Autoridade Intelectual)
   - Profundidade, lógica e domínio técnico
   - Energia: analítica, didática, orientada a resultado
   - Palavras-chave: método, estratégia, padrão, leitura, execução, diagnóstico
   - Quando predomina: pessoas que valorizam construção com propósito, análise fria da realidade, ensinar com profundidade

2. PROTETOR (Autoridade de Cuidado)
   - Estrutura, segurança e empatia
   - Energia: acolhedora, estruturada, orientada a cuidado
   - Palavras-chave: segurança, guia, estrutura, apoio, caminho, cuidado
   - Quando predomina: pessoas que priorizam proteger, orientar, criar ambientes seguros

3. PRÓXIMO (Autoridade de Conexão)
   - Autenticidade, vulnerabilidade e presença humana
   - Energia: humana, vulnerável, orientada a vínculo
   - Palavras-chave: verdade, humano, real, juntos, história, conexão
   - Quando predomina: pessoas que conectam pela honestidade, expõem vulnerabilidade, criam comunidade

4. DESBRAVADOR (Autoridade de Ruptura)
   - Velocidade, coragem e impacto
   - Energia: ousada, contrária, orientada a transformação
   - Palavras-chave: ruptura, coragem, quebrar, impacto, contrário, desbravar
   - Quando predomina: pessoas que questionam o status quo, pioneiros, disruptores

RESPONDA EXCLUSIVAMENTE com JSON no formato:
{
  "arquetipo_primario": "especialista|protetor|proximo|desbravador",
  "arquetipo_secundario": "especialista|protetor|proximo|desbravador",
  "justificativa": "2-3 frases explicando por que esses arquétipos emergem das respostas",
  "mapa_voz": {
    "energia_arquetipica": "1 frase descrevendo a energia combinada dos dois arquétipos",
    "tom_de_voz": "3-5 adjetivos separados por vírgula que descrevem o tom",
    "frase_essencia": "1 frase curta e poderosa, estilo manifesto pessoal, na voz do usuário (em 1ª pessoa)",
    "frase_impacto": "1 frase que o usuário poderia dizer publicamente como bandeira, direta e memorável",
    "palavras_usar": ["palavra1", "palavra2", "palavra3", "palavra4", "palavra5"],
    "palavras_evitar": ["palavra1", "palavra2", "palavra3"]
  }
}"""


def _call_claude(system: str, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
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


def descobrir_voz(answers: dict) -> dict:
    """Analisa respostas e retorna arquétipo primário/secundário + mapa de voz.

    answers = {"origem": "...", "virada": "...", ...}
    """
    formatted = "\n\n".join(
        f"**{q['question']}**\n{answers.get(q['key'], '').strip() or '(não respondeu)'}"
        for q in DISCOVERY_QUESTIONS
    )

    user_msg = f"Analise as respostas abaixo e identifique o arquétipo primário e secundário:\n\n{formatted}"
    result = _call_claude(SYSTEM_PROMPT, user_msg)
    return _parse_json(result)
