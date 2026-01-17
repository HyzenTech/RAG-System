"""
ChromaDB vector store operations.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from src.config import config
from src.embeddings import embedding_model


class VectorStore:
    """ChromaDB vector store for CVE and Personal data."""
    
    def __init__(self):
        self._client = None
        self._cve_collection = None
        self._personal_collection = None
    
    @property
    def client(self) -> chromadb.ClientAPI:
        """Lazy initialize ChromaDB client."""
        if self._client is None:
            config.ensure_directories()
            self._client = chromadb.PersistentClient(
                path=config.CHROMA_DB_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client
    
    @property
    def cve_collection(self):
        """Get or create CVE collection."""
        if self._cve_collection is None:
            self._cve_collection = self.client.get_or_create_collection(
                name=config.CVE_COLLECTION,
                metadata={"description": "CVE vulnerability data"}
            )
        return self._cve_collection
    
    @property
    def personal_collection(self):
        """Get or create Personal collection."""
        if self._personal_collection is None:
            self._personal_collection = self.client.get_or_create_collection(
                name=config.PERSONAL_COLLECTION,
                metadata={"description": "Personal information data"}
            )
        return self._personal_collection
    
    def add_documents(
        self,
        collection_type: str,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Add documents to a collection.
        
        Args:
            collection_type: "cve" or "personal"
            documents: List of document dicts with id, content, metadata
            
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        collection = self.cve_collection if collection_type == "cve" else self.personal_collection
        
        # Check if documents already exist
        existing = collection.count()
        if existing > 0:
            print(f"Collection {collection_type} already has {existing} documents, skipping...")
            return 0
        
        # Prepare data for insertion
        ids = [doc["id"] for doc in documents]
        contents = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(documents)} {collection_type} documents...")
        embeddings = embedding_model.embed(contents)
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
        
        print(f"Added {len(documents)} documents to {collection_type} collection")
        return len(documents)
    
    def search(
        self,
        query: str,
        collection_type: str = "both",
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            collection_type: "cve", "personal", or "both"
            top_k: Number of results to return
            
        Returns:
            List of matching documents with scores
        """
        top_k = top_k or config.TOP_K_RESULTS
        query_embedding = embedding_model.embed_query(query)
        
        results = []
        
        if collection_type in ["cve", "both"]:
            cve_results = self.cve_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            results.extend(self._format_results(cve_results, "cve"))
        
        if collection_type in ["personal", "both"]:
            personal_results = self.personal_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            results.extend(self._format_results(personal_results, "personal"))
        
        # Sort by distance (lower is better)
        results.sort(key=lambda x: x["distance"])
        
        return results[:top_k]
    
    def _format_results(
        self,
        raw_results: Dict,
        source: str
    ) -> List[Dict[str, Any]]:
        """Format raw ChromaDB results."""
        formatted = []
        
        if not raw_results["ids"] or not raw_results["ids"][0]:
            return formatted
        
        ids = raw_results["ids"][0]
        documents = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0]
        distances = raw_results["distances"][0]
        
        for i, doc_id in enumerate(ids):
            formatted.append({
                "id": doc_id,
                "content": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i],
                "source": source
            })
        
        return formatted
    
    def get_stats(self) -> Dict[str, int]:
        """Get collection statistics."""
        return {
            "cve_count": self.cve_collection.count(),
            "personal_count": self.personal_collection.count()
        }
    
    def clear_all(self):
        """Clear all collections (for testing)."""
        try:
            self.client.delete_collection(config.CVE_COLLECTION)
        except:
            pass
        try:
            self.client.delete_collection(config.PERSONAL_COLLECTION)
        except:
            pass
        self._cve_collection = None
        self._personal_collection = None


# Singleton instance
vector_store = VectorStore()
