"""
Conversation memory management.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """A single conversation message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConversationMemory:
    """
    Manages conversation history for multi-turn interactions.
    """
    
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.messages: List[Message] = []
        self.session_id: Optional[str] = None
    
    def add_user_message(self, content: str):
        """Add a user message to history."""
        self.messages.append(Message(role="user", content=content))
        self._trim_history()
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to history."""
        self.messages.append(Message(role="assistant", content=content))
        self._trim_history()
    
    def _trim_history(self):
        """Keep only the last max_turns * 2 messages (user + assistant pairs)."""
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
    
    def get_history_string(self, exclude_last: bool = True) -> str:
        """
        Get conversation history as a formatted string.
        
        Args:
            exclude_last: If True, exclude the last message (current query)
            
        Returns:
            Formatted conversation history
        """
        messages = self.messages[:-1] if exclude_last and self.messages else self.messages
        
        if not messages:
            return ""
        
        lines = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            lines.append(f"{role}: {msg.content}")
        
        return "\n".join(lines)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages as list of dicts for API calls."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []
    
    def get_turn_count(self) -> int:
        """Get number of conversation turns."""
        return len([m for m in self.messages if m.role == "user"])


# Create a default memory instance
conversation_memory = ConversationMemory()
