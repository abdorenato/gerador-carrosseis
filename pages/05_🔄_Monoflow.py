from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import streamlit as st
from db.database import init_db, get_connection
from db import repositories as repo
from db.models import SlideContent
from services.monoflow_generator import (
    generate_mother_text,
    generate_instagram_reels,
    generate_instagram_post,
    generate_instagram_carousel,
    generate_instagram_stories,
    generate_linkedin_post,
    generate_tiktok_video,
    refine_content,
)
from services.image_service import search_unsplash, download_image
from services.renderer import render_carousel, get_available_styles
from utils.auth_guard import require_login

require_login()

init_db()
conn = get_connection()


# ══════════════════════════════════════════════════════════════════════════
# Funções auxiliares de renderização
# ══════════════════════════════════════════════════════════════════════════

def _render_platform_tab(platform: str, data: dict, icp):
    """Renderiza o conteúdo de cada plataforma em sua tab."""
    if platform == "reels":
        _render_reels(data)
    elif platform == "post":
        _render_post(data)
    elif platform == "carousel":
        _render_carousel(data)
    elif platform == "stories":
        _render_stories(data)
    elif platform == "linkedin":
        _render_linkedin(data)
    elif platform == "tiktok":
        _render_tiktok(data)

    st.text_area(
        "📋 Conteúdo completo (copie daqui)",
        value=_format_copy_text(platform, data),
        height=200,
        key=f"copy_{platform}",
    )


def _format_copy_text(platform: str, data: dict) -> str:
    """Formata o conteúdo para fácil cópia."""
    if platform == "reels":
        lines = [f"🎬 ROTEIRO DE REELS — {data.get('title', '')}"]
        lines.append(f"Duração: {data.get('duration', '')}")
        lines.append(f"\n🪝 HOOK: {data.get('hook', '')}\n")
        for scene in data.get("scenes", []):
            lines.append(f"[{scene.get('time', '')}] {scene.get('action', '')}")
            if scene.get("text_overlay"):
                lines.append(f"   📝 Texto: {scene['text_overlay']}")
        lines.append(f"\n📢 CTA: {data.get('cta', '')}")
        lines.append(f"\n📝 LEGENDA:\n{data.get('caption', '')}")
        lines.append(f"\n🎵 Áudio: {data.get('audio_suggestion', '')}")
        return "\n".join(lines)
    elif platform == "post":
        lines = ["📸 POST INSTAGRAM\n"]
        lines.append(data.get("caption", ""))
        lines.append(f"\n#️⃣ {' '.join('#' + h for h in data.get('hashtags', []))}")
        lines.append(f"\n⏰ Melhor horário: {data.get('best_time', '')}")
        lines.append(f"🖼️ Imagem: {data.get('image_suggestion', '')}")
        return "\n".join(lines)
    elif platform == "carousel":
        lines = ["🎠 CARROSSEL INSTAGRAM\n"]
        for slide in data.get("slides", []):
            lines.append(f"— Slide {slide.get('index', 0) + 1} ({slide.get('slide_type', '')}) —")
            lines.append(f"  {slide.get('headline', '')}")
            if slide.get("body"):
                lines.append(f"  {slide['body']}")
            lines.append("")
        lines.append(f"📝 LEGENDA:\n{data.get('caption', '')}")
        lines.append(f"\n#️⃣ {' '.join('#' + h for h in data.get('hashtags', []))}")
        return "\n".join(lines)
    elif platform == "stories":
        lines = ["📱 SEQUÊNCIA DE STORIES\n"]
        lines.append(f"Estratégia: {data.get('strategy', '')}\n")
        for story in data.get("stories", []):
            lines.append(f"— Story {story.get('order', '')} ({story.get('type', '')}) —")
            lines.append(f"  {story.get('text', '')}")
            sticker = story.get("sticker", {})
            if sticker:
                lines.append(f"  🏷️ {sticker.get('type', '')}: {sticker.get('question', '')}")
                if sticker.get("options"):
                    lines.append(f"     Opções: {' | '.join(sticker['options'])}")
            lines.append(f"  🎨 Visual: {story.get('visual_tip', '')}")
            lines.append("")
        return "\n".join(lines)
    elif platform == "linkedin":
        lines = ["💼 POST LINKEDIN\n"]
        lines.append(data.get("post", ""))
        lines.append(f"\n#️⃣ {' '.join('#' + h for h in data.get('hashtags', []))}")
        return "\n".join(lines)
    elif platform == "tiktok":
        lines = [f"🎵 ROTEIRO TIKTOK — {data.get('title', '')}"]
        lines.append(f"Duração: {data.get('duration', '')}")
        lines.append(f"\n🪝 HOOK: {data.get('hook', '')}\n")
        for scene in data.get("scenes", []):
            lines.append(f"[{scene.get('time', '')}] {scene.get('action', '')}")
            if scene.get("text_overlay"):
                lines.append(f"   📝 Texto: {scene['text_overlay']}")
        lines.append(f"\n📢 CTA: {data.get('cta', '')}")
        lines.append(f"\n📝 LEGENDA:\n{data.get('caption', '')}")
        lines.append(f"\n🎵 Som: {data.get('sound_suggestion', '')}")
        lines.append(f"💡 Dicas: {data.get('tiktok_tips', '')}")
        return "\n".join(lines)
    return json.dumps(data, ensure_ascii=False, indent=2)


