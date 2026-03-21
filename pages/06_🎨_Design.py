from __future__ import annotations

import io
import zipfile
from pathlib import Path

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from db.models import SlideContent
from services.renderer import render_carousel, get_available_styles

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
        options=["1080x1350 (Retrato 4:5)", "1080x1080 (Quadrado)"],
        index=0,
    )

width = 1080
height = 1350 if "1350" in dimensions else 1080

# ── Imagem de fundo ──────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Imagem de fundo (opcional)")

col_upload, col_textbox = st.columns(2)

with col_upload:
    uploaded_bg = st.file_uploader(
        "Upload de imagem de fundo",
        type=["jpg", "jpeg", "png", "webp"],
        help="A mesma imagem será usada em todos os slides. Use imagens de alta qualidade (1080px+).",
    )

bg_image_path = None
if uploaded_bg:
    bg_dir = Path(__file__).parent.parent / "data" / "backgrounds"
    bg_dir.mkdir(parents=True, exist_ok=True)
    bg_image_path = str(bg_dir / uploaded_bg.name)
    with open(bg_image_path, "wb") as f:
        f.write(uploaded_bg.getbuffer())
    st.success(f"Imagem carregada: {uploaded_bg.name}")

with col_textbox:
    text_box_style = None
    if uploaded_bg:
        text_box_option = st.selectbox(
            "Estilo das caixas de texto",
            options=["Texto branco, caixa escura", "Texto preto, caixa clara"],
            index=0,
        )
        text_box_style = "dark" if "escura" in text_box_option else "light"
    else:
        st.info("Faça upload de uma imagem para ativar as caixas de texto.")

# ── Resumo dos slides ────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Slides do Projeto")

for slide in project.slides:
    st.markdown(f"**Slide {slide.index + 1}** ({slide.slide_type.upper()}) — {slide.headline}")

# ── Renderizar PNGs ──────────────────────────────────────────────────────

st.markdown("---")

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
                bg_image=bg_image_path,
                text_box_style=text_box_style,
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
