from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import config

_connection: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        db_path = Path(config.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS icps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            niche TEXT NOT NULL,
            demographics TEXT NOT NULL,
            pain_points TEXT NOT NULL,
            desires TEXT NOT NULL,
            objections TEXT NOT NULL,
            language_style TEXT NOT NULL,
            tone_keywords TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS instagram_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ig_media_id TEXT UNIQUE NOT NULL,
            media_type TEXT NOT NULL,
            caption TEXT,
            permalink TEXT,
            timestamp TIMESTAMP,
            reach INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            engagement INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS carousel_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icp_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            topic TEXT,
            hook TEXT,
            slides_json TEXT,
            caption TEXT,
            hashtags TEXT,
            style_template TEXT DEFAULT 'dark_bold',
            design_source TEXT DEFAULT 'html',
            canva_design_id TEXT,
            ig_media_id TEXT,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (icp_id) REFERENCES icps(id)
        );

        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            access_token TEXT NOT NULL,
            token_type TEXT,
            expires_at TIMESTAMP,
            refresh_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icp_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dream TEXT NOT NULL,
            success_proofs TEXT NOT NULL,
            time_to_result TEXT NOT NULL,
            effort_level TEXT NOT NULL,
            core_promise TEXT DEFAULT '',
            bonuses TEXT DEFAULT '[]',
            scarcity TEXT DEFAULT '',
            guarantee TEXT DEFAULT '',
            method_name TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (icp_id) REFERENCES icps(id)
        );

        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icp_id INTEGER NOT NULL,
            offer_id INTEGER,
            topic TEXT NOT NULL,
            hook TEXT NOT NULL,
            angle TEXT DEFAULT '',
            target_emotion TEXT DEFAULT '',
            carousel_style TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (icp_id) REFERENCES icps(id),
            FOREIGN KEY (offer_id) REFERENCES offers(id)
        );

        CREATE INDEX IF NOT EXISTS idx_ideas_icp ON ideas(icp_id);
        CREATE INDEX IF NOT EXISTS idx_ideas_offer ON ideas(offer_id);
        CREATE INDEX IF NOT EXISTS idx_offers_icp ON offers(icp_id);

        CREATE INDEX IF NOT EXISTS idx_posts_engagement ON instagram_posts(engagement DESC);
        CREATE INDEX IF NOT EXISTS idx_posts_reach ON instagram_posts(reach DESC);
        CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON instagram_posts(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_projects_status ON carousel_projects(status);
        CREATE INDEX IF NOT EXISTS idx_projects_icp ON carousel_projects(icp_id);
    """)
    conn.commit()
