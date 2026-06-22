import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UIRegressionTests(unittest.TestCase):
    def test_desktop_sidebar_has_collapsed_layout(self):
        css = (ROOT / "frontend/src/App.css").read_text(encoding="utf-8")

        self.assertIn(".app-layout.sidebar-collapsed .sidebar", css)
        self.assertIn(".app-layout.sidebar-collapsed .chat-container", css)

    def test_frontend_sends_conversation_id_to_backend(self):
        app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")

        self.assertIn("conversation_id", app)
        self.assertIn("URLSearchParams", app)

    def test_touch_devices_can_see_delete_buttons(self):
        css = (ROOT / "frontend/src/App.css").read_text(encoding="utf-8")

        self.assertIn("@media (hover: none)", css)
        self.assertIn(".sidebar-item-delete", css)

    def test_alert_quick_actions_are_available(self):
        app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
        message_list = (ROOT / "frontend/src/components/MessageList.tsx").read_text(encoding="utf-8")

        for label in ("Ver alertas", "Revisar anomalías", "Analizar tendencias", "Qué revisar"):
            self.assertIn(label, app)

        self.assertIn("shouldShowQuickActions", app)
        self.assertIn("onQuickPrompt", message_list)


if __name__ == "__main__":
    unittest.main()