def _render_reels(data: dict):
    st.markdown(f"### 📹 {data.get('title', 'Reels')}")
    st.markdown(f"**Duração:** {data.get('duration', '')}")
    st.markdown(f"**🪝 Hook:** {data.get('hook', '')}")
    st.markdown("**Cenas:**")
    for scene in data.get("scenes", []):
        with st.container():
            cols = st.columns([1, 3, 2])
            cols[0].markdown(f"`{scene.get('time', '')}`")
            cols[1].markdown(scene.get("action", ""))
            cols[2].markdown(f"📝 {scene.get('text_overlay', '')}")
    st.markdown(f"**📢 CTA:** {data.get('cta', '')}")
    st.markdown(f"**🎵 Áudio:** {data.get('audio_suggestion', '')}")
    if data.get("trend_tip"):
        st.info(f"💡 **Trend tip:** {data['trend_tip']}")


def _render_post(data: dict):
    st.markdown("### 📸 Post Instagram")
    st.markdown(data.get("caption", ""))
    if data.get("hashtags"):
        st.markdown(f"**#️⃣** {' '.join('#' + h for h in data['hashtags'])}")
    if data.get("best_time"):
        st.markdown(f"**⏰ Melhor horário:** {data['best_time']}")
    if data.get("headline_on_image"):
        st.markdown(f"**📝 Título na imagem:** {data['headline_on_image']}")

    # ── Busca e renderização de imagem ──
    keywords = data.get("image_keywords", [])
    if keywords:
        st.markdown("---")
        st.markdown("#### 🖼️ Imagem do Post")
        query = " ".join(keywords[:3])

        if st.button("🔍 Buscar fotos no Unsplash", key="search_post_img"):
            with st.spinner("Buscando fotos..."):
                photos = search_unsplash(query, count=6)
                st.session_state["post_photos"] = photos

        photos = st.session_state.get("post_photos", [])
        if photos:
            st.caption(f"Busca: \"{query}\"")
            cols = st.columns(3)
            for i, photo in enumerate(photos):
                with cols[i % 3]:
                    st.image(photo["thumb"], caption=f"📷 {photo['author']}", use_container_width=True)
                    if st.button("Usar esta", key=f"use_post_photo_{i}"):
                        st.session_state["selected_post_photo"] = photo
                        st.rerun()

            selected = st.session_state.get("selected_post_photo")
            if selected:
                st.success(f"Foto selecionada: {selected['author']}")

                text_box_opt = st.selectbox(
                    "Estilo do texto",
                    ["Texto branco, caixa escura", "Texto preto, caixa clara"],
                    key="post_text_style",
                )
                text_box_style = "dark" if "escura" in text_box_opt else "light"

                if st.button("🎨 Renderizar Post", key="render_post", type="primary"):
                    with st.spinner("Renderizando..."):
                        try:
                            bg_dir = str(Path(__file__).parent.parent / "data" / "backgrounds")
                            bg_path = download_image(selected["url"], bg_dir, "post_bg.jpg")

                            headline = data.get("headline_on_image", data.get("caption", "")[:50])
                            slide = SlideContent(index=0, slide_type="hook", headline=headline, body="")
                            output_dir = str(Path(__file__).parent.parent / "output" / "monoflow_post")
                            paths = render_carousel(
                                [slide], style="dark_bold", width=1080, height=1080,
                                output_dir=output_dir, bg_image=bg_path, text_box_style=text_box_style,
                            )
                            st.session_state["rendered_post"] = paths[0]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

            rendered = st.session_state.get("rendered_post")
            if rendered and Path(rendered).exists():
                st.image(rendered, caption="Post renderizado", use_container_width=True)
                st.download_button(
                    "📥 Download Post",
                    data=Path(rendered).read_bytes(),
                    file_name="post_instagram.png",
                    mime="image/png",
                    key="dl_post",
                )
                st.caption(f"📷 Foto: {st.session_state.get('selected_post_photo', {}).get('author', '')} via Unsplash")
    elif data.get("image_suggestion"):
        st.info(f"🖼️ **Sugestão de imagem:** {data['image_suggestion']}")


