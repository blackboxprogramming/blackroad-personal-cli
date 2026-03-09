"""BlackRoad Personal CLI — project scaffolding and management."""

import json
import sqlite3
import shutil
import tarfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

CONFIG_DIR = Path.home() / ".br"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_FILE = CONFIG_DIR / "projects.db"

PROJECT_TYPES = ("cli", "web", "lib", "api")

TEMPLATES = {
    "cli": {"main.py": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello from BlackRoad CLI')\n\nif __name__ == '__main__':\n    main()\n",
            "README.md": "# CLI Project\n"},
    "web": {"index.html": "<!DOCTYPE html>\n<html><head><title>BlackRoad</title></head><body></body></html>\n",
            "style.css": "body { margin: 0; font-family: sans-serif; }\n",
            "app.js": "console.log('BlackRoad Web');\n",
            "README.md": "# Web Project\n"},
    "lib": {"__init__.py": "",
            "lib.py": "\"\"\"Library module.\"\"\"\n",
            "README.md": "# Library\n"},
    "api": {"app.py": "from flask import Flask\napp = Flask(__name__)\n",
            "README.md": "# API Project\n"},
}

DEFAULT_CONFIG = {
    "default_branch": "main",
    "deploy_hook": "",
    "backup_dir": str(CONFIG_DIR / "backups"),
}


@dataclass
class LocalProject:
    name: str
    path: str
    type: str


def _ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_db() -> sqlite3.Connection:
    _ensure_dirs()
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS projects "
        "(name TEXT PRIMARY KEY, path TEXT, type TEXT)"
    )
    conn.commit()
    return conn


def load_config() -> dict:
    _ensure_dirs()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    _ensure_dirs()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def save_project(project: LocalProject):
    db = _get_db()
    db.execute(
        "INSERT OR REPLACE INTO projects (name, path, type) VALUES (?, ?, ?)",
        (project.name, project.path, project.type),
    )
    db.commit()
    db.close()


def load_project(name: str) -> Optional[LocalProject]:
    db = _get_db()
    row = db.execute(
        "SELECT name, path, type FROM projects WHERE name = ?", (name,)
    ).fetchone()
    db.close()
    if row:
        return LocalProject(name=row[0], path=row[1], type=row[2])
    return None


def all_projects() -> List[LocalProject]:
    db = _get_db()
    rows = db.execute("SELECT name, path, type FROM projects").fetchall()
    db.close()
    return [LocalProject(name=r[0], path=r[1], type=r[2]) for r in rows]


def cmd_init(args):
    dest = Path(args.path)
    dest.mkdir(parents=True, exist_ok=True)
    template = TEMPLATES.get(args.type, TEMPLATES["cli"])
    for filename, content in template.items():
        (dest / filename).write_text(content)
    project = LocalProject(name=args.name, path=str(dest), type=args.type)
    save_project(project)


def cmd_status(args):
    projects = all_projects()
    if not projects:
        print("No projects found.")
        return
    for p in projects:
        print(f"  {p.name} ({p.type}) @ {p.path}")


def cmd_backup(args):
    project = load_project(args.project)
    if not project:
        print(f"Project '{args.project}' not found.")
        return
    cfg = load_config()
    backup_dir = Path(cfg.get("backup_dir", str(CONFIG_DIR / "backups")))
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = backup_dir / f"{project.name}_{ts}.tar.gz"
    with tarfile.open(str(archive), "w:gz") as tar:
        tar.add(project.path, arcname=project.name)


def cmd_remove(args):
    db = _get_db()
    db.execute("DELETE FROM projects WHERE name = ?", (args.name,))
    db.commit()
    db.close()
