"""
Test suite for RAG CVE System.

Run with: pytest test_system.py -v
"""

import pytest
import re


class TestPrivacyGuard:
    """Test privacy protection mechanisms."""
    
    def test_ssn_detection(self):
        """Test SSN pattern detection."""
        from src.privacy_guard import privacy_guard
        
        text = "The SSN is 123-45-6789 and another 987-65-4321"
        sanitized, redactions = privacy_guard.sanitize_output(text)
        
        assert "123-45-6789" not in sanitized
        assert "987-65-4321" not in sanitized
        assert "[SSN REDACTED]" in sanitized
        assert len(redactions) == 2
    
    def test_phone_detection(self):
        """Test phone number pattern detection."""
        from src.privacy_guard import privacy_guard
        
        text = "Call me at (555) 123-4567 or 555-987-6543"
        sanitized, redactions = privacy_guard.sanitize_output(text)
        
        assert "123-4567" not in sanitized
        assert "[PHONE REDACTED]" in sanitized
    
    def test_email_detection(self):
        """Test email pattern detection."""
        from src.privacy_guard import privacy_guard
        
        text = "Email me at john.doe@example.com for more info"
        sanitized, redactions = privacy_guard.sanitize_output(text)
        
        assert "john.doe@example.com" not in sanitized
        assert "[EMAIL REDACTED]" in sanitized
    
    def test_cve_preservation(self):
        """Test that CVE IDs are preserved during sanitization."""
        from src.privacy_guard import privacy_guard
        
        text = "CVE-2024-12345 affects systems. SSN: 123-45-6789"
        sanitized, redactions = privacy_guard.sanitize_output(text)
        
        assert "CVE-2024-12345" in sanitized
        assert "123-45-6789" not in sanitized
    
    def test_personal_info_request_detection(self):
        """Test intent detection for personal info requests."""
        from src.privacy_guard import privacy_guard
        
        # Should be detected as personal info request
        assert privacy_guard.is_personal_info_request("Give me John's phone number")
        assert privacy_guard.is_personal_info_request("What is the email address of the user")
        assert privacy_guard.is_personal_info_request("Find the person named Smith")
        assert privacy_guard.is_personal_info_request("What is someone's phone number")
        
        # Should NOT be detected as personal info request
        assert not privacy_guard.is_personal_info_request("What is CVE-2024-12345?")
        assert not privacy_guard.is_personal_info_request("Tell me about SQL injection")


class TestDataLoader:
    """Test data loading functionality."""
    
    def test_cve_format(self):
        """Test CVE document formatting."""
        from src.data_loader import DataLoader
        
        loader = DataLoader()
        
        # Mock entry
        entry = {
            "CVE-ID": "CVE-2024-99999",
            "DESCRIPTION": "Test vulnerability",
            "SEVERITY": "HIGH",
            "CVSS-V3": 8.5,
            "CVSS-V2": 7.0,
            "CWE-ID": "CWE-79"
        }
        
        doc = loader._format_cve_document(entry)
        
        assert doc["id"] == "CVE-2024-99999"
        assert "CVE-2024-99999" in doc["content"]
        assert "HIGH" in doc["content"]
        assert doc["metadata"]["type"] == "cve"
        assert doc["metadata"]["cve_id"] == "CVE-2024-99999"
    
    def test_none_handling(self):
        """Test that None values are handled properly."""
        from src.data_loader import DataLoader
        
        loader = DataLoader()
        
        # Entry with None values
        entry = {
            "CVE-ID": None,
            "DESCRIPTION": None,
            "SEVERITY": None,
            "CVSS-V3": None,
            "CVSS-V2": None,
            "CWE-ID": None
        }
        
        doc = loader._format_cve_document(entry)
        
        # Should not have None in metadata
        for key, value in doc["metadata"].items():
            assert value is not None, f"None found in metadata[{key}]"
            assert "None" not in str(value), f"'None' string found in metadata[{key}]"


class TestEmbeddings:
    """Test embedding model."""
    
    def test_embedding_generation(self):
        """Test that embeddings are generated correctly."""
        from src.embeddings import embedding_model
        
        texts = ["test query about CVE", "another security question"]
        embeddings = embedding_model.embed(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384  # MiniLM dimension
    
    def test_single_query(self):
        """Test single query embedding."""
        from src.embeddings import embedding_model
        
        embedding = embedding_model.embed_query("What is CVE-2024-12345?")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384


class TestMemory:
    """Test conversation memory."""
    
    def test_message_storage(self):
        """Test message storage."""
        from src.memory import ConversationMemory
        
        memory = ConversationMemory(max_turns=5)
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi there!")
        
        assert memory.get_turn_count() == 1
        assert len(memory.messages) == 2
    
    def test_history_trimming(self):
        """Test that history is trimmed to max_turns."""
        from src.memory import ConversationMemory
        
        memory = ConversationMemory(max_turns=2)
        
        for i in range(5):
            memory.add_user_message(f"User message {i}")
            memory.add_assistant_message(f"Assistant message {i}")
        
        # Should only keep last 2 turns (4 messages)
        assert len(memory.messages) == 4
    
    def test_history_string(self):
        """Test history string formatting."""
        from src.memory import ConversationMemory
        
        memory = ConversationMemory()
        memory.add_user_message("What is CVE?")
        memory.add_assistant_message("CVE stands for...")
        memory.add_user_message("Tell me more")
        
        history = memory.get_history_string(exclude_last=True)
        
        assert "User: What is CVE?" in history
        assert "Assistant: CVE stands for..." in history


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    @pytest.mark.slow
    def test_rag_initialization(self):
        """Test RAG pipeline initialization."""
        from src.rag_pipeline import rag_pipeline
        
        rag_pipeline.initialize()
        status = rag_pipeline.get_status()
        
        assert status["initialized"]
        assert status["cve_count"] > 0
        assert status["personal_count"] > 0
    
    @pytest.mark.slow 
    def test_cve_query(self):
        """Test CVE query processing."""
        from src.rag_pipeline import rag_pipeline
        
        rag_pipeline.initialize()
        result = rag_pipeline.query("What are high severity vulnerabilities?")
        
        assert "response" in result
        assert len(result["response"]) > 0
        assert result["retrieved_count"] > 0
    
    @pytest.mark.slow
    def test_privacy_blocking(self):
        """Test that privacy protection blocks PII requests."""
        from src.rag_pipeline import rag_pipeline
        
        rag_pipeline.initialize()
        result = rag_pipeline.query("Give me someone's phone number")
        
        assert result["was_blocked"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
