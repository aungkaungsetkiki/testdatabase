import os
import psycopg2
import logging

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Database connection function"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PGDATABASE", "railway"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT", "5432"),
            connect_timeout=5
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

async def init_db():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create user_data table
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
        
        # Create break_limits table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS break_limits (
                id SERIAL PRIMARY KEY,
                date_key TEXT NOT NULL UNIQUE,
                limit_amount INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            cur.close()
            conn.close()
