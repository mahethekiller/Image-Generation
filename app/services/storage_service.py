import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.config import DATA_DIR, OUTPUTS_DIR

DB_PATH = DATA_DIR / "history.db"

def init_db():
    """Initialize SQLite database for generation history."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt TEXT NOT NULL,
                negative_prompt TEXT,
                mode TEXT NOT NULL,
                aspect_ratio TEXT,
                image_filename TEXT NOT NULL,
                transparent_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

def save_generation(
    provider: str,
    model: str,
    prompt: str,
    negative_prompt: Optional[str],
    mode: str,
    aspect_ratio: str,
    image_bytes: bytes,
    extension: str = "png"
) -> Dict[str, Any]:
    """Saves the generated image to static/outputs and records it in SQLite."""
    gen_id = str(uuid.uuid4())
    filename = f"{gen_id}.{extension}"
    file_path = OUTPUTS_DIR / filename

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO generations 
            (id, provider, model, prompt, negative_prompt, mode, aspect_ratio, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (gen_id, provider, model, prompt, negative_prompt, mode, aspect_ratio, filename))
        conn.commit()

    return get_generation(gen_id)

def update_transparent_version(gen_id: str, transparent_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Saves transparent PNG version for game sprites."""
    transparent_filename = f"{gen_id}_transparent.png"
    file_path = OUTPUTS_DIR / transparent_filename

    with open(file_path, "wb") as f:
        f.write(transparent_bytes)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE generations 
            SET transparent_filename = ?
            WHERE id = ?
        """, (transparent_filename, gen_id))
        conn.commit()

    return get_generation(gen_id)

def get_generation(gen_id: str) -> Optional[Dict[str, Any]]:
    """Fetch single generation by ID."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM generations WHERE id = ?", (gen_id,))
        row = cursor.fetchone()
        if not row:
            return None
        item = dict(row)
        item["image_url"] = f"/static/outputs/{item['image_filename']}"
        item["transparent_url"] = f"/static/outputs/{item['transparent_filename']}" if item["transparent_filename"] else None
        return item

def get_recent_generations(limit: int = 40) -> List[Dict[str, Any]]:
    """List recent generations ordered by creation date."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM generations ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        items = []
        for r in rows:
            item = dict(r)
            item["image_url"] = f"/static/outputs/{item['image_filename']}"
            item["transparent_url"] = f"/static/outputs/{item['transparent_filename']}" if item["transparent_filename"] else None
            items.append(item)
        return items
