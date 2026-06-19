from config import DOCS_DIR
from rag.models import Document, QueryResult
from rag.rag import DocumentRAG
from log import get_logger

logger = get_logger(__name__)

_rag = DocumentRAG(DOCS_DIR)


def query(question: str, k: int = 3) -> list[QueryResult]:
    return _rag.query(question, k)


def add_document(doc: Document) -> int:
    return _rag.add_document(doc)
