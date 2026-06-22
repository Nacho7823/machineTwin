from log import get_logger
from llm import LLMAgent
from langchain_core.messages import HumanMessage, SystemMessage

import tools

logger = get_logger(__name__)

SYSTEM_PROMPT = """
Sos MachineTwin, un asistente tecnico para maquinas industriales y gemelos digitales.
Respondes en espanol, de forma concisa, clara y tecnica.

Tu objetivo es ayudar a interpretar el estado operativo de la maquina, analizar variables,
detectar posibles anomalias y dar recomendaciones de operacion o mantenimiento basadas
en datos disponibles y documentacion tecnica.

Reglas de uso de informacion:
- Antes de responder sobre estado actual, valores medidos o condicion operativa, consulta obtener_estado_actual.
- Antes de responder sobre tendencias o evolucion de variables, consulta analizar_tendencia.
- Antes de responder sobre anomalias, riesgos o valores fuera de rango, consulta detectar_fuera_de_limites.
- Antes de responder sobre fallas, alertas, mantenimientos o antecedentes, consulta consultar_eventos_recientes.
- Antes de dar recomendaciones tecnicas de operacion o mantenimiento, consulta consultar_documentacion.
- Si necesitas complementar una respuesta con datos o documentacion, usa las herramientas disponibles.

Reglas de respuesta:
- No inventes valores, eventos, rangos, causas ni recomendaciones.
- Si una informacion no esta en los datos o en la documentacion, indicalo de forma clara.
- Cuando uses datos de la maquina, menciona brevemente la fuente: estado actual, historial, eventos o documentacion tecnica.
- Si la consulta esta fuera del dominio de maquinas industriales o gemelos digitales, indica que esta fuera del alcance.
"""


TOOLS = {
    "consultar_documentacion": tools.consultar_documentacion,
    "obtener_estado_actual": tools.obtener_estado_actual,
    "consultar_eventos_recientes": tools.consultar_eventos_recientes,
    "detectar_fuera_de_limites": tools.detectar_fuera_de_limites,
    "analizar_tendencia": tools.analizar_tendencia,
    "listar_archivos_datos": tools.listar_archivos_datos,
    "leer_archivo_datos": tools.leer_archivo_datos,
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

    twin = MachineTwin()

    def handle_completion(msg: str):
        return twin.process(msg)

    mode = sys.argv[1] if len(sys.argv) > 1 else "terminal"

    from uiBase import BaseUI
    if mode == "web":
        from uiWeb import WebUI
        ui: BaseUI = WebUI()
    else:
        from uiTerminal import TUI
        ui: BaseUI = TUI()

    ui.set_on_completion(handle_completion)
    ui.start()


