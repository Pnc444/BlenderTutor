# BlenderTutor

Fork of [ScreenReaderAI](https://github.com/Pnc444/ScreenReaderAI) — same core (side panel + screen capture + vision AI), with **Blender MCP** integration added on this branch of the product.


## Blender-specific (this repo) Changed From ScreenReaderAI to change project to be more blender oriented

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

## Build Windows EXE

```powershell
venv\Scripts\activate
.\build.ps1
```

Output: `dist\BlenderTutor.exe`

