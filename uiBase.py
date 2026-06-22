class BaseUI:
    def __init__(self):
        self._history = []
        self.onCompletition = None
        self.onClearHistory = None

    def set_on_completion(self, callback):
        self.onCompletition = callback

    def set_on_clear_history(self, callback):
        self.onClearHistory = callback

    def chat_history(self):
        return self._history
