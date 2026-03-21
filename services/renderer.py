from __future__ import annotations

import asyncio
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

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


def _build_html(slide: SlideContent, style: str, total_slides: int) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    # Carrega template do slide
    template_file = TEMPLATE_MAP.get(slide.slide_type, "slide_content.html")
    slide_template = env.get_template(template_file)
    slide_html = slide_template.render(
        headline=slide.headline,
        body=slide.body,
        slide_number=slide.index + 1,
        total_slides=total_slides,
    )

    # Carrega template base com CSS
    base_template = env.get_template("base.html")
    custom_css = _load_style_css(style)
    full_html = base_template.render(
        custom_css=custom_css,
        slide_content=slide_html,
    )
    return full_html


async def _render_slides_async(
    slides: list[SlideContent],
    style: str = "dark_bold",
    width: int = 1080,
    height: int = 1080,
    output_dir: str | None = None,
) -> list[str]:
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
            html = _build_html(slide, style, total)
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
    height: int = 1080,
    output_dir: str | None = None,
) -> list[str]:
    """Renderiza todos os slides como PNGs. Retorna lista de caminhos."""
    return asyncio.run(
        _render_slides_async(slides, style, width, height, output_dir)
    )


def render_single_slide(
    slide: SlideContent,
    style: str = "dark_bold",
    total_slides: int = 1,
    width: int = 1080,
    height: int = 1080,
    output_dir: str | None = None,
) -> str:
    """Renderiza um único slide. Retorna caminho do PNG."""
    if output_dir is None:
        output_dir = config.SLIDES_OUTPUT_DIR
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    async def _render():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})
            html = _build_html(slide, style, total_slides)
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
    slide: SlideContent, style: str = "dark_bold", total_slides: int = 1
) -> str:
    """Retorna o HTML completo do slide para preview no browser."""
    return _build_html(slide, style, total_slides)
