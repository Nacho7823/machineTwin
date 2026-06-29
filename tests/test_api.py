from fastapi.testclient import TestClient

from uiWeb import create_app


class FakeUI:
    def __init__(self):
        self.onCompletition = None
        self.onClearHistory = None
        self.onListConversations = lambda: [
            {
                "conversation_id": "chat-1",
                "title": "Estado",
                "message_count": 2,
                "created_at": "2026-06-29T00:00:00+00:00",
                "updated_at": "2026-06-29T00:01:00+00:00",
            }
        ]
        self.onListTraces = lambda limit=100, conversation_id=None: [
            {
                "conversation_id": conversation_id or "chat-1",
                "event": "tool_call",
                "tool": "obtener_estado_actual",
            }
        ]
        self.onGetConversationTrace = lambda conversation_id: {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": "Estado?", "created_at": "2026-06-29T00:00:00+00:00"}],
            "traces": [{"event": "tool_call", "tool": "obtener_estado_actual"}],
        }


def test_trace_api_returns_conversations_and_detail():
    client = TestClient(create_app(FakeUI()))

    conversations = client.get("/api/conversations").json()
    detail = client.get("/api/traces/chat-1").json()
    traces = client.get("/api/traces?conversation_id=chat-1").json()

    assert conversations["conversations"][0]["conversation_id"] == "chat-1"
    assert detail["messages"][0]["content"] == "Estado?"
    assert traces["traces"][0]["tool"] == "obtener_estado_actual"
