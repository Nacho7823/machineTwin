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
- No menciones nombres internos de tools en la respuesta al usuario.
- No agregues una seccion "Fuente" cuando respondas usando datos operativos de la maquina, como estado actual, historial, eventos o rangos configurados.
- Solo menciona fuente cuando uses documentacion tecnica, manuales, archivos consultables o explicaciones teoricas. En ese caso, cita la fuente por su nombre visible o tipo de documento, no por el nombre interno de la tool.
- Si los valores actuales estan normales pero hay alertas registradas, indica: "No veo valores actuales fuera de rango crítico. Hay alertas registradas para revisar." No las descartes ni recomiendes validar si corresponden a pruebas simuladas. Ofrece mostrar el detalle de esas alertas.
- No sugieras confirmar si los datos son reales, simulados o de prueba; tratalos como los datos actuales del entorno. Si un evento dice "anomalia inyectada", podes reportar esa descripcion, pero no recomiendes validar si corresponden a pruebas simuladas.
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
