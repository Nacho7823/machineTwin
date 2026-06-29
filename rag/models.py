from typing import TypedDict


class ChunkMetadata(TypedDict):
    titulo: str
    doc_id: str
    chunk_index: int
    source_path: str


class Document(TypedDict):
    id: str
    titulo: str
    contenido: str
    source_path: str


class QueryResult(TypedDict):
    document: str
    metadata: ChunkMetadata
    distance: float
