import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PromptRulesTests(unittest.TestCase):
    def test_prompt_does_not_cast_doubt_on_simulated_data(self):
        main = (ROOT / "main.py").read_text(encoding="utf-8")

        self.assertIn("No sugieras confirmar si los datos son reales, simulados o de prueba", main)
        self.assertIn("no recomiendes validar si corresponden a pruebas simuladas", main)


if __name__ == "__main__":
    unittest.main()
