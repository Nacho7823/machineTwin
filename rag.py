from pathlib import Path


class DocumentRAG:
    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)
        self.ready = False

    def query(self, question: str, k: int = 3) -> str:
        return ""
