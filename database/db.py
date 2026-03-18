# database/db.py
import os
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabasePool:
    """Пул соединений с PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        self.init_pool()
    
    def init_pool(self):
        """Инициализация пула соединений"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL not set")
                return
            
            result = urlparse(database_url)
            
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=result.hostname,
                port=result.port,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                cursor_factory=RealDictCursor
            )
            logger.info("Database pool created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
    
    def get_conn(self):
        """Получить соединение из пула"""
        if self.pool:
            try:
                return self.pool.getconn()
            except Exception as e:
                logger.error(f"Error getting connection: {e}")
        return None
    
    def put_conn(self, conn):
        """Вернуть соединение в пул"""
        if self.pool and conn:
            self.pool.putconn(conn)
    
    def close_all(self):
        """Закрыть все соединения"""
        if self.pool:
            self.pool.closeall()
            logger.info("All database connections closed")

# Глобальный экземпляр пула
db_pool = DatabasePool()
