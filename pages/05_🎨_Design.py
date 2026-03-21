from __future__ import annotations

import io
import zipfile
from pathlib import Path

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from db.models import SlideContent
from services.renderer import render_carousel, get_available_styles, get_slide_html_preview

st.set_page_config(page_title="Design", page_icon="🎨", layout="wide")
st.title("Design do Carrossel")

init_db()
conn = get_connection()

# ── Selecionar projeto ───────────────────────────────────────────────────

projects = repo.list_projects(conn)
ready_projects = [p for p in projects if p.status in ("copy_done", "designed")]

if not ready_projects:
    st.warning("Nenhum projeto pronto para design. Crie um na página Copywriter.")
    st.stop()

project_options = {p.id: f"{p.title} ({p.status})" for p in ready_projects}
selected_project_id = st.selectbox(
    "Selecione o projeto",
    options=list(project_options.keys()),
    format_func=lambda x: project_options[x],
    index=0,
)
project = repo.get_project(conn, selected_project_id)

if not project or not project.slides:
    st.error("Projeto sem slides.")
    st.stop()

st.markdown(f"**Tema:** {project.topic} | **Hook:** {project.hook} | **Slides:** {len(project.slides)}")
st.markdown("---")

# ── Configurações de estilo ──────────────────────────────────────────────

styles = get_available_styles()
style_labels = {
    "dark_bold": "Dark Bold — Fundo escuro, alto contraste",
    "light_minimal": "Light Minimal — Limpo e elegante",
    "gradient_pop": "Gradient Pop — Gradientes vibrantes",
}

col_style, col_size = st.columns(2)
with col_style:
    selected_style = st.selectbox(
        "Estilo visual",
        options=styles,
        format_func=lambda s: style_labels.get(s, s),
    )
with col_size:
    dimensions = st.selectbox(
        "Dimensões",
        options=["1080x1080 (Quadrado)", "1080x1350 (Retrato 4:5)"],
        index=0,
    )

width = 1080
height = 1080 if "1080x1080" in dimensions else 1350

# ── Preview HTML ─────────────────────────────────────────────────────────

st.subheader("Preview dos Slides")

preview_tabs = st.tabs([f"Slide {s.index + 1}" for s in project.slides])
for tab, slide in zip(preview_tabs, project.slides):
    with tab:
        html = get_slide_html_preview(slide, selected_style, len(project.slides))
        st.components.v1.html(html, height=500, scrolling=False)
        st.caption(f"**{slide.slide_type.upper()}** — {slide.headline}")

# ── Renderizar PNGs ──────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Renderizar Imagens")

if st.button("Renderizar todos os slides como PNG", type="primary", use_container_width=True):
    with st.spinner("Renderizando slides com Playwright..."):
        try:
            output_dir = str(
                Path(__file__).parent.parent / "output" / "slides" / f"project_{project.id}"
            )
            paths = render_carousel(
                project.slides,
                style=selected_style,
                width=width,
                height=height,
                output_dir=output_dir,
            )

            # Atualizar image_path nos slides
            updated_slides = []
            for slide, path in zip(project.slides, paths):
                updated_slides.append(
                    SlideContent(
                        index=slide.index,
                        slide_type=slide.slide_type,
                        headline=slide.headline,
                        body=slide.body,
                        image_path=path,
                    )
                )
            project.slides = updated_slides
            project.style_template = selected_style
            project.status = "designed"
            repo.update_project(conn, project)

            st.session_state["rendered_paths"] = paths
            st.success(f"{len(paths)} slides renderizados!")
        except Exception as e:
            st.error(f"Erro na renderização: {e}")
            st.info("Verifique se o Playwright está instalado: `playwright install chromium`")

# ── Exibir imagens renderizadas ──────────────────────────────────────────

rendered_paths = st.session_state.get("rendered_paths", [])
if not rendered_paths and project.slides and project.slides[0].image_path:
    rendered_paths = [s.image_path for s in project.slides if s.image_path]

if rendered_paths:
    st.markdown("---")
    st.subheader("Slides Renderizados")

    cols = st.columns(min(len(rendered_paths), 4))
    for i, path in enumerate(rendered_paths):
        p = Path(path)
        if p.exists():
            with cols[i % len(cols)]:
                st.image(str(p), caption=f"Slide {i + 1}", use_container_width=True)

    # Download individual e ZIP
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        for i, path in enumerate(rendered_paths):
            p = Path(path)
            if p.exists():
                st.download_button(
                    f"Download Slide {i + 1}",
                    data=p.read_bytes(),
                    file_name=f"slide_{i + 1}.png",
                    mime="image/png",
                    key=f"dl_slide_{i}",
                )

    with col_dl2:
        # ZIP com todos os slides
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, path in enumerate(rendered_paths):
                p = Path(path)
                if p.exists():
                    zf.write(p, f"slide_{i + 1}.png")
        zip_buffer.seek(0)

        st.download_button(
            "Download todos (ZIP)",
            data=zip_buffer,
            file_name=f"carrossel_{project.id}.zip",
            mime="application/zip",
            type="primary",
        )
