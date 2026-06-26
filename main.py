from log import get_logger
from llm import LLMAgent
from langchain_core.messages import HumanMessage, SystemMessage
from config import SYSTEM_PROMPT_PATH

import tools

logger = get_logger(__name__)

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


TOOLS = {
    "consultar_documentacion": tools.consultar_documentacion,
    "obtener_estado_actual": tools.obtener_estado_actual,
    "consultar_eventos_recientes": tools.consultar_eventos_recientes,
    "analizar_tendencia": tools.analizar_tendencia,
    "listar_archivos_datos": tools.listar_archivos_datos,
    "leer_archivo_datos": tools.leer_archivo_datos,
}


class MachineTwin:
    def __init__(self):
        self._agent = LLMAgent(tools=TOOLS)
        self._histories = {}

    @property
    def ready(self) -> bool:
        return self._agent.ready

    def _get_history(self, conversation_id: str | None):
        key = conversation_id or "default"
        return self._histories.setdefault(key, [])

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
            response = self._agent.invoke(messages)
            answer = response.content
            logger.info("Respuesta generada exitosamente.")
            history.append(HumanMessage(content=query))
            history.append(response)
            if len(history) > 20:
                history[:] = history[-20:]
            return answer
        except Exception as e:
            logger.error(f"Error al procesar consulta: {e}")
            return f"Error al consultar el LLM: {e}"

    def clear_history(self, conversation_id: str | None = None):
        if conversation_id:
            self._histories.pop(conversation_id, None)
        else:
            self._histories.clear()







if __name__ == "__main__":
    import sys

    twin = MachineTwin()

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
    ui.start()
