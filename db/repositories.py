from __future__ import annotations
import json
from datetime import datetime
from sqlite3 import Connection

from db.models import ICP, InstagramPost, CarouselProject, SlideContent, Offer


# ── ICP ──────────────────────────────────────────────────────────────────

def create_icp(conn: Connection, icp: ICP) -> int:
    cur = conn.execute(
        """INSERT INTO icps (name, niche, demographics, pain_points, desires,
           objections, language_style, tone_keywords)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            icp.name,
            icp.niche,
            json.dumps(icp.demographics, ensure_ascii=False),
            json.dumps(icp.pain_points, ensure_ascii=False),
            json.dumps(icp.desires, ensure_ascii=False),
            json.dumps(icp.objections, ensure_ascii=False),
            icp.language_style,
            json.dumps(icp.tone_keywords, ensure_ascii=False),
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_icp(conn: Connection, icp_id: int) -> ICP | None:
    row = conn.execute("SELECT * FROM icps WHERE id = ?", (icp_id,)).fetchone()
    if row is None:
        return None
    return _row_to_icp(row)


def list_icps(conn: Connection) -> list[ICP]:
    rows = conn.execute("SELECT * FROM icps ORDER BY updated_at DESC").fetchall()
    return [_row_to_icp(r) for r in rows]


def update_icp(conn: Connection, icp: ICP) -> None:
    conn.execute(
        """UPDATE icps SET name=?, niche=?, demographics=?, pain_points=?,
           desires=?, objections=?, language_style=?, tone_keywords=?,
           updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (
            icp.name,
            icp.niche,
            json.dumps(icp.demographics, ensure_ascii=False),
            json.dumps(icp.pain_points, ensure_ascii=False),
            json.dumps(icp.desires, ensure_ascii=False),
            json.dumps(icp.objections, ensure_ascii=False),
            icp.language_style,
            json.dumps(icp.tone_keywords, ensure_ascii=False),
            icp.id,
        ),
    )
    conn.commit()


def delete_icp(conn: Connection, icp_id: int) -> None:
    conn.execute("DELETE FROM icps WHERE id = ?", (icp_id,))
    conn.commit()


