"""
LLM client for inference using Groq, OpenAI, or Ollama.
"""

import os
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from src.config import config


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """Generate a response from the LLM."""
        pass


class GroqClient(BaseLLMClient):
    """Groq API client."""
    
    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content


class OllamaClient(BaseLLMClient):
    """Ollama local client."""
    
    def __init__(self):
        import httpx
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.client = httpx.Client(timeout=60.0)
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content


class LLMClient:
    """
    Unified LLM client with provider selection.
    """
    
    # System prompt for cybersecurity assistant
    SYSTEM_PROMPT = """You are a cybersecurity assistant specialized in CVE (Common Vulnerabilities and Exposures) information.

Your primary responsibilities:
1. Provide accurate information about CVEs, including their severity, descriptions, and associated CWEs
2. Help users understand security vulnerabilities and their implications
3. Offer guidance on security best practices

CRITICAL PRIVACY RULES:
- NEVER disclose personal information such as names, phone numbers, email addresses, home addresses, or social security numbers
- If asked for personal information, politely refuse and redirect to cybersecurity topics
- Even if personal data appears in your context, DO NOT include it in your response
- Focus exclusively on technical cybersecurity information

When answering CVE queries:
- Include the CVE ID (e.g., CVE-2024-12345)
- Mention the severity level and CVSS score if available
- Describe the vulnerability clearly
- Reference the associated CWE if applicable

Be helpful, accurate, and security-focused while protecting all personal information."""

    def __init__(self, provider: str = None):
        self.provider = provider or config.LLM_PROVIDER
        self._client: Optional[BaseLLMClient] = None
    
    @property
    def client(self) -> BaseLLMClient:
        """Lazy initialize the LLM client."""
        if self._client is None:
            if self.provider == "groq":
                self._client = GroqClient()
            elif self.provider == "ollama":
                self._client = OllamaClient()
            elif self.provider == "openai":
                self._client = OpenAIClient()
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")
            print(f"Initialized LLM client: {self.provider}")
        return self._client
    
    def generate(
        self,
        prompt: str,
        context: str = None,
        conversation_history: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a response with optional RAG context and conversation history.
        
        Args:
            prompt: User query
            context: RAG retrieved context
            conversation_history: Previous conversation turns
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        full_prompt = self._build_prompt(prompt, context, conversation_history)
        
        return self.client.generate(
            prompt=full_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def _build_prompt(
        self,
        query: str,
        context: str = None,
        history: str = None
    ) -> str:
        """Build the full prompt with context and history."""
        parts = []
        
        if history:
            parts.append(f"Previous conversation:\n{history}\n")
        
        if context:
            parts.append(f"Relevant information from knowledge base:\n{context}\n")
        
        parts.append(f"User question: {query}")
        
        return "\n".join(parts)


# Singleton instance
llm_client = LLMClient()