def _render_carousel(data: dict):
    st.markdown("### 🎠 Carrossel Instagram")
    slides_data = data.get("slides", [])
    if slides_data:
        slide_tabs = st.tabs([f"Slide {s.get('index', 0) + 1}" for s in slides_data])
        for tab, slide in zip(slide_tabs, slides_data):
            with tab:
                st.markdown(f"**Tipo:** {slide.get('slide_type', '')}")
                st.markdown(f"### {slide.get('headline', '')}")
                if slide.get("body"):
                    st.markdown(slide["body"])
    st.markdown("---")
    st.markdown(f"**📝 Legenda:** {data.get('caption', '')}")
    if data.get("hashtags"):
        st.markdown(f"**#️⃣** {' '.join('#' + h for h in data['hashtags'])}")

    # ── Busca de imagem e renderização ──
    keywords = data.get("image_keywords", [])
    if slides_data:
        st.markdown("---")
        st.markdown("#### 🎨 Renderizar Carrossel")

        col_style, col_textbox = st.columns(2)
        with col_style:
            styles = get_available_styles()
            style_labels = {
                "dark_bold": "Dark Bold",
                "light_minimal": "Light Minimal",
                "gradient_pop": "Gradient Pop",
            }
            selected_style = st.selectbox(
                "Estilo visual",
                options=styles,
                format_func=lambda s: style_labels.get(s, s),
                key="carousel_style",
            )
        with col_textbox:
            use_bg = st.checkbox("Usar foto de fundo", value=bool(keywords), key="carousel_use_bg")

        if use_bg and keywords:
            query = " ".join(keywords[:3])
            if st.button("🔍 Buscar fotos no Unsplash", key="search_carousel_img"):
                with st.spinner("Buscando fotos..."):
                    photos = search_unsplash(query, count=6)
                    st.session_state["carousel_photos"] = photos

            photos = st.session_state.get("carousel_photos", [])
            if photos:
                st.caption(f"Busca: \"{query}\"")
                cols = st.columns(3)
                for i, photo in enumerate(photos):
                    with cols[i % 3]:
                        st.image(photo["thumb"], caption=f"📷 {photo['author']}", use_container_width=True)
                        if st.button("Usar", key=f"use_carousel_photo_{i}"):
                            st.session_state["selected_carousel_photo"] = photo
                            st.rerun()

        # Botão de renderizar
        selected_photo = st.session_state.get("selected_carousel_photo") if use_bg else None
        if selected_photo:
            st.success(f"Foto selecionada: {selected_photo['author']}")
            text_box_opt = st.selectbox(
                "Estilo do texto sobre imagem",
                ["Texto branco, caixa escura", "Texto preto, caixa clara"],
                key="carousel_text_style",
            )
            text_box_style = "dark" if "escura" in text_box_opt else "light"
        else:
            text_box_style = None

        if st.button("🚀 Renderizar slides", key="render_carousel", type="primary", use_container_width=True):
            with st.spinner("Renderizando slides..."):
                try:
                    # Converter dicts em SlideContent
                    slide_objects = [
                        SlideContent(
                            index=s.get("index", i),
                            slide_type=s.get("slide_type", "content"),
                            headline=s.get("headline", ""),
                            body=s.get("body", ""),
                        )
                        for i, s in enumerate(slides_data)
                    ]

                    # Download foto se selecionada
                    bg_path = None
                    if selected_photo:
                        bg_dir = str(Path(__file__).parent.parent / "data" / "backgrounds")
                        bg_path = download_image(selected_photo["url"], bg_dir, "carousel_bg.jpg")

                    output_dir = str(Path(__file__).parent.parent / "output" / "monoflow_carousel")
                    paths = render_carousel(
                        slide_objects,
                        style=selected_style,
                        width=1080,
                        height=1350,
                        output_dir=output_dir,
                        bg_image=bg_path,
                        text_box_style=text_box_style,
                    )
                    st.session_state["rendered_carousel_paths"] = paths
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na renderização: {e}")

        # Mostrar slides renderizados
        rendered = st.session_state.get("rendered_carousel_paths", [])
        if rendered:
            st.markdown("---")
            st.markdown("#### Slides Renderizados")
            img_cols = st.columns(min(len(rendered), 4))
            for i, path in enumerate(rendered):
                p = Path(path)
                if p.exists():
                    with img_cols[i % len(img_cols)]:
                        st.image(str(p), caption=f"Slide {i + 1}", use_container_width=True)

            # Downloads
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                for i, path in enumerate(rendered):
                    p = Path(path)
                    if p.exists():
                        st.download_button(
                            f"📥 Slide {i + 1}",
                            data=p.read_bytes(),
                            file_name=f"slide_{i + 1}.png",
                            mime="image/png",
                            key=f"dl_carousel_slide_{i}",
                        )
            with dl_col2:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, path in enumerate(rendered):
                        p = Path(path)
                        if p.exists():
                            zf.write(p, f"slide_{i + 1}.png")
                zip_buf.seek(0)
                st.download_button(
                    "📥 Download todos (ZIP)",
                    data=zip_buf,
                    file_name="carrossel_monoflow.zip",
                    mime="application/zip",
                    type="primary",
                    key="dl_carousel_zip",
                )
            if selected_photo:
                st.caption(f"📷 Foto: {selected_photo.get('author', '')} via Unsplash")


