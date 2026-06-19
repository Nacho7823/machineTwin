import curses
from log import get_logger
from ui import ChatUI, HELP_MSG
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


def main(stdscr):
    ui = ChatUI(stdscr)
    ui.start()
    bot = MachineTwin()
    ui.set_status(bot.ready, True)

    while True:
        ui.draw()
        event = ui.get_event()
        if event is None:
            continue
        kind, data = event

        if kind == "quit":
            break
        elif kind == "clear":
            bot.clear_history()
            ui.chat_history.clear()
            ui.add_message("bot", "Chat limpiado.")
        elif kind == "help":
            ui.add_message("bot", HELP_MSG)
        elif kind in ("message", "command"):
            ui.add_message("user", data)
            ui.set_thinking(True)
            ui.draw()
            response = bot.process(data)
            ui.set_thinking(False)
            ui.add_message("bot", response)


if __name__ == "__main__":
    curses.wrapper(main)
