"""
core/rag_memory.py
==================
Implements Infinite Semantic Memory using ChromaDB.
This allows Vani to recall context, facts, and past conversations
across infinite sessions without bloating the context window.
"""

import os
from config.settings import DATA_DIR
from core.logger import get_logger

logger = get_logger(__name__)

class RAGMemory:
    """
    Retrieval-Augmented Generation (RAG) Memory using ChromaDB.
    Runs entirely locally.
    """
    
    def __init__(self):
        self.is_ready = False
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Persist DB inside our data directory
            self.persist_dir = os.path.join(DATA_DIR, "chroma_db")
            os.makedirs(self.persist_dir, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            
            # We use the default local embedding model
            self.collection = self.client.get_or_create_collection(name="vani_long_term_memory")
            self.is_ready = True
            logger.info("ChromaDB Semantic Memory initialized successfully.")
        except ImportError:
            logger.error("chromadb is not installed. Run: pip install chromadb")
        except Exception as e:
            logger.error(f"Failed to initialize RAG memory: {e}")

    def add_memory(self, session_id: str, role: str, content: str, memory_id: str):
        """Add a memory to the vector database."""
        if not self.is_ready or not content.strip():
            return
            
        try:
            # We construct a document string that includes the role context
            document = f"[{role.upper()}] {content}"
            
            self.collection.add(
                documents=[document],
                metadatas=[{"session_id": session_id, "role": role}],
                ids=[str(memory_id)]
            )
            logger.debug(f"Added to long-term memory: {memory_id}")
        except Exception as e:
            logger.error(f"Failed to add memory to ChromaDB: {e}")

    def search(self, query: str, limit: int = 3) -> str:
        """
        Search infinite memory for context related to a query.
        Returns a formatted string of relevant past messages.
        """
        if not self.is_ready or not query.strip():
            return ""
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            if not results["documents"] or not results["documents"][0]:
                return ""
                
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            
            context = "🧠 [Retrieved from Long-Term Memory]:\n"
            for doc, meta in zip(docs, metadatas):
                 session = meta.get("session_id", "Unknown session")
                 context += f"- (From {session[:8]}...) {doc}\n"
                 
            return context
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            return ""
