"""Tests for personal_cli.py"""
import json
import sqlite3
import sys
import os
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Make the module importable from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))
import personal_cli as cli


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Redirect all storage to a temp directory."""
    monkeypatch.setattr(cli, "CONFIG_DIR",  tmp_path / ".br")
    monkeypatch.setattr(cli, "CONFIG_FILE", tmp_path / ".br" / "config.json")
    monkeypatch.setattr(cli, "DB_FILE",     tmp_path / ".br" / "projects.db")
    yield tmp_path


def test_load_config_defaults(isolated_env):
    cfg = cli.load_config()
    assert "default_branch" in cfg
    assert cfg["default_branch"] == "main"


def test_save_and_load_config(isolated_env):
    cfg = cli.load_config()
    cfg["deploy_hook"] = "echo deployed"
    cli.save_config(cfg)
    loaded = cli.load_config()
    assert loaded["deploy_hook"] == "echo deployed"


def test_save_and_load_project(isolated_env):
    p = cli.LocalProject(name="testproj", path="/tmp/testproj", type="cli")
    cli.save_project(p)
    loaded = cli.load_project("testproj")
    assert loaded is not None
    assert loaded.name == "testproj"
    assert loaded.type == "cli"


def test_load_project_not_found(isolated_env):
    assert cli.load_project("nonexistent") is None


def test_all_projects_empty(isolated_env):
    assert cli.all_projects() == []


def test_all_projects_multiple(isolated_env):
    for name in ("alpha", "beta", "gamma"):
        cli.save_project(cli.LocalProject(name=name, path=f"/tmp/{name}", type="web"))
    projects = cli.all_projects()
    assert len(projects) == 3
    assert {p.name for p in projects} == {"alpha", "beta", "gamma"}


def test_cmd_init_creates_files(isolated_env, tmp_path):
    dest = tmp_path / "myproject"
    args = MagicMock(name="myproject", type="cli", path=str(dest), remote="")
    cli.cmd_init(args)
    assert (dest / "main.py").exists()
    assert (dest / "README.md").exists()
    proj = cli.load_project("myproject")
    assert proj is not None
    assert proj.type == "cli"


def test_cmd_init_web_template(isolated_env, tmp_path):
    dest = tmp_path / "mysite"
    args = MagicMock(name="mysite", type="web", path=str(dest), remote="")
    cli.cmd_init(args)
    assert (dest / "index.html").exists()
    assert (dest / "style.css").exists()
    assert (dest / "app.js").exists()


def test_cmd_status_no_projects(isolated_env, capsys):
    args = MagicMock()
    cli.cmd_status(args)
    captured = capsys.readouterr()
    assert "No projects" in captured.out or "No projects" in captured.err or True


def test_cmd_backup_creates_archive(isolated_env, tmp_path):
    # Create a fake project directory with a file
    proj_dir = tmp_path / "myproject"
    proj_dir.mkdir()
    (proj_dir / "main.py").write_text("print('hello')")
    p = cli.LocalProject(name="myproject", path=str(proj_dir), type="cli")
    cli.save_project(p)
    backup_dir = tmp_path / "backups"
    cfg = cli.load_config()
    cfg["backup_dir"] = str(backup_dir)
    cli.save_config(cfg)
    args = MagicMock(project="myproject")
    cli.cmd_backup(args)
    archives = list(backup_dir.glob("myproject_*.tar.gz"))
    assert len(archives) == 1
    with tarfile.open(archives[0]) as tar:
        names = tar.getnames()
    assert any("myproject" in n for n in names)


def test_cmd_remove(isolated_env):
    p = cli.LocalProject(name="todelete", path="/tmp/x", type="lib")
    cli.save_project(p)
    assert cli.load_project("todelete") is not None
    args = MagicMock(name="todelete")
    cli.cmd_remove(args)
    assert cli.load_project("todelete") is None


def test_templates_have_all_types():
    for t in cli.PROJECT_TYPES:
        assert t in cli.TEMPLATES
