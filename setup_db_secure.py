import mysql.connector
import os
from dotenv import load_dotenv
import logging

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

def setup_tables():
    """Create all necessary tables with proper schema"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Users table with enhanced security
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_data (
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
        
        # Materials table with enhanced features
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                material_id INT AUTO_INCREMENT PRIMARY KEY,
                material_name VARCHAR(255) NOT NULL,
                material_link TEXT NOT NULL,
                file_type VARCHAR(50),
                file_size BIGINT,
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
        
        # User sessions table for better session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id VARCHAR(128) PRIMARY KEY,
                user_id VARCHAR(20) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                INDEX idx_user (user_id),
                INDEX idx_expires (expires_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Activity logs for security and analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(20),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id VARCHAR(50),
                ip_address VARCHAR(45),
                user_agent TEXT,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_action (action),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Categories table for better organization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                color VARCHAR(7) DEFAULT '#007bff',
                icon VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # User favorites
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(20) NOT NULL,
                material_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_favorite (user_id, material_id),
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(20) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                action_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_read (is_read),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        logger.info("All tables created successfully")
        
        # Insert default categories
        default_categories = [
            ('PDF Documents', 'PDF study materials and documents', '#dc3545', 'file-pdf'),
            ('Images', 'Images, diagrams, and visual materials', '#28a745', 'image'),
            ('Presentations', 'PowerPoint presentations and slides', '#ffc107', 'presentation'),
            ('Documents', 'Word documents and text files', '#17a2b8', 'file-word'),
            ('Videos', 'Video lectures and tutorials', '#6f42c1', 'video'),
            ('Audio', 'Audio lectures and recordings', '#fd7e14', 'volume-up'),
            ('Code', 'Programming code and scripts', '#20c997', 'code'),
            ('Other', 'Other miscellaneous materials', '#6c757d', 'file')
        ]
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO categories (name, description, color, icon) 
                VALUES (%s, %s, %s, %s)
            """, default_categories)
            logger.info("Default categories inserted")
        
        # Insert sample admin user (password: admin123)
        cursor.execute("SELECT COUNT(*) FROM student_data WHERE id = 'admin'")
        if cursor.fetchone()[0] == 0:
            import bcrypt
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                INSERT INTO student_data (id, username, email, phone, password, role, email_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('admin', 'Administrator', 'admin@smartportal.com', '1234567890', admin_password, 'admin', True))
            logger.info("Default admin user created (ID: admin, Password: admin123)")
        
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Table creation error: {e}")
        return False
    finally:
        conn.close()

def insert_sample_data():
    """Insert sample data for testing"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Insert sample materials
        sample_materials = [
            ('Introduction to Python Programming', 'https://drive.google.com/file/d/1abc123', 'pdf', 'Programming', 'Python Basics', 'Complete guide to Python programming fundamentals'),
            ('Database Design Principles', 'https://drive.google.com/file/d/2def456', 'pdf', 'Database', 'SQL Fundamentals', 'Learn database design and SQL queries'),
            ('Web Development with Flask', 'https://drive.google.com/file/d/3ghi789', 'pdf', 'Web Development', 'Flask Framework', 'Building web applications with Python Flask'),
            ('Mathematics for Computer Science', 'https://drive.google.com/file/d/4jkl012', 'pdf', 'Mathematics', 'Discrete Math', 'Mathematical foundations for CS students'),
            ('Data Structures and Algorithms', 'https://drive.google.com/file/d/5mno345', 'pdf', 'Computer Science', 'Algorithms', 'Essential algorithms and data structures')
        ]
        
        cursor.execute("SELECT COUNT(*) FROM materials")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO materials (material_name, material_link, file_type, category, subject, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, sample_materials)
            logger.info("Sample materials inserted")
        
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Sample data insertion error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Setting up Smart Student Portal Database...")
    
    # Create database
    create_database()
    
    # Setup tables
    if setup_tables():
        print("✅ Database tables created successfully")
        
        # Insert sample data
        if insert_sample_data():
            print("✅ Sample data inserted successfully")
        
        print("\n🎉 Database setup completed!")
        print("\nDefault Admin Account:")
        print("Username: admin")
        print("Password: admin123")
        print("\nRemember to change the admin password after first login!")
        
    else:
        print("❌ Database setup failed")
