"""Agent memory and desire system"""
from typing import List, Dict, Any


class AgentMemory:
    """Manages agent memory and learning across sessions"""

    def __init__(self, max_entries: int = 20):
        self.memory: List[Dict[str, Any]] = []
        self.max_entries = max_entries

    def add_memory(self, entry: Dict[str, Any]):
        """Add a memory entry"""
        self.memory.append(entry)
        if len(self.memory) > self.max_entries:
            self.memory = self.memory[-self.max_entries:]

    def get_recent(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent memory entries"""
        return self.memory[-count:] if self.memory else []

    def clear(self):
        """Clear all memories"""
        self.memory = []

    def to_dict(self) -> Dict[str, Any]:
        """Export memory as dictionary"""
        return {"memory": self.memory, "count": len(self.memory)}