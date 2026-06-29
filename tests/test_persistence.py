from persistence import InMemoryPersistence


def test_persistence_stores_conversation_messages_and_trace_events():
    store = InMemoryPersistence()

    store.save_message("chat-1", "user", "Estado actual?")
    store.save_message("chat-1", "assistant", "Todo operativo.")
    store.record_trace_event(
        {
            "conversation_id": "chat-1",
            "trace_id": "trace-1",
            "event": "tool_call",
            "tool": "obtener_estado_actual",
            "input": {},
            "output": "Maquina: T-100",
            "timestamp": "2026-06-29T00:00:00+00:00",
        }
    )

    conversations = store.list_conversations()
    assert conversations[0]["conversation_id"] == "chat-1"
    assert conversations[0]["message_count"] == 2

    messages = store.load_messages("chat-1")
    assert messages[0].type == "human"
    assert messages[1].type == "ai"
    assert messages[1].content == "Todo operativo."

    detail = store.get_conversation_trace("chat-1")
    assert detail["conversation_id"] == "chat-1"
    assert detail["messages"][0]["content"] == "Estado actual?"
    assert detail["traces"][0]["tool"] == "obtener_estado_actual"


def test_persistence_can_clear_one_conversation_without_clearing_others():
    store = InMemoryPersistence()
    store.save_message("chat-1", "user", "uno")
    store.save_message("chat-2", "user", "dos")

    store.clear_conversation("chat-1")

    assert store.load_messages("chat-1") == []
    assert store.load_messages("chat-2")[0].content == "dos"