def _render_stories(data: dict):
    st.markdown("### 📱 Stories Instagram")
    if data.get("strategy"):
        st.info(f"🎯 **Estratégia:** {data['strategy']}")
    for story in data.get("stories", []):
        with st.expander(f"Story {story.get('order', '')} — {story.get('type', '').upper()}", expanded=True):
            st.markdown(story.get("text", ""))
            sticker = story.get("sticker", {})
            if sticker:
                st.markdown(f"**🏷️ {sticker.get('type', '').upper()}:** {sticker.get('question', '')}")
                if sticker.get("options"):
                    for opt in sticker["options"]:
                        st.markdown(f"  - {opt}")
            if story.get("visual_tip"):
                st.caption(f"🎨 {story['visual_tip']}")


def _render_linkedin(data: dict):
    st.markdown("### 💼 Post LinkedIn")
    st.markdown(data.get("post", ""))
    if data.get("hashtags"):
        st.markdown(f"**#️⃣** {' '.join('#' + h for h in data['hashtags'])}")


def _render_tiktok(data: dict):
    st.markdown(f"### 🎵 {data.get('title', 'TikTok')}")
    st.markdown(f"**Duração:** {data.get('duration', '')}")
    st.markdown(f"**🪝 Hook:** {data.get('hook', '')}")
    st.markdown("**Cenas:**")
    for scene in data.get("scenes", []):
        with st.container():
            cols = st.columns([1, 3, 2])
            cols[0].markdown(f"`{scene.get('time', '')}`")
            cols[1].markdown(scene.get("action", ""))
            cols[2].markdown(f"📝 {scene.get('text_overlay', '')}")
    st.markdown(f"**📢 CTA:** {data.get('cta', '')}")
    st.markdown(f"**🎵 Som sugerido:** {data.get('sound_suggestion', '')}")
    if data.get("tiktok_tips"):
        st.info(f"💡 **Dicas TikTok:** {data['tiktok_tips']}")


# ══════════════════════════════════════════════════════════════════════════
# Página principal
# ══════════════════════════════════════════════════════════════════════════

