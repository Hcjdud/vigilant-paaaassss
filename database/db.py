import os
import logging
from urllib.parse import urlparse
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self):
        self.pool = None
        self.init_pool()
    
    def init_pool(self):
        url = os.environ.get('DATABASE_URL')
        if not url:
            logger.error("DATABASE_URL not set")
            return
        
        try:
            r = urlparse(url)
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=r.hostname,
                port=r.port,
                database=r.path[1:],
                user=r.username,
                password=r.password,
                cursor_factory=RealDictCursor
            )
            logger.info("Database pool created")
        except Exception as e:
            logger.error(f"DB error: {e}")
    
    def get_conn(self):
        if self.pool:
            try:
                return self.pool.getconn()
            except:
                return None
        return None
    
    def put_conn(self, conn):
        if self.pool and conn:
            self.pool.putconn(conn)

db_pool = DatabasePool()
