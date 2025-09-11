import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "dpg-ed313pju1brs73a5g3g-a.oregon-postgres.render.com"),
            user=os.getenv("DB_USER", "smart_user"),
            password=os.getenv("DB_PASS", "p4xn6JGJTMEkeA5tzKzDDJLSdxgp7xKu"),
            database=os.getenv("DB_NAME", "smart_portal_pukh"),
            port=int(os.getenv("DB_PORT", "5432")),
            sslmode='require'
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def create_database():
    """Database already exists on Render, skip creation"""
    logger.info("Using existing Render PostgreSQL database")

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def setup_tables():
    """Create all necessary tables with proper schema"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Drop existing tables if they exist (in correct order)
        tables_to_drop = [
            'smart_portal_notifications', 'smart_portal_user_favorites', 'smart_portal_activity_logs', 
            'smart_portal_user_sessions', 'smart_portal_materials', 'smart_portal_categories', 'smart_portal_admins', 'smart_portal_students'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Dropped table {table} if it existed")
        
        # Create student_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_portal_students (
                id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                role VARCHAR(20) DEFAULT 'student',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
        """)
        
        # Create administrators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_portal_admins (
                admin_id VARCHAR(50) PRIMARY KEY,
                admin_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                is_super_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
        """)
        
        # Create materials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_portal_materials (
                material_id SERIAL PRIMARY KEY,
                material_name VARCHAR(200) NOT NULL,
                material_link TEXT NOT NULL,
                category VARCHAR(100) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                description TEXT,
                is_public BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("All tables created successfully")
        
        # Insert default admin user
        admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO smart_portal_admins (admin_id, admin_name, email, password, phone, is_super_admin) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (admin_id) DO NOTHING
        """, ('admin001', 'System Administrator', 'admin@smartportal.com', admin_password, '+1234567890', True))
        logger.info("Default admin user created (ID: admin, Password: admin123)")
        
        # Insert sample student (password: student123)
        student_password = hash_password('student123')
        cursor.execute("""
            INSERT INTO smart_portal_students (id, username, email, password, phone) 
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, ('student001', 'Test Student', 'student@test.com', student_password, '1234567890'))
        logger.info("Sample student created (ID: student001, Password: student123)")
        
        # Insert sample materials
        sample_materials = [
            ('Introduction to Python Programming', 'https://drive.google.com/file/d/1abc123', 'Programming', 'Python Basics', 'Complete guide to Python programming fundamentals', 'admin001'),
            ('Database Design Principles', 'https://drive.google.com/file/d/2def456', 'Database', 'SQL Fundamentals', 'Learn database design and SQL queries', 'admin001'),
            ('Web Development with Flask', 'https://drive.google.com/file/d/3ghi789', 'Web Development', 'Flask Framework', 'Building web applications with Python Flask', 'admin001'),
            ('Mathematics for Computer Science', 'https://drive.google.com/file/d/4jkl012', 'Mathematics', 'Discrete Math', 'Mathematical foundations for CS students', 'admin001'),
            ('Data Structures and Algorithms', 'https://drive.google.com/file/d/5mno345', 'Computer Science', 'Algorithms', 'Essential algorithms and data structures', 'admin001')
        ]
        
        for material in sample_materials:
            cursor.execute("""
                INSERT INTO smart_portal_materials (material_name, material_link, category, subject, description, created_by) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, material)
        logger.info("Sample materials inserted")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Table creation error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Setting up Smart Student Portal Database...")
    
    # Create database
    create_database()
    
    # Setup tables
    if setup_tables():
        print("✅ Database setup completed successfully!")
        print("\n🔑 Default Login Credentials:")
        print("Admin Login:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nStudent Login:")
        print("  Username: student001")
        print("  Password: student123")
        print("\n⚠️  Remember to change default passwords after first login!")
        
    else:
        print("❌ Database setup failed")
