from io import StringIO
import psycopg2
from typing import Dict
from .db_utils import DatabasePool
from ..utils.logging_config import setup_logging

class PostgresLoader:
    def __init__(self, import_manager, db_params: Dict[str, str], table_name: str):
        self.import_manager = import_manager
        self.table_name = table_name
        self.logger = setup_logging(__name__)
        self.db_pool = DatabasePool(db_params)

    def _handle_duplicates(self, conn, data: str, is_first_chunk: bool, position: int) -> bool:
        """Handle duplicate records by using a temp table approach"""
        try:
            cur = conn.cursor()
            
            # Create a temp table for the chunk
            cur.execute(f"CREATE TEMP TABLE temp_chunk (LIKE {self.table_name} INCLUDING ALL) ON COMMIT DROP;")
            
            # Copy the chunk into the temp table
            string_buffer = StringIO(data)
            cur.copy_expert(f"COPY temp_chunk FROM STDIN WITH (FORMAT CSV{', HEADER' if is_first_chunk else ''})", string_buffer)
            
            # Insert only non-duplicate records
            cur.execute(f"""
                INSERT INTO {self.table_name}
                SELECT t.* FROM temp_chunk t
                LEFT JOIN {self.table_name} m ON t.id = m.id
                WHERE m.id IS NULL;
            """)
            
            conn.commit()
            
            # Update state since we successfully processed the chunk
            self.import_manager.state.last_successful_position = position
            self.import_manager.state.processed_bytes = position
            self.import_manager.state.processed_chunks += 1
            
            # Remove this chunk from failed_chunks
            self.import_manager.state.failed_chunks = [
                (start, end) for start, end in self.import_manager.state.failed_chunks 
                if start != position
            ]
            
            self.import_manager.save_state()
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling duplicates: {str(e)}")
            conn.rollback()
            return False

    def copy_to_postgres(self, position: int, data: str, is_first_chunk: bool, retries: int = 3) -> bool:
        """Copy a chunk of cleaned data to Postgres with retry logic"""
        try:
            with self.db_pool.get_connection() as conn:
                cur = conn.cursor()
                
                # First try direct COPY
                try:
                    string_buffer = StringIO(data)
                    copy_sql = f"COPY {self.table_name} FROM STDIN WITH (FORMAT CSV{', HEADER' if is_first_chunk else ''})"
                    cur.copy_expert(copy_sql, string_buffer)
                    conn.commit()
                    
                    # Update state
                    self.import_manager.state.last_successful_position = position
                    self.import_manager.state.processed_bytes = position
                    self.import_manager.state.processed_chunks += 1
                    
                    # Remove this chunk from failed_chunks if it was successful
                    self.import_manager.state.failed_chunks = [
                        (start, end) for start, end in self.import_manager.state.failed_chunks 
                        if start != position
                    ]
                    
                    self.import_manager.save_state()
                    return True
                    
                except psycopg2.errors.UniqueViolation:
                    # If we got a duplicate key error, try the temp table approach
                    self.logger.info("Detected duplicates, using temp table approach")
                    conn.rollback()  # Reset the connection state
                    return self._handle_duplicates(conn, data, is_first_chunk, position)
                    
        except Exception as e:
            # Log detailed error information
            self.logger.error(f"Error processing chunk at position {position}:")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error message: {str(e)}")
            if isinstance(e, psycopg2.Error):
                self.logger.error(f"PostgreSQL error code: {e.pgcode}")
                self.logger.error(f"PostgreSQL error details: {e.diag.message_detail if e.diag else 'No details'}")
            
            # Add to failed chunks if not already there
            chunk_range = (position, position + len(data))
            if chunk_range not in self.import_manager.state.failed_chunks:
                self.import_manager.state.failed_chunks.append(chunk_range)
            self.import_manager.save_state()
            return False
