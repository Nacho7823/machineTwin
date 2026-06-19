from pathlib import Path
import chromadb
from utils import cargar_documentos, chunk_por_oracion
from log import get_logger
from models import ChunkMetadata, Document
from sentence_transformers import SentenceTransformer


logger = get_logger(__name__)
modelo_emb = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


class DocumentRAG:
    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)
        self.ready = False
        
        self.client = chromadb.Client()
        try:
            self.client.delete_collection('clase3_docs')
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name='clase3_docs',
            metadata={'hnsw:space': 'cosine'},
        )

        self._initialize_db()

    def add_document(self, doc: Document) -> int:
        chunks = chunk_por_oracion(doc['contenido'])
        if not chunks:
            return 0

        chunk_ids = [f"{doc['id']}_chunk_{i}" for i in range(len(chunks))]
        metadatas: list[ChunkMetadata] = [
            {
                'titulo': doc['titulo'],
                'doc_id': doc['id'],
                'chunk_index': i,
            }
            for i in range(len(chunks))
        ]

        embeddings = modelo_emb.encode(chunks).tolist()
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=chunk_ids,
        )
        return len(chunks)

    def _initialize_db(self):
        logger.info("Inicializando base de datos RAG...")
        docs = cargar_documentos(self.docs_dir)

        total_chunks = 0
        for doc in docs:
            total_chunks += self.add_document(doc)

        if total_chunks:
            self.ready = True
            logger.info(f"✓ Indexados {self.collection.count()} chunks en ChromaDB")
        else:
            logger.warning("No se encontraron documentos para inicializar la base de datos RAG.")

    def query(self, question: str, k: int = 3) -> str:
        if not self.ready:
            logger.warning("Intento de consulta RAG pero el sistema no esta listo.")
            return "No hay documentos indexados o el sistema RAG no está listo."
            
        logger.info(f"Realizando consulta RAG: '{question}' con k={k}")
        try:
            query_embeddings = modelo_emb.encode([question]).tolist()
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=k,
                include=['documents', 'metadatas', 'distances'],
            )
            
            if not results or not results.get('documents') or not results['documents'][0]:
                logger.info("No se encontraron documentos relevantes en ChromaDB.")
                return "No se encontraron documentos relevantes."
                
            contexto_partes: list[str] = []
            for i in range(len(results['documents'][0])):
                doc = results['documents'][0][i]
                metadata: ChunkMetadata = results['metadatas'][0][i]
                titulo = metadata['titulo']
                contexto_partes.append(f'[{i+1}] ({titulo}): {doc}')
            
            logger.info(f"Consulta RAG exitosa. Se recuperaron {len(contexto_partes)} fragmentos relevantes.")
            return '\n\n'.join(contexto_partes)
        except Exception as e:
            logger.error(f"Error al consultar el RAG: {e}")
            return f"Error al consultar el RAG: {e}"






#----------------------------------------------------------------------------------
# Esto es para probar el rag sin tener q usar main
#----------------------------------------------------------------------------------






if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Crear un documento de prueba
        test_file = tmp_path / "test_doc.txt"
        test_file.write_text(
            "La cátedra de Inteligencia Artificial tiene varios docentes. "
            "El profesor titular es Jorge Roa. La jefa de trabajos prácticos es Milagros Gutierrez. "
            "Las entregas del TP2 son obligatorias y se realizan a través de la plataforma virtual.",
            encoding="utf-8"
        )
        
        print("Inicializando RAG...")
        rag_system = DocumentRAG(tmp_path)
        print(f"RAG listo: {rag_system.ready}")
        
        pregunta = "¿Quiénes son los docentes de la cátedra?"
        print(f"\nPregunta: {pregunta}")
        contexto = rag_system.query(pregunta, k=2)
        print(f"Contexto recuperado:\n{contexto}")


