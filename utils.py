import re
import sys
from pathlib import Path


def read_text_with_fallback(path: Path, encodings: tuple[str, ...] = ("utf-8", "latin-1")) -> str:
    """Lee texto intentando codificaciones comunes para datos heredados."""
    last_error = None
    for encoding in encodings:
        try:
            return Path(path).read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error


def read_csv_with_fallback(path: Path, encodings: tuple[str, ...] = ("utf-8", "latin-1"), **kwargs):
    """Lee CSV intentando codificaciones comunes para datos heredados."""
    pd = sys.modules.get("pandas")
    if pd is None:
        import pandas as pd

    last_error = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding, **kwargs)
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error


def chunk_por_oracion(texto: str) -> list[str]:
    """Chunking por oración (split en punto/exclamación/interrogación + espacio)."""
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    return [o.strip() for o in oraciones if o.strip()]


def cargar_documentos(docs_dir: Path) -> list[dict]:
    """Carga y procesa archivos de texto, markdown y PDF desde un directorio."""
    docs = []
    if not docs_dir.exists():
        return docs
        
    for path in docs_dir.iterdir():
        if path.is_file():
            ext = path.suffix.lower()
            content = ""
            if ext in (".md", ".txt"):
                try:
                    content = read_text_with_fallback(path)
                except Exception as e:
                    print(f"Error al leer {path.name}: {e}")
            elif ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(path)
                    pages_text = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            pages_text.append(t)
                    content = "\n".join(pages_text)
                except Exception as e:
                    print(f"Error al leer PDF {path.name}: {e}")

            if content.strip():
                docs.append({
                    "id": path.stem,
                    "titulo": path.name,
                    "contenido": content,
                    "source_path": str(path),
                })
    return docs
