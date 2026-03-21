from __future__ import annotations

import base64
import textwrap
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

import config
from db.models import SlideContent

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# ── Paletas de estilo ─────────────────────────────────────────────────────

STYLE_PALETTES = {
    "dark_bold": {
        "bg": (10, 10, 10),
        "text": (255, 255, 255),
        "accent": (255, 215, 0),
        "box_bg": (10, 10, 10, 200),
        "box_text": (255, 255, 255),
    },
    "light_minimal": {
        "bg": (250, 250, 248),
        "text": (30, 30, 30),
        "accent": (100, 100, 100),
        "box_bg": (250, 250, 248, 220),
        "box_text": (30, 30, 30),
    },
    "gradient_pop": {
        "bg": (88, 28, 135),
        "bg2": (15, 118, 110),
        "text": (255, 255, 255),
        "accent": (250, 204, 21),
        "box_bg": (88, 28, 135, 200),
        "box_text": (255, 255, 255),
    },
}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Tenta carregar fonte do sistema, senão usa default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    if bold:
        bold_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ]
        font_paths = bold_paths + font_paths

    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _create_gradient(width: int, height: int, color1: tuple, color2: tuple) -> Image.Image:
    """Cria imagem com gradiente vertical."""
    img = Image.new("RGB", (width, height))
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img


def _draw_text_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    line_spacing: int = 10,
) -> int:
    """Desenha texto com word wrap. Retorna y final."""
    # Estimar caracteres por linha
    avg_char_width = font.getlength("A")
    chars_per_line = max(1, int(max_width / avg_char_width))
    lines = []
    for paragraph in text.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=chars_per_line) or [""]
        lines.extend(wrapped)

    current_y = y
    for line in lines:
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += line_height + line_spacing

    return current_y


