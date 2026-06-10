import sqlite3
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("/home/kafka/projects/rule-scribe-games/data/games.db")

def get_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Mirroring Supabase games schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE,
        title TEXT,
        title_ja TEXT,
        summary TEXT,
        description TEXT,
        rules_content TEXT,
        min_players INTEGER,
        max_players INTEGER,
        play_time INTEGER,
        min_age INTEGER,
        published_year INTEGER,
        image_url TEXT,
        strategy_tier TEXT,
        structured_data TEXT, -- JSON string
        infographics TEXT,    -- JSON string
        view_count INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def upsert_game(game_data: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    
    # Extract structured_data and infographics as JSON strings
    sd = game_data.get("structured_data", {})
    if isinstance(sd, dict):
        sd = json.dumps(sd, ensure_ascii=False)
        
    info = game_data.get("infographics")
    if isinstance(info, dict):
        info = json.dumps(info, ensure_ascii=False)
    
    fields = [
        game_data.get("id"), game_data.get("slug"), game_data.get("title"),
        game_data.get("title_ja"), game_data.get("summary"), game_data.get("description"),
        game_data.get("rules_content"), game_data.get("min_players"), game_data.get("max_players"),
        game_data.get("play_time"), game_data.get("min_age"), game_data.get("published_year"),
        game_data.get("image_url"), game_data.get("strategy_tier"), sd, info,
        game_data.get("created_at"), game_data.get("updated_at")
    ]
    
    cursor.execute("""
    INSERT INTO games (
        id, slug, title, title_ja, summary, description, rules_content,
        min_players, max_players, play_time, min_age, published_year,
        image_url, strategy_tier, structured_data, infographics, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(slug) DO UPDATE SET
        title=excluded.title,
        title_ja=excluded.title_ja,
        summary=excluded.summary,
        description=excluded.description,
        rules_content=excluded.rules_content,
        min_players=excluded.min_players,
        max_players=excluded.max_players,
        play_time=excluded.play_time,
        min_age=excluded.min_age,
        published_year=excluded.published_year,
        image_url=excluded.image_url,
        strategy_tier=excluded.strategy_tier,
        structured_data=excluded.structured_data,
        infographics=excluded.infographics,
        updated_at=excluded.updated_at
    """, fields)
    
    conn.commit()
    conn.close()

def list_recent(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    
    # Get data
    cursor.execute(f"SELECT * FROM games ORDER BY updated_at DESC LIMIT {limit} OFFSET {offset}")
    rows = cursor.fetchall()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM games")
    total = cursor.fetchone()[0]
    
    games = []
    for row in rows:
        g = dict(row)
        if g.get("structured_data"):
            g["structured_data"] = json.loads(g["structured_data"])
        if g.get("infographics"):
            g["infographics"] = json.loads(g["infographics"])
        games.append(g)
        
    conn.close()
    return {"data": games, "total": total}

def get_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        g = dict(row)
        if g.get("structured_data"):
            g["structured_data"] = json.loads(g["structured_data"])
        if g.get("infographics"):
            g["infographics"] = json.loads(g["infographics"])
        return g
    return None

if __name__ == "__main__":
    init_db()
    print("Local SQLite Initialized at", DB_PATH)
