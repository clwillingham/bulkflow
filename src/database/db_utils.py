import psycopg2
import psycopg2.pool
from contextlib import contextmanager
from typing import Dict, Generator
from psycopg2.extensions import connection

class DatabasePool:
    def __init__(self, db_params: Dict[str, str]):
        self.pool = self._create_pool(db_params)
    
    def _create_pool(self, db_params: Dict[str, str]) -> psycopg2.pool.ThreadedConnectionPool:
        """Create a connection pool for better performance"""
        return psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            **db_params
        )
    
    @contextmanager
    def get_connection(self) -> Generator[connection, None, None]:
        """Get a connection from the pool with context management"""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    def close(self):
        """Close the connection pool"""
        if self.pool:
            self.pool.closeall()
