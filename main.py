from log import get_logger
from llm import LLMAgent
from langchain_core.messages import HumanMessage, SystemMessage

import tools

logger = get_logger(__name__)

SYSTEM_PROMPT = """
Sos MachineTwin, un asistente técnico para maquinas. 
Respondés en español, de forma concisa y técnica. 
Si no tenés datos suficientes, especificaciones o documentación técnica, 
utilizá las herramientas disponibles para buscar la información necesaria. 
Si no encontrás información suficiente, indícalo de forma clara.

Al usar la herramienta ejecutar_codigo, las variables machine_current (dict), machine_history (pd.DataFrame) y pd (pandas) ya están disponibles. NO es necesario cargar archivos ni incrustar datos en el código.
"""


TOOLS = {
    "consultar_documentacion": tools.consultar_documentacion,
    "listar_archivos_datos": tools.listar_archivos_datos,
    "leer_archivo_datos": tools.leer_archivo_datos,
    "ejecutar_codigo": tools.ejecutar_codigo,
}


class MachineTwin:
    def __init__(self):
        self._agent = LLMAgent(tools=TOOLS)
        self._history = []

    @property
    def ready(self) -> bool:
        return self._agent.ready

    def process(self, query: str) -> str:
        if not self._agent.ready:
            return "Error: No se configuro la API key (LLM_API_KEY)."

        logger.info(f"Procesando consulta del usuario: '{query}'")
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *self._history,
            HumanMessage(content=query),
        ]

        try:
            response = self._agent.invoke(messages)
            answer = response.content
            logger.info("Respuesta generada exitosamente.")
            self._history.append(HumanMessage(content=query))
            self._history.append(response)
            if len(self._history) > 20:
                self._history = self._history[-20:]
            return answer
        except Exception as e:
            logger.error(f"Error al procesar consulta: {e}")
            return f"Error al consultar el LLM: {e}"

    def clear_history(self):
        self._history.clear()







if __name__ == "__main__":
    import sys
    from uiBase import BaseUI

    twin = MachineTwin()

    def handle_completion(msg: str):
        return twin.process(msg)

    
    from uiTerminal import TUI
    ui: BaseUI = TUI()

    ui.set_on_completion(handle_completion)
    ui.start()





