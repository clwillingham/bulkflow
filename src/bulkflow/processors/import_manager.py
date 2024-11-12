import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict
from ..models import ProcessingState
from ..utils.logging_config import setup_logging

class ImportManager:
    def __init__(self, file_path: str, state_file: str = 'import_state.json'):
        self.file_path = file_path
        self.state_file = state_file
        self.logger = setup_logging(__name__)
        self.state = self._initialize_state()
        self.last_progress_update = time.time()
        self.progress_update_interval = 5  # seconds
        self._progress_cache = {}
        self._last_eta_update = 0
        self._processing_start_time = time.time()
        self._last_processed_position = self.state.last_successful_position
        
        # Initialize failed rows file
        self.failed_rows_file = f"failed_rows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.state.failed_rows_file = self.failed_rows_file
        
        # Create failed rows file with header
        with open(self.failed_rows_file, 'w') as f:
            f.write("row_number,row_content,error_reason,timestamp\n")

    def _calculate_file_hash(self) -> str:
        """Calculate a hash of the first 1MB of the file + file size + mtime"""
        stat = os.stat(self.file_path)
        with open(self.file_path, 'rb') as f:
            content_hash = hashlib.md5(f.read(1024 * 1024)).hexdigest()
        return f"{content_hash}-{stat.st_size}-{stat.st_mtime}"

    def _initialize_state(self) -> ProcessingState:
        """Initialize or load existing processing state"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                saved_state = ProcessingState.from_dict(json.load(f))
                
            current_hash = self._calculate_file_hash()
            if saved_state.file_hash != current_hash:
                self.logger.warning("File appears to have changed since last run. Starting fresh.")
                return self._create_new_state()
            
            self.logger.info(f"Resuming from previous state. "
                           f"Processed: {saved_state.processed_chunks} chunks, "
                           f"{saved_state.processed_bytes / saved_state.total_bytes:.1%} complete")
            
            # Log failed chunks details if any
            if saved_state.failed_chunks:
                for start, end in saved_state.failed_chunks:
                    self.logger.info(f"Found failed chunk: {start}-{end} (size: {end-start} bytes)")
            
            return saved_state
        
        return self._create_new_state()

    def _create_new_state(self) -> ProcessingState:
        """Create a new processing state"""
        return ProcessingState(
            file_path=self.file_path,
            file_hash=self._calculate_file_hash(),
            total_bytes=os.path.getsize(self.file_path),
            processed_bytes=0,
            processed_chunks=0,
            last_successful_position=0,
            failed_chunks=[],
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            processing_rate=0.0,
            failed_rows_file=''
        )

    def update_progress(self, position: int):
        """Update progress and calculate ETA"""
        current_time = time.time()
        
        # Only update progress at intervals to reduce I/O
        if current_time - self.last_progress_update >= self.progress_update_interval:
            elapsed_time = current_time - self._processing_start_time
            if elapsed_time > 0:
                # Calculate rate based on bytes processed since last position
                bytes_processed = position - self._last_processed_position
                self.state.processing_rate = bytes_processed / elapsed_time
                self._last_processed_position = position
                self._processing_start_time = current_time  # Reset for next calculation
                
                # Calculate ETA
                remaining_bytes = self.state.total_bytes - position
                if self.state.processing_rate > 0:
                    eta_seconds = remaining_bytes / self.state.processing_rate
                    eta = timedelta(seconds=int(eta_seconds))
                    progress = (position / self.state.total_bytes) * 100
                    
                    self.logger.info(
                        f"Progress: {progress:.2f}% complete | "
                        f"Speed: {self.state.processing_rate/1024/1024:.2f} MB/s | "
                        f"ETA: {eta}"
                    )
            
            self.last_progress_update = current_time
            self._last_eta_update = current_time

    def save_state(self):
        """Save current state to file"""
        self.state.last_updated = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def log_failed_row(self, row_number: int, row_content: str, error_reason: str):
        """Log a failed row to the failed rows file"""
        timestamp = datetime.now().isoformat()
        # Escape any quotes in the content and error reason
        row_content = row_content.replace('"', '""')
        error_reason = error_reason.replace('"', '""')
        with open(self.failed_rows_file, 'a') as f:
            f.write(f'{row_number},"{row_content}","{error_reason}",{timestamp}\n')
