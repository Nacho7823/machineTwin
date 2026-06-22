import tempfile
import unittest
from pathlib import Path

from utils import cargar_documentos, read_csv_with_fallback, read_text_with_fallback


class EncodingFallbackTests(unittest.TestCase):
    def test_read_text_with_fallback_reads_latin1_degree_symbol(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "machine_current.json"
            path.write_bytes(b'{"unit": "\xb0C"}')

            self.assertEqual(read_text_with_fallback(path), '{"unit": "°C"}')

    def test_cargar_documentos_reads_latin1_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)
            (docs_dir / "manual.md").write_bytes("Temperatura: 42 °C".encode("latin-1"))

            docs = cargar_documentos(docs_dir)

            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]["contenido"], "Temperatura: 42 °C")

    def test_read_csv_with_fallback_reads_latin1_degree_symbol(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "history.csv"
            path.write_bytes("unit,value\n°C,42\n".encode("latin-1"))

            df = read_csv_with_fallback(path)

            self.assertEqual(df.loc[0, "unit"], "°C")
            self.assertEqual(df.loc[0, "value"], 42)


if __name__ == "__main__":
    unittest.main()
