from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import config
from db.models import SlideContent

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Mapeamento de slide_type para template
TEMPLATE_MAP = {
    "hook": "slide_hook.html",
    "content": "slide_content.html",
    "listicle": "slide_listicle.html",
    "quote": "slide_quote.html",
    "cta": "slide_cta.html",
}


def _load_style_css(style_name: str) -> str:
    css_path = TEMPLATES_DIR / "styles" / f"{style_name}.css"
    if not css_path.exists():
        css_path = TEMPLATES_DIR / "styles" / "dark_bold.css"
    return css_path.read_text(encoding="utf-8")


def _image_to_data_uri(image_path: str) -> str:
    """Converte imagem em data URI base64 para embutir no HTML."""
    p = Path(image_path)
    if not p.exists():
        return ""
    suffix = p.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/jpeg")
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _build_html(
    slide: SlideContent,
    style: str,
    total_slides: int,
    height: int = 1350,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    # Determinar classe da text-box
    text_box_class = ""
    if bg_image or text_box_style:
        if text_box_style == "light":
            text_box_class = "text-box text-box-light"
        elif text_box_style == "dark":
            text_box_class = "text-box text-box-dark"

    # Carrega template do slide
    template_file = TEMPLATE_MAP.get(slide.slide_type, "slide_content.html")
    slide_template = env.get_template(template_file)
    slide_html = slide_template.render(
        headline=slide.headline,
        body=slide.body,
        slide_number=slide.index + 1,
        total_slides=total_slides,
        text_box_class=text_box_class,
    )

    # Resolver imagem de fundo
    bg_data_uri = ""
    if bg_image:
        bg_data_uri = _image_to_data_uri(bg_image)

    # Carrega template base com CSS
    base_template = env.get_template("base.html")
    custom_css = _load_style_css(style)
    full_html = base_template.render(
        custom_css=custom_css,
        slide_content=slide_html,
        height=height,
        bg_image=bg_data_uri if bg_data_uri else "",
    )
    return full_html


def _has_playwright() -> bool:
    """Verifica se o Playwright está disponível e com browsers instalados."""
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        return False


async def _render_slides_async(
    slides: list[SlideContent],
    style: str = "dark_bold",
    width: int = 1080,
    height: int = 1350,
    output_dir: str | None = None,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> list[str]:
    from playwright.async_api import async_playwright

    if output_dir is None:
        output_dir = config.SLIDES_OUTPUT_DIR

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    rendered_paths = []
    total = len(slides)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})

        for slide in slides:
            html = _build_html(slide, style, total, height, bg_image, text_box_style)
            await page.set_content(html, wait_until="networkidle")
            file_name = f"slide_{slide.index + 1:02d}.png"
            file_path = out_path / file_name
            await page.screenshot(path=str(file_path))
            rendered_paths.append(str(file_path))

        await browser.close()

    return rendered_paths


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
    return asyncio.run(
        _render_slides_async(slides, style, width, height, output_dir, bg_image, text_box_style)
    )


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

    async def _render():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})
            html = _build_html(slide, style, total_slides, height, bg_image, text_box_style)
            await page.set_content(html, wait_until="networkidle")
            file_name = f"slide_{slide.index + 1:02d}.png"
            file_path = out_path / file_name
            await page.screenshot(path=str(file_path))
            await browser.close()
            return str(file_path)

    return asyncio.run(_render())


def get_available_styles() -> list[str]:
    """Lista estilos CSS disponíveis."""
    styles_dir = TEMPLATES_DIR / "styles"
    return [f.stem for f in styles_dir.glob("*.css")]


def get_slide_html_preview(
    slide: SlideContent,
    style: str = "dark_bold",
    total_slides: int = 1,
    height: int = 1350,
    bg_image: str | None = None,
    text_box_style: str | None = None,
) -> str:
    """Retorna o HTML completo do slide para preview no browser."""
    return _build_html(slide, style, total_slides, height, bg_image, text_box_style)
