from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    from langchain_core.messages import AIMessage, HumanMessage
except ModuleNotFoundError:
    @dataclass
    class HumanMessage:
        content: str
        type: str = "human"

    @dataclass
    class AIMessage:
        content: str
        type: str = "ai"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _message_from_row(role: str, content: str):
    if role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


class InMemoryPersistence:
    def __init__(self):
        self._messages: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._traces: list[dict[str, Any]] = []

    def save_message(self, conversation_id: str, role: str, content: str):
        self.ensure_conversation(conversation_id, content if role == "user" else None)
        self._messages[conversation_id].append({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": _now_iso(),
        })

    def load_messages(self, conversation_id: str):
        return [
            _message_from_row(message["role"], message["content"])
            for message in self._messages.get(conversation_id, [])
        ]

    def clear_conversation(self, conversation_id: str | None = None):
        if conversation_id:
            self._messages.pop(conversation_id, None)
            self._traces = [t for t in self._traces if t.get("conversation_id") != conversation_id]
            self.record_trace_event({"conversation_id": conversation_id, "event": "conversation_cleared"})
            return
        self._messages.clear()
        self._traces.clear()
        self.record_trace_event({"event": "all_conversations_cleared"})

    def ensure_conversation(self, conversation_id: str, title: str | None = None):
        if conversation_id not in self._messages:
            self._messages[conversation_id] = []

    def record_trace_event(self, payload: dict):
        event = dict(payload)
        event.setdefault("timestamp", _now_iso())
        conversation_id = event.get("conversation_id")
        if conversation_id:
            self.ensure_conversation(conversation_id)
        self._traces.append(event)

    def list_conversations(self) -> list[dict[str, Any]]:
        conversations = []
        for conversation_id, messages in self._messages.items():
            if not messages:
                continue
            first_user = next((m["content"] for m in messages if m["role"] == "user"), "Conversacion")
            conversations.append({
                "conversation_id": conversation_id,
                "title": first_user[:60],
                "message_count": len(messages),
                "created_at": messages[0]["created_at"],
                "updated_at": messages[-1]["created_at"],
            })
        return sorted(conversations, key=lambda row: row["updated_at"], reverse=True)

    def list_traces(self, limit: int = 100, conversation_id: str | None = None) -> list[dict[str, Any]]:
        traces = self._traces
        if conversation_id:
            traces = [trace for trace in traces if trace.get("conversation_id") == conversation_id]
        return traces[-limit:]

    def get_conversation_trace(self, conversation_id: str) -> dict[str, Any]:
        messages = [
            {
                "role": message["role"],
                "content": message["content"],
                "created_at": message["created_at"],
            }
            for message in self._messages.get(conversation_id, [])
        ]
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "traces": self.list_traces(conversation_id=conversation_id),
        }

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        detail = self.get_conversation_trace(conversation_id)
        return {
            "conversation_id": conversation_id,
            "messages": detail["messages"],
        }

    def delete_conversation(self, conversation_id: str):
        self._messages.pop(conversation_id, None)
        self._traces = [t for t in self._traces if t.get("conversation_id") != conversation_id]


