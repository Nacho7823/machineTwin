from typing import TypedDict


class ChunkMetadata(TypedDict):
    titulo: str
    doc_id: str
    chunk_index: int


class Document(TypedDict):
    id: str
    titulo: str
    contenido: str


class QueryResult(TypedDict):
    document: str
    metadata: ChunkMetadata
    distance: float
