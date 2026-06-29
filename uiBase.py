class BaseUI:
    def __init__(self):
        self._history = []
        self.onCompletition = None
        self.onClearHistory = None
        self.onEnsureConversation = None
        self.onListConversations = None
        self.onGetConversation = None
        self.onDeleteConversation = None
        self.onListTraces = None
        self.onGetConversationTrace = None

    def set_on_completion(self, callback):
        self.onCompletition = callback

    def set_on_clear_history(self, callback):
        self.onClearHistory = callback

    def set_on_ensure_conversation(self, callback):
        self.onEnsureConversation = callback

    def set_on_list_conversations(self, callback):
        self.onListConversations = callback

    def set_on_get_conversation(self, callback):
        self.onGetConversation = callback

    def set_on_delete_conversation(self, callback):
        self.onDeleteConversation = callback

    def set_on_list_traces(self, callback):
        self.onListTraces = callback

    def set_on_get_conversation_trace(self, callback):
        self.onGetConversationTrace = callback

    def chat_history(self):
        return self._history
