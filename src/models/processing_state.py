from dataclasses import dataclass, asdict
from typing import List, Tuple
from datetime import datetime

@dataclass
class ProcessingState:
    """Track the state of the import process"""
    file_path: str
    file_hash: str
    total_bytes: int
    processed_bytes: int
    processed_chunks: int
    last_successful_position: int
    failed_chunks: List[Tuple[int, int]]  # [(start_pos, end_pos)]
    started_at: str
    last_updated: str
    processing_rate: float = 0.0  # bytes per second
    failed_rows_file: str = ''  # Path to file containing failed rows
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
