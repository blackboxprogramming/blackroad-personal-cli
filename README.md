# blackroad-personal-cli

Personal development CLI utilities and shortcuts for Alexa Amundson / BlackRoad OS.

## Installation

```bash
pip install -r requirements.txt
chmod +x personal_cli.py
ln -s $(pwd)/personal_cli.py /usr/local/bin/br-cli
```

## Usage

```bash
# Scaffold a new web project
br-cli init mysite --type web --path ~/projects/mysite

# Scaffold an API project with a git remote
br-cli init myapi --type api --remote git@github.com:blackboxprogramming/myapi.git

# Register an existing project
br-cli register myapp ~/projects/myapp --type cli

# Install dependencies
br-cli setup myapp

# Deploy (git push + optional hook)
br-cli deploy myapp

# Create a backup
br-cli backup myapp

# Pull latest for all projects
br-cli sync

# Show all projects with git status
br-cli status

# List projects
br-cli list

# Configure deploy hook
br-cli config deploy_hook "curl -X POST https://hooks.example.com/deploy"

# Show all config
br-cli config
```

## Project Types

| Type | Templates |
|------|-----------|
| `web` | index.html, style.css, app.js, README |
| `api` | main.py (FastAPI), requirements.txt, README |
| `cli` | main.py (argparse), README |
| `lib` | __init__.py, README |

## Config

Stored in `~/.blackroad-personal/config.json`:

```json
{
  "deploy_hook": "",
  "backup_dir": "~/.blackroad-personal/backups",
  "default_branch": "main",
  "editor": "vim"
}
```

## Data

SQLite registry at `~/.blackroad-personal/projects.db`.

## License

Proprietary — BlackRoad OS, Inc.
