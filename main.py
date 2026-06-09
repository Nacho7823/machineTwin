import curses
from log import get_logger
from ui import ChatUI, HELP_MSG
from config import DATA_DIR, DOCS_DIR, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

import tools

logger = get_logger(__name__)


# SYSTEM_PROMPT = (
#     "Sos MachineTwin, un asistente técnico para la Torre de Enfriamiento T-100. "
#     "Respondés en español, de forma concisa y técnica. "
#     "Si no tenés datos suficientes o te consultan sobre el TP2, especificaciones o documentación técnica, "
#     "utilizá la herramienta 'consultar_documentacion' para buscar en los documentos. "
#     "Si no encontrás información suficiente, indícalo de forma clara."
# )
SYSTEM_PROMPT = (
    "Sos un asistente"
    "Respondés en español, de forma concisa y técnica. "
)


class MachineTwin:
    def __init__(self):

        self.rag = tools.rag
        self.agent = None
        self._history = []
        self._init_agent()

    def _init_agent(self):
        api_key = LLM_API_KEY if LLM_API_KEY else "a"
        self.agent = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=api_key,
            openai_api_base=LLM_BASE_URL,
            temperature=0.3,
        ).bind_tools([tools.consultar_documentacion, tools.listar_archivos_datos, tools.leer_archivo_datos])

    def process(self, query: str) -> str:
        if not self.agent:
            return "Error: No se configuro la API key (LLM_API_KEY)."

        logger.info(f"Procesando consulta del usuario: '{query}'")
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *self._history,
            HumanMessage(content=query),
        ]

        try:
            response = self.llamada_con_herramientas(messages)
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

    def llamada_con_herramientas(self, messages: list):
        logger.info("Iniciando invocacion del agente (llamada_con_herramientas)")
        response = self.agent.invoke(messages)

        while response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                
                logger.info(f"El agente decidio llamar a la herramienta '{tool_name}' con argumentos: {tool_args}")
                available_tools = {
                    "consultar_documentacion": tools.consultar_documentacion,
                    "listar_archivos_datos": tools.listar_archivos_datos,
                    "leer_archivo_datos": tools.leer_archivo_datos,
                }
                if tool_name in available_tools:
                    tool_output = available_tools[tool_name].invoke(tool_args)
                else:
                    tool_output = f"Error: Herramienta '{tool_name}' no encontrada."
                    logger.warning(f"Intento de usar herramienta no existente '{tool_name}'")
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_id))
            response = self.agent.invoke(messages)

        return response


    def clear_history(self):
        self._history.clear()


def main(stdscr):
    ui = ChatUI(stdscr)
    ui.start()
    bot = MachineTwin()
    ui.set_status(bot.agent is not None, bot.rag is not None)

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
