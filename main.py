from pathlib import Path
from log import get_logger, set_trace_recorder
from llm import LLMAgent
from langchain_core.messages import HumanMessage, SystemMessage
from config import SYSTEM_PROMPT_PATH, DATA_DIR, DOCS_DIR, DATABASE_URL
from persistence import create_persistence

import tools

logger = get_logger(__name__)

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


class MachineTwin:
    def __init__(self, data_dir=None, docs_dir=None):
        data_path = Path(data_dir) if data_dir else DATA_DIR
        docs_path = Path(docs_dir) if docs_dir else DOCS_DIR
        self.tools_manager = tools.TwinTools(data_path, docs_path)
        self._agent = LLMAgent(tools=self.tools_manager.get_tools())
        self._histories = {}
        self.persistence = create_persistence(DATABASE_URL)
        set_trace_recorder(self.persistence.record_trace_event)

    @property
    def ready(self) -> bool:
        return self._agent.ready

    def _get_history(self, conversation_id: str | None):
        key = conversation_id or "default"
        if key not in self._histories:
            self._histories[key] = self.persistence.load_messages(key)
        return self._histories[key]

    def process(self, query: str, conversation_id: str | None = None) -> str:
        if not self._agent.ready:
            return "Error: No se configuro la API key (LLM_API_KEY)."

        logger.info(f"Procesando consulta del usuario: '{query}'")
        history = self._get_history(conversation_id)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *history,
            HumanMessage(content=query),
        ]

        try:
            response = self._agent.invoke(messages, conversation_id=conversation_id or "default")
            answer = response.content
            logger.info("Respuesta generada exitosamente.")
            history.append(HumanMessage(content=query))
            history.append(response)
            self.persistence.save_message(conversation_id or "default", "user", query)
            self.persistence.save_message(conversation_id or "default", "assistant", answer)
            # if len(history) > 20:
            #     history[:] = history[-20:]
            return answer
        except Exception as e:
            logger.error(f"Error al procesar consulta: {e}")
            return f"Error al consultar el LLM: {e}"

    def clear_history(self, conversation_id: str | None = None):
        if conversation_id:
            self._histories.pop(conversation_id, None)
            self.persistence.clear_conversation(conversation_id)
        else:
            self._histories.clear()
            self.persistence.clear_conversation()

    def ensure_conversation(self, conversation_id: str, title: str | None = None):
        self.persistence.ensure_conversation(conversation_id, title)
        self._histories.setdefault(conversation_id, self.persistence.load_messages(conversation_id))

    def list_conversations(self):
        return self.persistence.list_conversations()

    def get_conversation(self, conversation_id: str):
        return self.persistence.get_conversation(conversation_id)

    def delete_conversation(self, conversation_id: str):
        self._histories.pop(conversation_id, None)
        return self.persistence.delete_conversation(conversation_id)

    def list_traces(self, limit: int = 100, conversation_id: str | None = None):
        return self.persistence.list_traces(limit=limit, conversation_id=conversation_id)

    def get_conversation_trace(self, conversation_id: str):
        return self.persistence.get_conversation_trace(conversation_id)







if __name__ == "__main__":
    import sys

    twin = MachineTwin(DATA_DIR, DOCS_DIR)

    def handle_completion(msg: str, conversation_id: str | None = None):
        return twin.process(msg, conversation_id=conversation_id)

    mode = sys.argv[1] if len(sys.argv) > 1 else "terminal"

    from uiBase import BaseUI
    if mode == "web":
        from uiWeb import WebUI
        ui: BaseUI = WebUI()
    else:
        from uiTerminal import TUI
        ui: BaseUI = TUI()

    ui.set_on_completion(handle_completion)
    ui.set_on_clear_history(twin.clear_history)
    ui.set_on_ensure_conversation(twin.ensure_conversation)
    ui.set_on_list_conversations(twin.list_conversations)
    ui.set_on_get_conversation(twin.get_conversation)
    ui.set_on_delete_conversation(twin.delete_conversation)
    ui.set_on_list_traces(twin.list_traces)
    ui.set_on_get_conversation_trace(twin.get_conversation_trace)
    ui.start()
