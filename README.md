# BlenderTutor

Fork of [ScreenReaderAI](https://github.com/Pnc444/ScreenReaderAI) — same core (side panel + screen capture + vision AI), with **Blender MCP** integration added on this branch of the product.

| Repo | Focus |
|------|--------|
| **ScreenReaderAI** | General desktop screen assistant |
| **BlenderTutor** (this repo) | Same panel + screen help, plus live Blender demos via MCP (coming next) |

## Shared core (today)

- CustomTkinter side panel (`gui.py`)
- Screen capture + dedup (`screen.py`, `dedup.py`, `watch_loop.py`)
- Anthropic or Ollama vision (`ai.py`)

## Blender-specific (this repo)

- [`.cursor/mcp.json`](.cursor/mcp.json) — Cursor MCP bridge (`uvx --python 3.12 blender-mcp`)
- Blender addon: [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — install `addon.py`, connect on port 9876
- **Planned:** `tutor.py`, Blender mode in the app (MCP from Python, not only Cursor)

## Setup

```powershell
git clone <your-blender-tutor-repo-url>
cd BlenderTutor
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install "anthropic[mcp]"
copy .env.example .env
# Add ANTHROPIC_API_KEY to .env
python main.py
```

## Blender MCP smoke test (Cursor)

1. Blender open → BlenderMCP sidebar → **Connect** (9876)
2. Open this folder in Cursor → reload → **Settings → MCP** → `blender` connected
3. Agent chat: *"Using Blender MCP, add a cube."*

## Build Windows EXE

```powershell
venv\Scripts\activate
.\build.ps1
```

Output: `dist\BlenderTutor.exe`


