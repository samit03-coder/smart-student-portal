import mysql.connector
import os
from dotenv import load_dotenv
import logging
import bcrypt

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "nopass"),
            database=os.getenv("DB_NAME", "smart_portal"),
            port=int(os.getenv("DB_PORT", "3306")),
            autocommit=True,
            charset='utf8mb4',
            use_unicode=True
        )
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def create_database():
    """Create database if it doesn't exist"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "nopass"),
            port=int(os.getenv("DB_PORT", "3306"))
        )
        cursor = conn.cursor()
        
        db_name = os.getenv("DB_NAME", "smart_portal")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        logger.info(f"Database '{db_name}' created or verified")
        
        conn.close()
    except mysql.connector.Error as e:
        logger.error(f"Database creation error: {e}")

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
            'notifications', 'user_favorites', 'activity_logs', 
            'user_sessions', 'materials', 'categories', 'administrators', 'student_data'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"Dropped table {table} if it existed")
        
        # Student data table
        cursor.execute('''
            CREATE TABLE student_data (
                id VARCHAR(20) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('student', 'teacher', 'admin') DEFAULT 'student',
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_role (role),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Administrators table
        cursor.execute('''
            CREATE TABLE administrators (
                admin_id VARCHAR(20) PRIMARY KEY,
                admin_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_super_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Materials table
        cursor.execute('''
            CREATE TABLE materials (
                material_id VARCHAR(50) PRIMARY KEY,
                material_name VARCHAR(255) NOT NULL,
                material_link TEXT NOT NULL,
                file_type VARCHAR(50),
                file_size BIGINT DEFAULT 0,
                category VARCHAR(100),
                subject VARCHAR(100),
                description TEXT,
                tags TEXT,
                uploader_id VARCHAR(20),
                is_public BOOLEAN DEFAULT TRUE,
                download_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (material_name),
                INDEX idx_category (category),
                INDEX idx_subject (subject),
                INDEX idx_public (is_public),
                INDEX idx_created (created_at),
                FULLTEXT idx_search (material_name, description, tags)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        logger.info("All tables created successfully")
        
        # Insert default admin user (password: admin123)
        admin_password = hash_password('admin123')
        cursor.execute("""
            INSERT INTO administrators (admin_id, admin_name, email, password, is_super_admin, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('admin', 'System Administrator', 'admin@smartportal.com', admin_password, True, True))
        logger.info("Default admin user created (ID: admin, Password: admin123)")
        
        # Insert sample student (password: student123)
        student_password = hash_password('student123')
        cursor.execute("""
            INSERT INTO student_data (id, username, email, phone, password, role, email_verified, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ('student001', 'Test Student', 'student@test.com', '1234567890', student_password, 'student', True, True))
        logger.info("Sample student created (ID: student001, Password: student123)")
        
        # Insert sample materials
        sample_materials = [
            ('BWU/MAT/001', 'Introduction to Python Programming', 'https://drive.google.com/file/d/1abc123', 'pdf', 2048000, 'Programming', 'Python Basics', 'Complete guide to Python programming fundamentals', 'python,programming,basics', 'admin'),
            ('BWU/MAT/002', 'Database Design Principles', 'https://drive.google.com/file/d/2def456', 'pdf', 1536000, 'Database', 'SQL Fundamentals', 'Learn database design and SQL queries', 'database,sql,design', 'admin'),
            ('BWU/MAT/003', 'Web Development with Flask', 'https://drive.google.com/file/d/3ghi789', 'pdf', 3072000, 'Web Development', 'Flask Framework', 'Building web applications with Python Flask', 'flask,web,python', 'admin'),
            ('BWU/MAT/004', 'Mathematics for Computer Science', 'https://drive.google.com/file/d/4jkl012', 'pdf', 4096000, 'Mathematics', 'Discrete Math', 'Mathematical foundations for CS students', 'math,discrete,computer-science', 'admin'),
            ('BWU/MAT/005', 'Data Structures and Algorithms', 'https://drive.google.com/file/d/5mno345', 'pdf', 2560000, 'Computer Science', 'Algorithms', 'Essential algorithms and data structures', 'algorithms,data-structures,programming', 'admin')
        ]
        
        cursor.executemany("""
            INSERT INTO materials (material_id, material_name, material_link, file_type, file_size, category, subject, description, tags, uploader_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, sample_materials)
        logger.info("Sample materials inserted")
        
        return True
        
    except mysql.connector.Error as e:
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
