from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ICP:
    name: str
    niche: str
    demographics: dict  # {"age_range": "25-45", "gender": "all", "location": "Brasil"}
    pain_points: list[str]
    desires: list[str]
    objections: list[str]
    language_style: str
    tone_keywords: list[str]
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Offer:
    icp_id: int
    name: str
    # Equação de valor
    dream: str
    success_proofs: list[str]
    time_to_result: str
    effort_level: str
    # Componentes da oferta
    core_promise: str = ""
    bonuses: list[str] = field(default_factory=list)
    scarcity: str = ""
    guarantee: str = ""
    method_name: str = ""
    summary: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class InstagramPost:
    ig_media_id: str
    media_type: str  # IMAGE, VIDEO, CAROUSEL_ALBUM
    caption: str
    permalink: str
    timestamp: datetime
    reach: int = 0
    impressions: int = 0
    engagement: int = 0
    saves: int = 0
    shares: int = 0
    comments_count: int = 0
    likes_count: int = 0
    id: int | None = None
    fetched_at: datetime = field(default_factory=datetime.now)


@dataclass
class SlideContent:
    index: int
    slide_type: str  # hook, content, listicle, quote, cta
    headline: str
    body: str
    image_path: str | None = None


@dataclass
class CarouselProject:
    icp_id: int
    title: str
    topic: str = ""
    hook: str = ""
    slides: list[SlideContent] = field(default_factory=list)
    caption: str = ""
    hashtags: str = ""
    style_template: str = "dark_bold"
    design_source: str = "html"  # html | canva
    status: str = "draft"  # draft | copy_done | designed | published
    canva_design_id: str | None = None
    ig_media_id: str | None = None
    published_at: datetime | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
