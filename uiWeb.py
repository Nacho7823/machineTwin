import os
from pathlib import Path

import fastapi
import uvicorn
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from uiBase import BaseUI

DIST_DIR = Path(__file__).parent / "frontend" / "dist"


class WebUI(BaseUI):
    def __init__(self):
        super().__init__()

    def start(self):
        self.app = create_app(self)
        uvicorn.run(self.app, host="0.0.0.0", port=8000)


def create_app(ui: WebUI = None):
    app = fastapi.FastAPI(title="Machine Chat API", version="1.0.0")

    @app.get("/api/completion")
    async def get_completion(msg: str, conversation_id: str | None = None):
        if ui and ui.onCompletition:
            return {"completion": ui.onCompletition(msg, conversation_id)}
        return {"completion": f"Generated completion for the given prompt: {msg}"}

    @app.post("/api/clear")
    async def clear_history(payload: dict | None = fastapi.Body(default=None)):
        if ui and ui.onClearHistory:
            conversation_id = payload.get("conversation_id") if payload else None
            ui.onClearHistory(conversation_id)
        return {"ok": True}

    if DIST_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = DIST_DIR / full_path
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(DIST_DIR / "index.html"))

    return app
