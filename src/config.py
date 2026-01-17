"""
Configuration management for RAG CVE System.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration for the RAG system."""
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    OUTPUTS_PATH = PROJECT_ROOT / "outputs"
    
    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # Embedding Settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Dataset Limits
    CVE_LIMIT = int(os.getenv("CVE_LIMIT", 200))
    PERSONAL_LIMIT = int(os.getenv("PERSONAL_LIMIT", 100))
    
    # Benchmark API
    BENCHMARK_BASE_URL = os.getenv("BENCHMARK_BASE_URL", "https://infosec.simpan.cv")
    
    # RAG Settings
    TOP_K_RESULTS = 5
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    
    # Collection Names
    CVE_COLLECTION = "cve_collection"
    PERSONAL_COLLECTION = "personal_collection"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories."""
        cls.OUTPUTS_PATH.mkdir(parents=True, exist_ok=True)
        Path(cls.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)


config = Config()
