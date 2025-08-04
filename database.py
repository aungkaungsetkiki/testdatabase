import os
import logging
import psycopg2
from psycopg2 import OperationalError, sql
from psycopg2.extras import DictCursor
import time
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 2

    def get_db_connection(self):
        """Establish PostgreSQL connection with retry mechanism"""
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                conn = psycopg2.connect(
                    dbname=os.getenv("PGDATABASE", "railway"),
                    user=os.getenv("PGUSER", "postgres"),
                    password=os.getenv("PGPASSWORD"),
                    host=os.getenv("PGHOST"),
                    port=os.getenv("PGPORT", "5432"),
                    connect_timeout=5,
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=3
                )
                logger.info("Database connection established")
                return conn
                
            except OperationalError as e:
                retry_count += 1
                last_error = str(e)
                logger.warning(f"Connection attempt {retry_count} failed: {last_error}")
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
        
        logger.error(f"Max retries reached. Last error: {last_error}")
        raise OperationalError(f"Could not connect to database after {self.max_retries} attempts. Error: {last_error}")

    async def init_db(self):
        """Initialize database tables"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Create tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    date_key TEXT NOT NULL,
                    number INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS break_limits (
                    id SERIAL PRIMARY KEY,
                    date_key TEXT NOT NULL UNIQUE,
                    limit_amount INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                cur.close()
                conn.close()

    async def save_user_bet(self, username: str, date_key: str, number: int, amount: int) -> bool:
        """Save user bet to database"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute(
                "INSERT INTO user_data (username, date_key, number, amount) VALUES (%s, %s, %s, %s)",
                (username, date_key, number, amount)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving bet: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                cur.close()
                conn.close()

    async def get_user_bets(self, username: Optional[str] = None, date_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve user bets"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=DictCursor)
            
            query = "SELECT * FROM user_data"
            conditions = []
            params = []
            
            if username:
                conditions.append("username = %s")
                params.append(username)
            if date_key:
                conditions.append("date_key = %s")
                params.append(date_key)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
            
        except Exception as e:
            logger.error(f"Error fetching bets: {str(e)}")
            return []
        finally:
            if 'conn' in locals():
                cur.close()
                conn.close()

# Initialize database instance
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Test database connection
    try:
        conn = db_manager.get_db_connection()
        print("✅ Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