st.title("🔄 Monoflow")
st.caption("Um tema → múltiplos conteúdos para todas as plataformas")

# ── Seletor de ICP ─────────────────────────────────────────────────────────
icps = repo.list_icps(conn)
if not icps:
    st.warning("Cadastre um ICP primeiro na página ICP.")
    st.stop()

icp_options = {icp.id: icp.name for icp in icps}
selected_icp_id = st.selectbox(
    "Selecione o ICP",
    options=list(icp_options.keys()),
    format_func=lambda x: icp_options[x],
)
icp = repo.get_icp(conn, selected_icp_id)

# Oferta (opcional)
offers = repo.list_offers_by_icp(conn, selected_icp_id)
offer = None
if offers:
    offer_options = {0: "Nenhuma"} | {o.id: o.name for o in offers}
    selected_offer_id = st.selectbox(
        "Oferta ativa (opcional)",
        options=list(offer_options.keys()),
        format_func=lambda x: offer_options[x],
    )
    if selected_offer_id:
        offer = repo.get_offer(conn, selected_offer_id)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Ideia
# ══════════════════════════════════════════════════════════════════════════

st.subheader("1️⃣ Ideia")

idea_source = st.radio(
    "Origem da ideia",
    ["Banco de ideias", "Escrever manualmente"],
    horizontal=True,
)

idea = None

if idea_source == "Banco de ideias":
    # Carregar ideias do banco filtradas por ICP e oferta
    offer_filter_id = offer.id if offer else None
    saved_ideas = repo.list_ideas_by_icp(conn, selected_icp_id, offer_filter_id)

    # Se não encontrou com filtro de oferta, tenta sem
    if not saved_ideas and offer_filter_id:
        saved_ideas = repo.list_ideas_by_icp(conn, selected_icp_id)
        if saved_ideas:
            st.caption("Mostrando todas as ideias do ICP (nenhuma específica para esta oferta)")

    # Também verificar session_state (ideias recém-geradas)
    monoflow_idea = st.session_state.get("monoflow_idea")

    if monoflow_idea:
        st.success(f"Ideia pré-selecionada: **{monoflow_idea.get('topic', '')}**")
        idea = monoflow_idea
        if st.button("Limpar seleção"):
            del st.session_state["monoflow_idea"]
            st.rerun()
    elif saved_ideas:
        idea_titles = [f"{i.get('topic', 'Sem tema')}" for i in saved_ideas]
        sel_idx = st.selectbox(
            f"Escolha uma ideia ({len(saved_ideas)} disponíveis)",
            range(len(idea_titles)),
            format_func=lambda x: idea_titles[x],
        )
        idea = saved_ideas[sel_idx]
        with st.expander("Detalhes da ideia"):
            st.markdown(f"**Hook:** {idea.get('hook', '-')}")
            st.markdown(f"**Ângulo:** {idea.get('angle', '-')}")
            st.markdown(f"**Emoção:** {idea.get('target_emotion', '-')}")
            st.markdown(f"**Estilo:** {idea.get('carousel_style', '-')}")
    else:
        st.info("Nenhuma ideia salva para este ICP. Vá para **Ideas** para gerar ou escreva manualmente.")
else:
    topic = st.text_input("Tema", placeholder="Ex: 5 erros que matam sua produtividade")
    hook = st.text_input("Hook", placeholder="Ex: Você está sabotando seu próprio sucesso...")
    angle = st.text_input("Ângulo (opcional)", placeholder="Ex: Contraintuitivo")
    emotion = st.text_input("Emoção alvo (opcional)", placeholder="Ex: Urgência")
    if topic and hook:
        idea = {
            "topic": topic,
            "hook": hook,
            "angle": angle or "direto",
            "target_emotion": emotion or "curiosidade",
        }

if not idea:
    st.stop()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# ETAPA 2 — Texto-mãe
# ══════════════════════════════════════════════════════════════════════════

st.subheader("2️⃣ Texto-mãe")

# Inicializa session state
if "monoflow" not in st.session_state:
    st.session_state["monoflow"] = {}

monoflow = st.session_state["monoflow"]

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🧠 Gerar texto-mãe", type="primary", use_container_width=True):
        with st.spinner("Gerando texto-mãe..."):
            try:
                text = generate_mother_text(icp, idea, offer)
                monoflow["mother_text"] = text
                monoflow["idea"] = idea
                monoflow["contents"] = {}
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