def _row_to_icp(row) -> ICP:
    return ICP(
        id=row["id"],
        name=row["name"],
        niche=row["niche"],
        demographics=json.loads(row["demographics"]),
        pain_points=json.loads(row["pain_points"]),
        desires=json.loads(row["desires"]),
        objections=json.loads(row["objections"]),
        language_style=row["language_style"],
        tone_keywords=json.loads(row["tone_keywords"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ── Offers ───────────────────────────────────────────────────────────────

def create_offer(conn: Connection, offer: Offer) -> int:
    cur = conn.execute(
        """INSERT INTO offers (icp_id, name, dream, success_proofs,
           time_to_result, effort_level, core_promise, bonuses,
           scarcity, guarantee, method_name, summary)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            offer.icp_id,
            offer.name,
            offer.dream,
            json.dumps(offer.success_proofs, ensure_ascii=False),
            offer.time_to_result,
            offer.effort_level,
            offer.core_promise,
            json.dumps(offer.bonuses, ensure_ascii=False),
            offer.scarcity,
            offer.guarantee,
            offer.method_name,
            offer.summary,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_offer(conn: Connection, offer_id: int) -> Offer | None:
    row = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    if row is None:
        return None
    return _row_to_offer(row)


def list_offers_by_icp(conn: Connection, icp_id: int) -> list[Offer]:
    rows = conn.execute(
        "SELECT * FROM offers WHERE icp_id = ? ORDER BY updated_at DESC",
        (icp_id,),
    ).fetchall()
    return [_row_to_offer(r) for r in rows]


def update_offer(conn: Connection, offer: Offer) -> None:
    conn.execute(
        """UPDATE offers SET name=?, dream=?, success_proofs=?,
           time_to_result=?, effort_level=?, core_promise=?,
           bonuses=?, scarcity=?, guarantee=?, method_name=?,
           summary=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (
            offer.name,
            offer.dream,
            json.dumps(offer.success_proofs, ensure_ascii=False),
            offer.time_to_result,
            offer.effort_level,
            offer.core_promise,
            json.dumps(offer.bonuses, ensure_ascii=False),
            offer.scarcity,
            offer.guarantee,
            offer.method_name,
            offer.summary,
            offer.id,
        ),
    )
    conn.commit()


def delete_offer(conn: Connection, offer_id: int) -> None:
    conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    conn.commit()


def _row_to_offer(row) -> Offer:
    return Offer(
        id=row["id"],
        icp_id=row["icp_id"],
        name=row["name"],
        dream=row["dream"],
        success_proofs=json.loads(row["success_proofs"]),
        time_to_result=row["time_to_result"],
        effort_level=row["effort_level"],
        core_promise=row["core_promise"] or "",
        bonuses=json.loads(row["bonuses"] or "[]"),
        scarcity=row["scarcity"] or "",
        guarantee=row["guarantee"] or "",
        method_name=row["method_name"] or "",
        summary=row["summary"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ── Ideas ─────────────────────────────────────────────────────────────────

def save_ideas(conn: Connection, icp_id: int, ideas: list[dict], offer_id: int | None = None) -> None:
    """Salva uma lista de ideias geradas no banco."""
    for idea in ideas:
        conn.execute(
            """INSERT INTO ideas (icp_id, offer_id, topic, hook, angle, target_emotion, carousel_style)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                icp_id,
                offer_id,
                idea.get("topic", ""),
                idea.get("hook", ""),
                idea.get("angle", ""),
                idea.get("target_emotion", ""),
                idea.get("carousel_style", ""),
            ),
        )
    conn.commit()


def list_ideas_by_icp(conn: Connection, icp_id: int, offer_id: int | None = None) -> list[dict]:
    """Lista ideias filtradas por ICP e opcionalmente por oferta."""
    if offer_id:
        rows = conn.execute(
            "SELECT * FROM ideas WHERE icp_id = ? AND offer_id = ? ORDER BY created_at DESC",
            (icp_id, offer_id),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM ideas WHERE icp_id = ? ORDER BY created_at DESC",
            (icp_id,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "topic": r["topic"],
            "hook": r["hook"],
            "angle": r["angle"],
            "target_emotion": r["target_emotion"],
            "carousel_style": r["carousel_style"],
            "offer_id": r["offer_id"],
        }
        for r in rows
    ]


def delete_idea(conn: Connection, idea_id: int) -> None:
    conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    conn.commit()


# ── Instagram Posts ──────────────────────────────────────────────────────

def upsert_post(conn: Connection, post: InstagramPost) -> None:
    conn.execute(
        """INSERT INTO instagram_posts
           (ig_media_id, media_type, caption, permalink, timestamp,
            reach, impressions, engagement, saves, shares,
            comments_count, likes_count, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(ig_media_id) DO UPDATE SET
            reach=excluded.reach, impressions=excluded.impressions,
            engagement=excluded.engagement, saves=excluded.saves,
            shares=excluded.shares, comments_count=excluded.comments_count,
            likes_count=excluded.likes_count, fetched_at=excluded.fetched_at""",
        (
            post.ig_media_id, post.media_type, post.caption, post.permalink,
            post.timestamp, post.reach, post.impressions, post.engagement,
            post.saves, post.shares, post.comments_count, post.likes_count,
            datetime.now(),
        ),
    )
    conn.commit()


def get_top_posts(
    conn: Connection, limit: int = 10, order_by: str = "engagement"
) -> list[InstagramPost]:
    valid_cols = {"engagement", "reach", "impressions", "saves", "shares", "likes_count"}
    col = order_by if order_by in valid_cols else "engagement"
    rows = conn.execute(
        f"SELECT * FROM instagram_posts ORDER BY {col} DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_row_to_post(r) for r in rows]


def get_all_posts(conn: Connection) -> list[InstagramPost]:
    rows = conn.execute(
        "SELECT * FROM instagram_posts ORDER BY timestamp DESC"
    ).fetchall()
    return [_row_to_post(r) for r in rows]


def _row_to_post(row) -> InstagramPost:
    return InstagramPost(
        id=row["id"],
        ig_media_id=row["ig_media_id"],
        media_type=row["media_type"],
        caption=row["caption"] or "",
        permalink=row["permalink"] or "",
        timestamp=row["timestamp"],
        reach=row["reach"],
        impressions=row["impressions"],
        engagement=row["engagement"],
        saves=row["saves"],
        shares=row["shares"],
        comments_count=row["comments_count"],
        likes_count=row["likes_count"],
        fetched_at=row["fetched_at"],
    )


# ── Carousel Projects ───────────────────────────────────────────────────

def create_project(conn: Connection, project: CarouselProject) -> int:
    slides_json = json.dumps(
        [
            {
                "index": s.index,
                "slide_type": s.slide_type,
                "headline": s.headline,
                "body": s.body,
                "image_path": s.image_path,
            }
            for s in project.slides
        ],
        ensure_ascii=False,
    )
    cur = conn.execute(
        """INSERT INTO carousel_projects
           (icp_id, title, status, topic, hook, slides_json, caption,
            hashtags, style_template, design_source, canva_design_id, ig_media_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            project.icp_id, project.title, project.status, project.topic,
            project.hook, slides_json, project.caption, project.hashtags,
            project.style_template, project.design_source,
            project.canva_design_id, project.ig_media_id,
        ),
    )
    conn.commit()
    return cur.lastrowid


def update_project(conn: Connection, project: CarouselProject) -> None:
    slides_json = json.dumps(
        [
            {
                "index": s.index,
                "slide_type": s.slide_type,
                "headline": s.headline,
                "body": s.body,
                "image_path": s.image_path,
            }
            for s in project.slides
        ],
        ensure_ascii=False,
    )
    conn.execute(
        """UPDATE carousel_projects SET
           icp_id=?, title=?, status=?, topic=?, hook=?, slides_json=?,
           caption=?, hashtags=?, style_template=?, design_source=?,
           canva_design_id=?, ig_media_id=?, published_at=?,
           updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (
            project.icp_id, project.title, project.status, project.topic,
            project.hook, slides_json, project.caption, project.hashtags,
            project.style_template, project.design_source,
            project.canva_design_id, project.ig_media_id, project.published_at,
            project.id,
        ),
    )
    conn.commit()


def list_projects(
    conn: Connection, status: str | None = None
) -> list[CarouselProject]:
    if status:
        rows = conn.execute(
            "SELECT * FROM carousel_projects WHERE status=? ORDER BY updated_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM carousel_projects ORDER BY updated_at DESC"
        ).fetchall()
    return [_row_to_project(r) for r in rows]


def get_project(conn: Connection, project_id: int) -> CarouselProject | None:
    row = conn.execute(
        "SELECT * FROM carousel_projects WHERE id=?", (project_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_project(row)


def _row_to_project(row) -> CarouselProject:
    slides_data = json.loads(row["slides_json"] or "[]")
    slides = [
        SlideContent(
            index=s["index"],
            slide_type=s["slide_type"],
            headline=s["headline"],
            body=s["body"],
            image_path=s.get("image_path"),
        )
        for s in slides_data
    ]
    return CarouselProject(
        id=row["id"],
        icp_id=row["icp_id"],
        title=row["title"],
        status=row["status"],
        topic=row["topic"] or "",
        hook=row["hook"] or "",
        slides=slides,
        caption=row["caption"] or "",
        hashtags=row["hashtags"] or "",
        style_template=row["style_template"] or "dark_bold",
        design_source=row["design_source"] or "html",
        canva_design_id=row["canva_design_id"],
        ig_media_id=row["ig_media_id"],
        published_at=row["published_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
