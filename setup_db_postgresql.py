import psycopg2
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get PostgreSQL database connection with error handling"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "smart_portal"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def setup_database():
    """Create database tables"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create materials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                material_id SERIAL PRIMARY KEY,
                material_name VARCHAR(200) NOT NULL,
                material_link TEXT NOT NULL,
                category VARCHAR(100),
                subject VARCHAR(100),
                description TEXT,
                is_public BOOLEAN DEFAULT TRUE,
                download_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database tables created successfully")
        
        # Insert default admin if not exists
        cursor.execute("SELECT COUNT(*) FROM admins WHERE username = %s", ('admin',))
        if cursor.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            admin_password = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO admins (username, email, password_hash) 
                VALUES (%s, %s, %s)
            """, ('admin', 'admin@smartportal.com', admin_password))
            conn.commit()
            logger.info("Default admin created: username=admin, password=admin123")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database setup failed: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    logger.info("Setting up PostgreSQL database...")
    if setup_database():
        logger.info("Database setup completed successfully!")
    else:
        logger.error("Database setup failed!")
