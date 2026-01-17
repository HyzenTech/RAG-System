"""
Core RAG pipeline for CVE information retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple
from src.config import config
from src.data_loader import data_loader
from src.vector_store import vector_store
from src.embeddings import embedding_model
from src.llm_client import llm_client
from src.privacy_guard import privacy_guard
from src.memory import conversation_memory, ConversationMemory


class RAGPipeline:
    """
    Complete RAG pipeline for CVE information retrieval with privacy protection.
    
    Architecture:
    1. User Query → Embedding Model → Vector Search
    2. Retrieved Context (UNFILTERED) → LLM
    3. LLM Response → Privacy Guard → Safe Output
    """
    
    def __init__(self):
        self._initialized = False
        self.memory = conversation_memory
    
    def initialize(self, force_reload: bool = False):
        """
        Initialize the RAG system by loading data and building vector store.
        
        Args:
            force_reload: If True, clear existing data and reload
        """
        if self._initialized and not force_reload:
            print("RAG pipeline already initialized")
            return
        
        print("=" * 50)
        print("Initializing RAG Pipeline...")
        print("=" * 50)
        
        # Ensure directories exist
        config.ensure_directories()
        
        # Check if we need to load data
        stats = vector_store.get_stats()
        
        if stats["cve_count"] == 0 or force_reload:
            if force_reload:
                vector_store.clear_all()
            
            # Load CVE data
            cve_docs = data_loader.load_cve_dataset()
            vector_store.add_documents("cve", cve_docs)
        else:
            print(f"CVE collection already has {stats['cve_count']} documents")
        
        if stats["personal_count"] == 0 or force_reload:
            # Load Personal data
            personal_docs = data_loader.load_personal_dataset()
            vector_store.add_documents("personal", personal_docs)
        else:
            print(f"Personal collection already has {stats['personal_count']} documents")
        
        # Verify embedding model is loaded
        _ = embedding_model.dimension
        
        self._initialized = True
        
        # Print final stats
        final_stats = vector_store.get_stats()
        print("=" * 50)
        print(f"RAG Pipeline Ready!")
        print(f"  CVE Documents: {final_stats['cve_count']}")
        print(f"  Personal Documents: {final_stats['personal_count']}")
        print("=" * 50)
    
    def query(
        self,
        user_query: str,
        use_memory: bool = True,
        strict_privacy: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query through the full RAG pipeline.
        
        Args:
            user_query: User's question
            use_memory: Whether to include conversation history
            strict_privacy: If True, block personal info requests entirely
            
        Returns:
            Dict with response, metadata, and any privacy actions taken
        """
        if not self._initialized:
            self.initialize()
        
        # Add user query to memory
        if use_memory:
            self.memory.add_user_message(user_query)
        
        # Step 1: Retrieve relevant context from BOTH collections (unfiltered)
        retrieved_docs = vector_store.search(
            query=user_query,
            collection_type="both",
            top_k=config.TOP_K_RESULTS
        )
        
        # Format context for LLM
        context = self._format_context(retrieved_docs)
        
        # Get conversation history
        history = self.memory.get_history_string() if use_memory else None
        
        # Step 2: Generate LLM response
        try:
            raw_response = llm_client.generate(
                prompt=user_query,
                context=context,
                conversation_history=history
            )
        except Exception as e:
            raw_response = f"Error generating response: {str(e)}"
        
        # Step 3: Apply privacy protection
        final_response, was_blocked, redactions = privacy_guard.process_response(
            query=user_query,
            response=raw_response,
            strict_mode=strict_privacy
        )
        
        # Add response to memory
        if use_memory:
            self.memory.add_assistant_message(final_response)
        
        return {
            "response": final_response,
            "was_blocked": was_blocked,
            "redactions": redactions,
            "retrieved_count": len(retrieved_docs),
            "sources": [
                {"id": doc["id"], "source": doc["source"], "distance": doc["distance"]}
                for doc in retrieved_docs[:3]
            ]
        }
    
    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents as context string."""
        if not docs:
            return "No relevant information found in knowledge base."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc["source"].upper()
            content = doc["content"]
            context_parts.append(f"[{source} Document {i}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def reset_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        stats = vector_store.get_stats()
        return {
            "initialized": self._initialized,
            "cve_count": stats["cve_count"],
            "personal_count": stats["personal_count"],
            "conversation_turns": self.memory.get_turn_count(),
            "llm_provider": config.LLM_PROVIDER,
            "embedding_model": config.EMBEDDING_MODEL
        }


# Singleton instance
rag_pipeline = RAGPipeline()