def _render_slide_image(
    slide: SlideContent,
    style: str = "dark_bold",
    total_slides: int = 1,
    width: int = 1080,
    height: int = 1350,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> Image.Image:
    """Renderiza um slide como imagem PIL."""
    palette = STYLE_PALETTES.get(style, STYLE_PALETTES["dark_bold"])

    # Criar imagem base
    if bg_image and Path(bg_image).exists():
        img = Image.open(bg_image).convert("RGBA")
        img = img.resize((width, height), Image.LANCZOS)
    elif "bg2" in palette:
        img = _create_gradient(width, height, palette["bg"], palette["bg2"]).convert("RGBA")
    else:
        img = Image.new("RGBA", (width, height), palette["bg"] + (255,))

    draw = ImageDraw.Draw(img)

    # Margens
    margin_x = 80
    margin_top = 120
    content_width = width - (margin_x * 2)

    # Contador de slides (canto superior direito)
    counter_font = _get_font(40)
    counter_text = f"{slide.index + 1}/{total_slides}"
    draw.text((width - margin_x - 60, 40), counter_text, font=counter_font, fill=palette["accent"])

    # Se tem imagem de fundo + text box
    if bg_image and text_box_style:
        box_margin = 60
        box_padding = 40
        box_x = box_margin
        box_w = width - (box_margin * 2)

        # Calcular altura do box baseado no conteúdo
        headline_font = _get_font(80, bold=True)
        body_font = _get_font(52)

        # Estimar altura
        headline_lines = len(textwrap.wrap(slide.headline, width=int((box_w - box_padding * 2) / 30))) or 1
        body_lines = len(textwrap.wrap(slide.body, width=int((box_w - box_padding * 2) / 20))) if slide.body else 0
        estimated_height = (headline_lines * 65) + (body_lines * 50) + box_padding * 3 + 30

        box_y = height - box_margin - estimated_height
        box_h = estimated_height

        # Desenhar box semi-transparente
        overlay = Image.new("RGBA", (box_w, box_h), palette.get("box_bg", (0, 0, 0, 200)))
        img.paste(overlay, (box_x, box_y), overlay)

        text_color = palette.get("box_text", (255, 255, 255))

        # Accent line
        accent_y = box_y + box_padding
        draw.rectangle(
            [box_x + box_padding, accent_y, box_x + box_padding + 60, accent_y + 5],
            fill=palette["accent"],
        )

        # Headline dentro do box
        y_pos = accent_y + 25
        y_pos = _draw_text_wrapped(
            draw, slide.headline.upper(),
            box_x + box_padding, y_pos,
            box_w - box_padding * 2,
            headline_font, text_color, line_spacing=12,
        )

        # Body dentro do box
        if slide.body:
            y_pos += 15
            _draw_text_wrapped(
                draw, slide.body,
                box_x + box_padding, y_pos,
                box_w - box_padding * 2,
                body_font, text_color, line_spacing=8,
            )
    else:
        # Renderização padrão (sem imagem de fundo)
        text_color = palette["text"]
        headline_font = _get_font(120, bold=True)
        body_font = _get_font(64)

        # Calcular altura total do conteúdo para centralizar verticalmente
        avg_char_w = headline_font.getlength("A")
        chars_per_line = max(1, int(content_width / avg_char_w))
        headline_lines = textwrap.wrap(slide.headline.upper(), width=chars_per_line) or [""]
        h_line_h = headline_font.getbbox("A")[3] - headline_font.getbbox("A")[1]
        total_headline_h = len(headline_lines) * (h_line_h + 16)

        total_body_h = 0
        if slide.body:
            avg_bw = body_font.getlength("A")
            b_chars = max(1, int(content_width / avg_bw))
            body_lines = textwrap.wrap(slide.body, width=b_chars) or [""]
            b_line_h = body_font.getbbox("A")[3] - body_font.getbbox("A")[1]
            total_body_h = len(body_lines) * (b_line_h + 12) + 40

        total_content_h = total_headline_h + total_body_h + 40  # 40 for accent line
        start_y = max(margin_top, (height - total_content_h) // 2 - 40)

        # Accent line
        draw.rectangle(
            [margin_x, start_y, margin_x + 80, start_y + 6],
            fill=palette["accent"],
        )

        # Headline
        y_pos = start_y + 35
        y_pos = _draw_text_wrapped(
            draw, slide.headline.upper(),
            margin_x, y_pos,
            content_width,
            headline_font, text_color, line_spacing=16,
        )

        # Body
        if slide.body:
            y_pos += 40
            _draw_text_wrapped(
                draw, slide.body,
                margin_x, y_pos,
                content_width,
                body_font, text_color, line_spacing=12,
            )

        # Slide type badge (hook, cta, etc.)
        if slide.slide_type in ("hook", "cta"):
            badge_font = _get_font(28)
            badge_text = slide.slide_type.upper()
            draw.text(
                (margin_x, height - 80),
                badge_text,
                font=badge_font,
                fill=palette["accent"],
            )

    return img.convert("RGB")


def render_carousel(
    slides: list[SlideContent],
    style: str = "dark_bold",
    width: int = 1080,
    height: int = 1350,
    output_dir: str | None = None,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> list[str]:
    """Renderiza todos os slides como PNGs. Retorna lista de caminhos."""
    if output_dir is None:
        output_dir = config.SLIDES_OUTPUT_DIR

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    rendered_paths = []
    total = len(slides)

    for slide in slides:
        img = _render_slide_image(slide, style, total, width, height, bg_image, text_box_style)
        file_name = f"slide_{slide.index + 1:02d}.png"
        file_path = out_path / file_name
        img.save(str(file_path), "PNG", quality=95)
        rendered_paths.append(str(file_path))

    return rendered_paths


def render_single_slide(
    slide: SlideContent,
    style: str = "dark_bold",
    total_slides: int = 1,
    width: int = 1080,
    height: int = 1350,
    output_dir: str | None = None,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> str:
    """Renderiza um único slide. Retorna caminho do PNG."""
    if output_dir is None:
        output_dir = config.SLIDES_OUTPUT_DIR
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    img = _render_slide_image(slide, style, total_slides, width, height, bg_image, text_box_style)
    file_name = f"slide_{slide.index + 1:02d}.png"
    file_path = out_path / file_name
    img.save(str(file_path), "PNG", quality=95)
    return str(file_path)


def render_slide_to_bytes(
    slide: SlideContent,
    style: str = "dark_bold",
    total_slides: int = 1,
    width: int = 1080,
    height: int = 1350,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> bytes:
    """Renderiza um slide e retorna bytes PNG (para preview sem salvar)."""
    img = _render_slide_image(slide, style, total_slides, width, height, bg_image, text_box_style)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_available_styles() -> list[str]:
    """Lista estilos disponíveis."""
    return list(STYLE_PALETTES.keys())
