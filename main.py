import curses
from ui import ChatUI, HELP_MSG
from modules import DigitalTwinData
from config import DATA_DIR, DOCS_DIR, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
from rag import DocumentRAG

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


rag = DocumentRAG(DOCS_DIR)

SYSTEM_PROMPT = (
    "Sos MachineTwin, un asistente tecnico "
    "Respondes en espanol, de forma concisa y tecnica. "
    "Si no tenes datos suficientes, lo indicas."
)


class MachineTwin:
    def __init__(self):
        self.twin_data = DigitalTwinData(DATA_DIR)
        self.agent = None
        self.rag = rag
        self._history = []
        self._init_agent()

    def _init_agent(self):
        if not LLM_API_KEY:
            return
        self.agent = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=LLM_API_KEY,
            openai_api_base=LLM_BASE_URL,
            temperature=0.3,
        )

    def process(self, query: str) -> str:
        if not self.agent:
            return "Error: No se configuro la API key (LLM_API_KEY)."

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *self._history,
            HumanMessage(content=query),
        ]

        try:
            response = self.agent.invoke(messages)
            answer = response.content
            self._history.append(HumanMessage(content=query))
            self._history.append(response)
            if len(self._history) > 20:
                self._history = self._history[-20:]
            return answer
        except Exception as e:
            return f"Error al consultar el LLM: {e}"

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