with col2:
    if monoflow.get("mother_text"):
        if st.button("🔄 Regenerar", use_container_width=True):
            with st.spinner("Regenerando..."):
                try:
                    text = generate_mother_text(icp, idea, offer)
                    monoflow["mother_text"] = text
                    monoflow["contents"] = {}
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

if monoflow.get("mother_text"):
    edited_text = st.text_area(
        "Texto-mãe (edite se quiser)",
        value=monoflow["mother_text"],
        height=300,
    )
    monoflow["mother_text"] = edited_text

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════
    # ETAPA 3 — Desdobramentos
    # ══════════════════════════════════════════════════════════════════════

    st.subheader("3️⃣ Escolha as plataformas")

    col1, col2, col3 = st.columns(3)
    with col1:
        do_reels = st.checkbox("📹 Instagram Reels", value=True)
        do_post = st.checkbox("📸 Instagram Post", value=True)
    with col2:
        do_carousel = st.checkbox("🎠 Instagram Carrossel", value=True)
        do_stories = st.checkbox("📱 Instagram Stories", value=True)
    with col3:
        do_linkedin = st.checkbox("💼 LinkedIn Post", value=True)
        do_tiktok = st.checkbox("🎵 TikTok", value=True)

    if do_carousel:
        num_slides = st.slider("Slides do carrossel", 3, 10, 7)
    else:
        num_slides = 7

    if st.button("🚀 Gerar conteúdos", type="primary", use_container_width=True):
        mother = monoflow["mother_text"]
        contents = {}
        progress = st.progress(0)
        platforms = []
        if do_reels:
            platforms.append("reels")
        if do_post:
            platforms.append("post")
        if do_carousel:
            platforms.append("carousel")
        if do_stories:
            platforms.append("stories")
        if do_linkedin:
            platforms.append("linkedin")
        if do_tiktok:
            platforms.append("tiktok")

        total = len(platforms)

        for i, p in enumerate(platforms):
            progress.progress((i) / total, text=f"Gerando {p}...")
            try:
                if p == "reels":
                    contents["reels"] = generate_instagram_reels(icp, mother)
                elif p == "post":
                    contents["post"] = generate_instagram_post(icp, mother)
                elif p == "carousel":
                    contents["carousel"] = generate_instagram_carousel(icp, mother, num_slides)
                elif p == "stories":
                    contents["stories"] = generate_instagram_stories(icp, mother)
                elif p == "linkedin":
                    contents["linkedin"] = generate_linkedin_post(icp, mother)
                elif p == "tiktok":
                    # TikTok depende do Reels
                    if "reels" not in contents:
                        contents["reels"] = generate_instagram_reels(icp, mother)
                    contents["tiktok"] = generate_tiktok_video(icp, contents["reels"])
            except Exception as e:
                st.error(f"Erro ao gerar {p}: {e}")

        progress.progress(1.0, text="Concluído!")
        monoflow["contents"] = contents
        st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # ETAPA 4 — Revisão por plataforma
    # ══════════════════════════════════════════════════════════════════════

    contents = monoflow.get("contents", {})

    if contents:
        st.markdown("---")
        st.subheader("4️⃣ Conteúdos gerados")

        tab_names = []
        tab_keys = []
        if "reels" in contents:
            tab_names.append("📹 Reels")
            tab_keys.append("reels")
        if "post" in contents:
            tab_names.append("📸 Post")
            tab_keys.append("post")
        if "carousel" in contents:
            tab_names.append("🎠 Carrossel")
            tab_keys.append("carousel")
        if "stories" in contents:
            tab_names.append("📱 Stories")
            tab_keys.append("stories")
        if "linkedin" in contents:
            tab_names.append("💼 LinkedIn")
            tab_keys.append("linkedin")
        if "tiktok" in contents:
            tab_names.append("🎵 TikTok")
            tab_keys.append("tiktok")

        if tab_names:
            tabs = st.tabs(tab_names)

            for tab, key in zip(tabs, tab_keys):
                with tab:
                    data = contents[key]
                    _render_platform_tab(key, data, icp)