class PostgresPersistence:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._verify_schema()

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def _verify_schema(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('schema_migrations', 'conversations', 'conversation_messages', 'trace_events')
                """
            ).fetchall()
        found = {row[0] for row in rows}
        required = {"schema_migrations", "conversations", "conversation_messages", "trace_events"}
        missing = required - found
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise RuntimeError(
                "Faltan tablas de PostgreSQL. Ejecuta `python -m db migrate` antes de iniciar la app. "
                f"Tablas faltantes: {missing_list}"
            )

    def _touch_conversation(self, conn, conversation_id: str, title: str = "Conversacion"):
        conn.execute(
            """
            INSERT INTO conversations (conversation_id, title)
            VALUES (%s, %s)
            ON CONFLICT (conversation_id)
            DO UPDATE SET
                updated_at = now(),
                title = CASE
                    WHEN conversations.title = 'Conversacion' AND EXCLUDED.title <> 'Conversacion'
                    THEN EXCLUDED.title
                    ELSE conversations.title
                END
            """,
            (conversation_id, title[:80] or "Conversacion"),
        )

    def ensure_conversation(self, conversation_id: str, title: str | None = None):
        with self._connect() as conn:
            self._touch_conversation(conn, conversation_id, title or "Conversacion")

    def save_message(self, conversation_id: str, role: str, content: str):
        title = content if role == "user" else "Conversacion"
        with self._connect() as conn:
            self._touch_conversation(conn, conversation_id, title)
            conn.execute(
                """
                INSERT INTO conversation_messages (conversation_id, role, content)
                VALUES (%s, %s, %s)
                """,
                (conversation_id, role, content),
            )

    def load_messages(self, conversation_id: str):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY id ASC
                """,
                (conversation_id,),
            ).fetchall()
        return [_message_from_row(role, content) for role, content in rows]

    def clear_conversation(self, conversation_id: str | None = None):
        import psycopg.types.json

        with self._connect() as conn:
            if conversation_id:
                conn.execute(
                    """
                    INSERT INTO trace_events (conversation_id, event, payload)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        conversation_id,
                        "conversation_cleared",
                        psycopg.types.json.Jsonb({"conversation_id": conversation_id, "event": "conversation_cleared"}),
                    ),
                )
                conn.execute("DELETE FROM conversation_messages WHERE conversation_id = %s", (conversation_id,))
                conn.execute("UPDATE conversations SET title = 'Conversacion limpia', updated_at = now() WHERE conversation_id = %s", (conversation_id,))
            else:
                conn.execute(
                    """
                    INSERT INTO trace_events (event, payload)
                    VALUES (%s, %s)
                    """,
                    ("all_conversations_cleared", psycopg.types.json.Jsonb({"event": "all_conversations_cleared"})),
                )
                conn.execute("DELETE FROM conversation_messages")
                conn.execute("UPDATE conversations SET title = 'Conversacion limpia', updated_at = now()")

    def delete_conversation(self, conversation_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM trace_events WHERE conversation_id = %s", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE conversation_id = %s", (conversation_id,))

    def record_trace_event(self, payload: dict):
        import psycopg.types.json

        event = dict(payload)
        event.setdefault("timestamp", _now_iso())
        with self._connect() as conn:
            conversation_id = event.get("conversation_id")
            if conversation_id:
                self._touch_conversation(conn, conversation_id)
            conn.execute(
                """
                INSERT INTO trace_events (conversation_id, trace_id, event, step, tool, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    event.get("trace_id"),
                    event.get("event", "unknown"),
                    event.get("step"),
                    event.get("tool"),
                    psycopg.types.json.Jsonb(event),
                ),
            )

    def list_conversations(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.conversation_id, c.title, c.created_at, c.updated_at, count(m.id) AS message_count
                FROM conversations c
                LEFT JOIN conversation_messages m ON m.conversation_id = c.conversation_id
                WHERE c.deleted_at IS NULL
                GROUP BY c.conversation_id, c.title, c.created_at, c.updated_at
                ORDER BY c.updated_at DESC
                LIMIT 100
                """
            ).fetchall()
        return [
            {
                "conversation_id": conversation_id,
                "title": title,
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
                "message_count": message_count,
            }
            for conversation_id, title, created_at, updated_at, message_count in rows
        ]

    def list_traces(self, limit: int = 100, conversation_id: str | None = None) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        params: list[Any] = []
        where = ""
        if conversation_id:
            where = "WHERE conversation_id = %s"
            params.append(conversation_id)
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT payload, created_at
                FROM trace_events
                {where}
                ORDER BY id DESC
                LIMIT %s
                """,
                params,
            ).fetchall()
        traces = []
        for payload, created_at in rows:
            event = dict(payload)
            event.setdefault("timestamp", created_at.isoformat())
            traces.append(event)
        return list(reversed(traces))

    def get_conversation_trace(self, conversation_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            message_rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY id ASC
                """,
                (conversation_id,),
            ).fetchall()
        messages = [
            {"role": role, "content": content, "created_at": created_at.isoformat()}
            for role, content, created_at in message_rows
        ]
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "traces": self.list_traces(conversation_id=conversation_id),
        }

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            message_rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY id ASC
                """,
                (conversation_id,),
            ).fetchall()
        return {
            "conversation_id": conversation_id,
            "messages": [
                {"role": role, "content": content, "created_at": created_at.isoformat()}
                for role, content, created_at in message_rows
            ],
        }


def create_persistence(database_url: str | None):
    if database_url:
        return PostgresPersistence(database_url)
    return InMemoryPersistence()
