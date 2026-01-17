"""
Data loader for CVE and Personal datasets from HuggingFace.
"""

from typing import List, Dict, Any
from datasets import load_dataset
from src.config import config


class DataLoader:
    """Load and preprocess datasets for RAG system."""
    
    def __init__(self):
        self.cve_data: List[Dict[str, Any]] = []
        self.personal_data: List[Dict[str, Any]] = []
    
    def load_cve_dataset(self) -> List[Dict[str, Any]]:
        """
        Load CVE dataset from HuggingFace.
        Returns the latest CVE_LIMIT entries.
        """
        print(f"Loading CVE dataset (last {config.CVE_LIMIT} entries)...")
        
        dataset = load_dataset(
            "stasvinokur/cve-and-cwe-dataset-1999-2025",
            split="train"
        )
        
        # Get the last N entries (most recent CVEs)
        total_entries = len(dataset)
        start_idx = max(0, total_entries - config.CVE_LIMIT)
        
        self.cve_data = []
        for i in range(start_idx, total_entries):
            entry = dataset[i]
            doc = self._format_cve_document(entry)
            self.cve_data.append(doc)
        
        print(f"Loaded {len(self.cve_data)} CVE entries")
        return self.cve_data
    
    def _format_cve_document(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Format a CVE entry into a document for embedding."""
        cve_id = entry.get("CVE-ID") or "Unknown"
        description = entry.get("DESCRIPTION") or "No description available"
        severity = entry.get("SEVERITY") or "Unknown"
        cvss_v3 = entry.get("CVSS-V3") or "N/A"
        cvss_v2 = entry.get("CVSS-V2") or "N/A"
        cwe_id = entry.get("CWE-ID") or "Unknown"
        
        # Create a rich text representation for embedding
        content = f"""CVE ID: {cve_id}
Severity: {severity}
CVSS v3 Score: {cvss_v3}
CVSS v2 Score: {cvss_v2}
CWE ID: {cwe_id}
Description: {description}"""
        
        return {
            "id": cve_id,
            "content": content,
            "metadata": {
                "type": "cve",
                "cve_id": str(cve_id),
                "severity": str(severity),
                "cvss_v3": str(cvss_v3),
                "cvss_v2": str(cvss_v2),
                "cwe_id": str(cwe_id),
                "description": str(description)[:500]  # Truncate long descriptions
            }
        }
    
    def load_personal_dataset(self) -> List[Dict[str, Any]]:
        """
        Load Personal dataset from HuggingFace.
        Returns the first PERSONAL_LIMIT entries.
        """
        print(f"Loading Personal dataset (first {config.PERSONAL_LIMIT} entries)...")
        
        dataset = load_dataset(
            "nvidia/Nemotron-Personas-USA",
            split="train"
        )
        
        self.personal_data = []
        for i in range(min(config.PERSONAL_LIMIT, len(dataset))):
            entry = dataset[i]
            doc = self._format_personal_document(entry, i)
            self.personal_data.append(doc)
        
        print(f"Loaded {len(self.personal_data)} Personal entries")
        return self.personal_data
    
    def _format_personal_document(self, entry: Dict[str, Any], idx: int) -> Dict[str, Any]:
        """Format a personal entry into a document for embedding."""
        # Extract key personal information fields
        persona = entry.get("persona") or ""
        
        # Extract individual fields if available
        name = entry.get("name") or f"Person_{idx}"
        age = entry.get("age") or "Unknown"
        occupation = entry.get("occupation") or "Unknown"
        location = entry.get("location") or "Unknown"
        education = entry.get("education_level") or "Unknown"
        
        # Build content from persona if individual fields not available
        if persona and not entry.get("name"):
            content = persona
        else:
            content = f"""Name: {name}
Age: {age}
Occupation: {occupation}
Location: {location}
Education: {education}
Full Persona: {str(persona)[:500] if persona else 'N/A'}"""
        
        return {
            "id": f"person_{idx}",
            "content": content,
            "metadata": {
                "type": "personal",
                "record_id": f"person_{idx}",
                "persona": str(persona)[:200] if persona else "N/A"
            }
        }
    
    def load_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load both datasets."""
        return {
            "cve": self.load_cve_dataset(),
            "personal": self.load_personal_dataset()
        }


# Singleton instance
data_loader = DataLoader()
