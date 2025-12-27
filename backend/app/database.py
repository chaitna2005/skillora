"""
Database Connection and Session Management
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from app.config import settings
from typing import Generator


class Database:
    _pool: SimpleConnectionPool = None
    
    @classmethod
    def initialize(cls):
        """Initialize database connection pool"""
        if cls._pool is None:
            cls._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                database=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD
            )
    
    @classmethod
    def close(cls):
        """Close all database connections"""
        if cls._pool:
            cls._pool.closeall()
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool"""
        if cls._pool is None:
            cls.initialize()
        
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)
    
    @classmethod
    @contextmanager
    def get_cursor(cls, commit: bool = True) -> Generator:
        """Get a cursor with automatic commit/rollback"""
        with cls.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()


# Dependency for FastAPI routes
def get_db():
    """Database dependency for FastAPI"""
    with Database.get_cursor() as cursor:
        yield cursor

