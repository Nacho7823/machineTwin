import os
from pathlib import Path

import fastapi
import uvicorn
import config
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from uiBase import BaseUI

DIST_DIR = Path(__file__).parent / "frontend" / "dist"


class WebUI(BaseUI):
    def __init__(self):
        super().__init__()

    def start(self):
        self.app = create_app(self)
        uvicorn.run(self.app, host=config.WEB_HOST, port=config.WEB_PORT)


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

    @app.get("/api/conversations")
    async def list_conversations():
        if ui and ui.onListConversations:
            return {"conversations": ui.onListConversations()}
        return {"conversations": []}

    @app.post("/api/conversations")
    async def ensure_conversation(payload: dict = fastapi.Body(default=None)):
        conversation_id = (payload or {}).get("conversation_id")
        title = (payload or {}).get("title")
        if not conversation_id:
            raise fastapi.HTTPException(status_code=400, detail="conversation_id requerido")
        if ui and ui.onEnsureConversation:
            ui.onEnsureConversation(conversation_id, title)
        return {"ok": True}

    @app.get("/api/conversations/{conversation_id}")
    async def get_conversation(conversation_id: str):
        if ui and ui.onGetConversation:
            return ui.onGetConversation(conversation_id)
        return {"conversation_id": conversation_id, "messages": []}

    @app.delete("/api/conversations/{conversation_id}")
    async def delete_conversation(conversation_id: str):
        if ui and ui.onDeleteConversation:
            ui.onDeleteConversation(conversation_id)
        return {"ok": True}

    @app.get("/api/traces")
    async def list_traces(limit: int = 100, conversation_id: str | None = None):
        if ui and ui.onListTraces:
            return {"traces": ui.onListTraces(limit=limit, conversation_id=conversation_id)}
        return {"traces": []}

    @app.get("/api/traces/{conversation_id}")
    async def get_conversation_trace(conversation_id: str):
        if ui and ui.onGetConversationTrace:
            return ui.onGetConversationTrace(conversation_id)
        return {"conversation_id": conversation_id, "messages": [], "traces": []}

    if DIST_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = DIST_DIR / full_path
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(DIST_DIR / "index.html"))

    return app
