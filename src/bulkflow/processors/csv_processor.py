import csv
import resource
from typing import List, Tuple, Iterator
from ..utils.logging_config import setup_logging

class CSVProcessor:
    def __init__(self, import_manager):
        self.import_manager = import_manager
        self.logger = setup_logging(__name__)
        self.chunk_size = self._calculate_optimal_chunk_size()
        self.header = None
        self.current_row_number = 0
        self.encoding = self._detect_encoding()

    def _detect_encoding(self) -> str:
        """Try to detect the file encoding by attempting different common encodings"""
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(self.import_manager.file_path, 'r', encoding=encoding) as f:
                    # Try to read a small sample of the file
                    f.read(1024)
                    f.seek(0)
                    self.logger.info(f"Successfully detected encoding: {encoding}")
                    return encoding
            except UnicodeDecodeError:
                continue
        
        # If no encoding works perfectly, default to latin1 which can read any byte
        self.logger.warning("Could not detect exact encoding, defaulting to latin1")
        return 'latin1'

    def preview_data(self, num_rows: int = 5) -> List[List[str]]:
        """Preview the first few rows of data to verify correct parsing"""
        rows = []
        with open(self.import_manager.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            # Read and store header
            self.header = f.readline().strip()
            header_cols = self.header.split(',')
            rows.append(header_cols)  # Add header as first row
            
            # Read specified number of data rows
            csv_reader = csv.reader(f)
            for _ in range(num_rows):
                try:
                    row = next(csv_reader)
                    if row:  # Skip empty rows
                        rows.append(row)
                except StopIteration:
                    break
                except csv.Error as e:
                    self.logger.error(f"Error reading preview row: {str(e)}")
                    continue
        
        return rows

    def _calculate_optimal_chunk_size(self) -> int:
        """Calculate optimal chunk size based on available memory"""
        # Get available memory in bytes
        memory_info = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        
        # Target using no more than 10% of available memory
        target_memory = memory_info * 0.1
        
        # Estimate bytes per row (assuming average row size of 1KB)
        bytes_per_row = 1024
        
        # Calculate optimal chunk size
        optimal_size = int(target_memory / bytes_per_row)
        
        # Ensure chunk size is between reasonable bounds
        return max(min(optimal_size, 500000), 50000)

    def process_failed_chunks(self) -> Iterator[Tuple[int, str, bool]]:
        """Process only the failed chunks"""
        if not self.import_manager.state.failed_chunks:
            return
            
        expected_cols = self._count_header_columns()
        
        with open(self.import_manager.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            # Read header first
            self.header = f.readline()
            
            for chunk_start, chunk_end in self.import_manager.state.failed_chunks:
                self.logger.info(f"Processing failed chunk {chunk_start}-{chunk_end}")
                
                # Seek to the start of the failed chunk
                f.seek(chunk_start)
                
                # Read the chunk
                chunk_data = f.read(chunk_end - chunk_start)
                
                # Split into lines and clean
                lines = chunk_data.splitlines()
                current_chunk = [(i, line + '\n') for i, line in enumerate(lines, start=1)]
                
                cleaned_rows = self._clean_chunk(current_chunk, expected_cols)
                if cleaned_rows:
                    yield (chunk_start, ''.join(cleaned_rows), False)  # Never first chunk since header already processed

    def process_csv_in_chunks(self) -> Iterator[Tuple[int, str, bool]]:
        """
        Process CSV file in chunks, yielding (position, chunk, is_first_chunk) tuples.
        Skips already processed chunks based on saved state.
        """
        # If we have failed chunks, only process those
        if self.import_manager.state.failed_chunks:
            yield from self.process_failed_chunks()
            return
            
        expected_cols = self._count_header_columns()
        current_chunk = []
        current_position = 0
        is_first_chunk = self.import_manager.state.last_successful_position == 0
        
        with open(self.import_manager.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            # Always read header first to store it
            self.header = f.readline()
            header_length = f.tell()
            self.current_row_number = 1  # Start after header
            
            # Skip to last successful position if resuming
            if self.import_manager.state.last_successful_position > header_length:
                f.seek(self.import_manager.state.last_successful_position)
                self.logger.info(f"Resuming from position {self.import_manager.state.last_successful_position}")
                is_first_chunk = False
                # Estimate current row number based on position
                self.current_row_number = int(self.import_manager.state.last_successful_position / 100)  # Rough estimate
            else:
                # Reset to start if we're processing from the beginning
                f.seek(0)
            
            while True:
                # Get current position before reading
                current_position = f.tell()
                
                # Read next line
                line = f.readline()
                self.current_row_number += 1
                
                # Check for EOF
                if not line:
                    break
                
                # Skip if this chunk was already successfully processed
                if current_position <= self.import_manager.state.last_successful_position:
                    continue
                
                current_chunk.append((self.current_row_number, line))
                
                if len(current_chunk) >= self.chunk_size:
                    chunk_start_pos = current_position
                    cleaned_rows = self._clean_chunk(current_chunk, expected_cols)
                    if cleaned_rows:
                        yield (chunk_start_pos, ''.join(cleaned_rows), is_first_chunk)
                    current_chunk = []
                    is_first_chunk = False
                    
                    # Update progress and ETA
                    self.import_manager.update_progress(current_position)
            
            # Process remaining rows
            if current_chunk:
                chunk_start_pos = current_position
                cleaned_rows = self._clean_chunk(current_chunk, expected_cols)
                if cleaned_rows:
                    yield (chunk_start_pos, ''.join(cleaned_rows), is_first_chunk)

    def _count_header_columns(self) -> int:
        """Read just the header to determine the expected number of columns."""
        with open(self.import_manager.file_path, 'r', encoding=self.encoding, errors='replace') as f:
            header = f.readline().strip()
            return len(header.split(','))

    def _clean_chunk(self, chunk: List[Tuple[int, str]], expected_cols: int) -> List[str]:
        """Clean a chunk of rows, ensuring each row has the correct number of columns."""
        cleaned_rows = []
        
        for row_num, row in chunk:
            if not row.strip():
                continue
            
            try:
                parsed_row = next(csv.reader([row]))
                if len(parsed_row) == expected_cols:
                    cleaned_rows.append(row)
                else:
                    error_reason = f"Wrong number of columns: expected {expected_cols}, got {len(parsed_row)}"
                    self.import_manager.log_failed_row(row_num, row.strip(), error_reason)
            except csv.Error as e:
                error_reason = f"CSV parsing error: {str(e)}"
                self.import_manager.log_failed_row(row_num, row.strip(), error_reason)
                self.logger.warning(f"Failed to parse row {row_num}: {row[:100]}... Error: {e}")
        
        return cleaned_rows
