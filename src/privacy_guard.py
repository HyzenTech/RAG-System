"""
Privacy guard for PII detection and output sanitization.

IMPORTANT: The RAG itself is NOT filtered (per requirements).
This module only sanitizes the FINAL OUTPUT from the LLM.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class PIIPattern:
    """Pattern for PII detection."""
    name: str
    pattern: str
    replacement: str


class PrivacyGuard:
    """
    Multi-layer privacy protection for LLM outputs.
    
    Layer 1: Intent detection (block requests for personal info)
    Layer 2: Regex-based PII sanitization
    Layer 3: CVE-ID preservation
    """
    
    # PII detection patterns
    PII_PATTERNS: List[PIIPattern] = [
        # Social Security Numbers
        PIIPattern(
            name="ssn",
            pattern=r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
            replacement="[SSN REDACTED]"
        ),
        # Phone numbers (various formats)
        PIIPattern(
            name="phone",
            pattern=r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            replacement="[PHONE REDACTED]"
        ),
        # Email addresses
        PIIPattern(
            name="email",
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            replacement="[EMAIL REDACTED]"
        ),
        # Credit card numbers
        PIIPattern(
            name="credit_card",
            pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            replacement="[CREDIT CARD REDACTED]"
        ),
        # Street addresses (basic pattern)
        PIIPattern(
            name="address",
            pattern=r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct)\b',
            replacement="[ADDRESS REDACTED]"
        ),
        # Personal record IDs from our dataset
        PIIPattern(
            name="record_id",
            pattern=r'\bperson_\d+\b',
            replacement="[RECORD ID REDACTED]"
        ),
    ]
    
    # Phrases indicating personal info requests
    PERSONAL_INFO_INDICATORS = [
        r"(?:give|tell|show|provide|find|get|what is|what's)\s+(?:me\s+)?(?:\w+'?s?\s+)?(?:the\s+)?(?:phone|email|address|ssn|social security|contact)",
        r"(?:phone number|email address|home address|street address|social security number)",
        r"(?:how can i (?:reach|contact)|where does .+ live)",
        r"(?:personal information|private data|contact details|contact info)",
        r"(?:find|locate|look up|search for)\s+(?:a\s+)?(?:person|individual|someone)",
        r"(?:\w+'s\s+(?:phone|email|address|number|contact))",  # John's phone, Mary's email
        r"(?:phone|email|address|number)\s+(?:of|for)\s+(?:the\s+)?(?:user|person|individual)",
        r"(?:find|locate)\s+(?:the\s+)?person\s+(?:named|called)",  # find the person named X
    ]
    
    # CVE pattern to preserve
    CVE_PATTERN = r'CVE-\d{4}-\d{4,}'
    
    def __init__(self):
        self._compiled_patterns = [
            (p.name, re.compile(p.pattern, re.IGNORECASE), p.replacement)
            for p in self.PII_PATTERNS
        ]
        self._personal_indicators = [
            re.compile(p, re.IGNORECASE) for p in self.PERSONAL_INFO_INDICATORS
        ]
        self._cve_pattern = re.compile(self.CVE_PATTERN)
    
    def is_personal_info_request(self, query: str) -> bool:
        """
        Check if a query is requesting personal information.
        
        Args:
            query: User query
            
        Returns:
            True if query appears to request personal info
        """
        query_lower = query.lower()
        
        for pattern in self._personal_indicators:
            if pattern.search(query_lower):
                return True
        
        return False
    
    def sanitize_output(self, text: str) -> Tuple[str, List[str]]:
        """
        Sanitize LLM output by removing PII while preserving CVE IDs.
        
        Args:
            text: Raw LLM output
            
        Returns:
            Tuple of (sanitized text, list of redactions made)
        """
        # First, extract and protect CVE IDs
        cve_ids = self._cve_pattern.findall(text)
        protected_text = text
        cve_placeholders = {}
        
        for i, cve_id in enumerate(cve_ids):
            placeholder = f"__CVE_PLACEHOLDER_{i}__"
            cve_placeholders[placeholder] = cve_id
            protected_text = protected_text.replace(cve_id, placeholder, 1)
        
        # Apply PII sanitization
        redactions = []
        sanitized = protected_text
        
        for name, pattern, replacement in self._compiled_patterns:
            matches = pattern.findall(sanitized)
            if matches:
                redactions.extend([f"{name}: {m}" for m in matches])
                sanitized = pattern.sub(replacement, sanitized)
        
        # Restore CVE IDs
        for placeholder, cve_id in cve_placeholders.items():
            sanitized = sanitized.replace(placeholder, cve_id)
        
        return sanitized, redactions
    
    def get_refusal_message(self) -> str:
        """Get a polite refusal message for personal info requests."""
        return (
            "I'm sorry, but I cannot provide personal information such as phone numbers, "
            "email addresses, home addresses, or other private data. This is to protect "
            "individual privacy.\n\n"
            "I'm happy to help you with cybersecurity topics like:\n"
            "- CVE (Common Vulnerabilities and Exposures) information\n"
            "- Security best practices\n"
            "- Vulnerability analysis\n"
            "- CWE (Common Weakness Enumeration) details\n\n"
            "How can I assist you with cybersecurity today?"
        )
    
    def process_response(
        self,
        query: str,
        response: str,
        strict_mode: bool = True
    ) -> Tuple[str, bool, List[str]]:
        """
        Full privacy processing pipeline.
        
        Args:
            query: Original user query
            response: LLM response
            strict_mode: If True, refuse personal info requests entirely
            
        Returns:
            Tuple of (processed response, was_blocked, redactions)
        """
        # Layer 1: Intent detection
        if strict_mode and self.is_personal_info_request(query):
            return self.get_refusal_message(), True, ["query_blocked"]
        
        # Layer 2: Output sanitization
        sanitized, redactions = self.sanitize_output(response)
        
        return sanitized, False, redactions


# Singleton instance
privacy_guard = PrivacyGuard()
