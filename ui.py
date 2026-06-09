import curses
import textwrap
from datetime import datetime


WELCOME_MSG = (
    "Hola! Soy MachineTwin, tu asistente tecnico para la Torre de Enfriamiento T-100.\n"
    "Escribi tu pregunta para empezar."
)
HELP_MSG = (
    "Comandos:\n"
    "  /status      Estado actual\n"
    "  /summary     Resumen general\n"
    "  /anomalies   Anomalias (24h)\n"
    "  /events      Eventos (7 dias)\n"
    "  /recomend    Recomendaciones\n"
    "  /vars        Historial variables\n"
    "  /clear       Limpiar chat\n"
    "  /quit        Salir"
)
CMD_MAP = {
    "/status": "Dame el estado actual de la maquina.",
    "/summary": "Dame un resumen general de la maquina con tendencias y anomalias.",
    "/anomalies": "Detecta anomalias en las variables de la maquina en las ultimas 24 horas.",
    "/events": "Muestra los eventos recientes de la maquina de los ultimos 7 dias.",
    "/recomend": "Dame recomendaciones de operacion y mantenimiento.",
    "/vars": "Muestra el historial de las variables principales de la maquina en 24 horas.",
}


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(7, curses.COLOR_BLACK, -1)


class ChatUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.chat_input = ""
        self.chat_cursor = 0
        self.chat_history = []
        self.scroll_offset = 0
        self.thinking = False
        self.agent_ready = False
        self.rag_ready = False

    def start(self):
        curses.curs_set(1)
        init_colors()
        self.stdscr.keypad(True)
        self.stdscr.timeout(-1)
        self.chat_history.append(("bot", WELCOME_MSG))

    def add_message(self, role, text):
        self.chat_history.append((role, text))
        self.scroll_offset = 0

    def set_thinking(self, state):
        self.thinking = state

    def set_status(self, agent_ready, rag_ready):
        self.agent_ready = agent_ready
        self.rag_ready = rag_ready

    def get_event(self):
        ch = self.stdscr.getch()
        if ch == -1:
            return None
        # Ctrl+Q (ASCII 17) para salir de forma rápida
        if ch == 17:
            return ("quit", None)
        if self.thinking:
            return None
        if ch in (curses.KEY_ENTER, 10, 13):
            if self.chat_input.strip():
                text = self.chat_input.strip()
                self.chat_input = ""
                self.chat_cursor = 0
                if text == "/quit":
                    return ("quit", None)
                if text == "/clear":
                    return ("clear", None)
                if text == "/help":
                    return ("help", None)
                if text in CMD_MAP:
                    return ("command", CMD_MAP[text])
                return ("message", text)
            return None
        if ch in (curses.KEY_BACKSPACE, 127, 8):
            if self.chat_cursor > 0:
                self.chat_input = self.chat_input[: self.chat_cursor - 1] + self.chat_input[self.chat_cursor :]
                self.chat_cursor -= 1
        elif ch == curses.KEY_LEFT:
            self.chat_cursor = max(0, self.chat_cursor - 1)
        elif ch == curses.KEY_RIGHT:
            self.chat_cursor = min(len(self.chat_input), self.chat_cursor + 1)
        elif ch == curses.KEY_UP:
            self.scroll_offset = min(max(0, self._total_lines() - self._visible_lines()), self.scroll_offset + 3)
        elif ch == curses.KEY_DOWN:
            self.scroll_offset = max(0, self.scroll_offset - 3)
        elif 32 <= ch <= 126:
            self.chat_input = self.chat_input[: self.chat_cursor] + chr(ch) + self.chat_input[self.chat_cursor :]
            self.chat_cursor += 1
        return None

    def draw(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        if h < 8 or w < 30:
            self._safe_addstr(0, 0, "Terminal muy pequena")
            self.stdscr.refresh()
            return

        self._safe_addstr(0, 0, " " + " " * ((w - 30) // 2) + "MachineTwin - Torre T-100" + " " * ((w - 30) // 2), curses.color_pair(6) | curses.A_BOLD, w - 1)
        self._safe_addstr(1, 0, "\u2500" * (w - 1), curses.color_pair(7))

        ts = datetime.now().strftime("%H:%M")
        ag = "ON" if self.agent_ready else "OFF"
        rg = "ON" if self.rag_ready else "OFF"
        self._safe_addstr(h - 1, 0, f"Ag:{ag} RAG:{rg} {ts}".rjust(w), curses.color_pair(6), w - 1)

        chat_top = 2
        chat_bottom = h - 3
        input_y = h - 2
        max_visible = chat_bottom - chat_top

        all_lines = []
        for role, msg in self.chat_history:
            prefix = "Vos" if role == "user" else "MachineTwin"
            color = 4 if role == "user" else 3
            wrapped = textwrap.wrap(msg, width=w - 12) or [""]
            all_lines.append(("h", prefix, color))
            for line in wrapped:
                all_lines.append(("m", line, color))
            all_lines.append(("s", "", 0))

        total = len(all_lines)
        start_idx = max(0, total - max_visible - self.scroll_offset)
        cy = chat_top
        for kind, text, color in all_lines[start_idx:]:
            if cy >= chat_bottom:
                break
            if kind == "h":
                self._safe_addstr(cy, 2, text, curses.color_pair(color) | curses.A_BOLD)
            elif kind == "m":
                self._safe_addstr(cy, 4, text, curses.color_pair(color))
            cy += 1

        self._safe_addstr(input_y, 0, "\u2500" * (w - 1), curses.color_pair(7))
        if self.thinking:
            self._safe_addstr(input_y + 1, 0, " Generando respuesta...", curses.color_pair(2) | curses.A_BOLD, w - 1)
        else:
            display = self.chat_input[: w - 4]
            self._safe_addstr(input_y + 1, 0, "> ", curses.A_BOLD)
            self._safe_addstr(input_y + 1, 2, display, 0, w - 3)
            try:
                self.stdscr.move(input_y + 1, 2 + self.chat_cursor)
            except curses.error:
                pass
        self.stdscr.refresh()

    def _safe_addstr(self, y, x, text, attr=0, max_w=None):
        h, w = self.stdscr.getmaxyx()
        if y < 0 or y >= h:
            return
        if max_w is None:
            max_w = w - x
        try:
            self.stdscr.addnstr(y, x, text, max_w, attr)
        except curses.error:
            pass

    def _total_lines(self):
        h, w = self.stdscr.getmaxyx()
        return sum(max(1, len(textwrap.wrap(m, width=w - 12))) + 1 for _, m in self.chat_history)

    def _visible_lines(self):
        h, _ = self.stdscr.getmaxyx()
        return h - 5
