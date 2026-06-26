import importlib
import sys
import types
import unittest
from unittest.mock import patch


class _Message:
    def __init__(self, content):
        self.content = content


class _Logger:
    def info(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


class _RecordingAgent:
    ready = True

    def __init__(self):
        self.calls = []

    def invoke(self, messages):
        self.calls.append([message.content for message in messages])
        return _Message(f"respuesta a {messages[-1].content}")


class MachineTwinConversationHistoryTests(unittest.TestCase):
    def _load_main_with_fakes(self):
        self.addCleanup(lambda: sys.modules.pop("main", None))
        fake_tools = types.SimpleNamespace(
            consultar_documentacion=object(),
            obtener_estado_actual=object(),
            consultar_eventos_recientes=object(),
            detectar_fuera_de_limites=object(),
            analizar_tendencia=object(),
            listar_archivos_datos=object(),
            leer_archivo_datos=object(),
        )
        fake_modules = {
            "tools": fake_tools,
            "llm": types.SimpleNamespace(LLMAgent=lambda tools: _RecordingAgent()),
            "log": types.SimpleNamespace(get_logger=lambda _name: _Logger()),
            "langchain_core.messages": types.SimpleNamespace(
                HumanMessage=_Message,
                SystemMessage=_Message,
            ),
        }
        with patch.dict(sys.modules, fake_modules):
            sys.modules.pop("main", None)
            return importlib.import_module("main")

    def test_process_keeps_histories_isolated_by_conversation_id(self):
        main = self._load_main_with_fakes()
        twin = main.MachineTwin()

        twin.process("primer chat", conversation_id="chat-a")
        twin.process("otro chat", conversation_id="chat-b")
        twin.process("seguimiento", conversation_id="chat-a")

        self.assertIn("primer chat", twin._agent.calls[2])
        self.assertIn("respuesta a primer chat", twin._agent.calls[2])
        self.assertIn("seguimiento", twin._agent.calls[2])
        self.assertNotIn("otro chat", twin._agent.calls[2])

    def test_clear_history_can_clear_one_conversation_without_touching_others(self):
        main = self._load_main_with_fakes()
        twin = main.MachineTwin()

        twin.process("chat a", conversation_id="chat-a")
        twin.process("chat b", conversation_id="chat-b")
        twin.clear_history(conversation_id="chat-a")
        twin.process("sigue b", conversation_id="chat-b")

        self.assertIn("chat b", twin._agent.calls[-1])
        self.assertIn("respuesta a chat b", twin._agent.calls[-1])
        self.assertNotIn("chat a", twin._agent.calls[-1])


if __name__ == "__main__":
    unittest.main()
