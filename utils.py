import re
from pathlib import Path


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
                    content = path.read_text(encoding="utf-8")
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
                    "contenido": content
                })
    return docs