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
        
        # Administrators table - Separate from students for better security
        cursor.execute('''
            CREATE TABLE administrators (
                admin_id VARCHAR(20) PRIMARY KEY,
                admin_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_super_admin BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        logger.info("Administrators table created")
        
        # Students table - Only for student data
        cursor.execute('''
            CREATE TABLE student_data (
                id VARCHAR(20) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        logger.info("Student data table created")
        
        # Materials table with enhanced features
        cursor.execute('''
            CREATE TABLE materials (
                material_id INT AUTO_INCREMENT PRIMARY KEY,
                material_name VARCHAR(255) NOT NULL,
                material_link TEXT NOT NULL,
                file_type VARCHAR(50),
                file_size BIGINT,
                category VARCHAR(100),
                subject VARCHAR(100),
                description TEXT,
                tags TEXT,
                uploader_id VARCHAR(20) NOT NULL,
                is_public BOOLEAN DEFAULT TRUE,
                download_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (material_name),
                INDEX idx_category (category),
                INDEX idx_subject (subject),
                INDEX idx_public (is_public),
                INDEX idx_created (created_at),
                INDEX idx_uploader (uploader_id),
                FULLTEXT idx_search (material_name, description, tags)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        logger.info("Materials table created")
        
        # Categories table for better organization
        cursor.execute('''
            CREATE TABLE categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                color VARCHAR(7) DEFAULT '#007bff',
                icon VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        logger.info("Categories table created")
        
        # User sessions table for better session management
        cursor.execute('''
            CREATE TABLE user_sessions (
                id VARCHAR(128) PRIMARY KEY,
                user_id VARCHAR(20) NOT NULL,
                user_type ENUM('admin', 'student') NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                INDEX idx_user (user_id),
                INDEX idx_expires (expires_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        logger.info("User sessions table created")
        
        # Activity logs for security and analytics
        cursor.execute('''
            CREATE TABLE activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(20),
                user_type ENUM('admin', 'student'),
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
        logger.info("Activity logs table created")
        
        # User favorites
        cursor.execute('''
            CREATE TABLE user_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(20) NOT NULL,
                material_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_favorite (user_id, material_id),
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        logger.info("User favorites table created")
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(20) NOT NULL,
                user_type ENUM('admin', 'student') NOT NULL,
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
        logger.info("Notifications table created")
        
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
        
        cursor.executemany("""
            INSERT INTO categories (name, description, color, icon) 
            VALUES (%s, %s, %s, %s)
        """, default_categories)
        logger.info("Default categories inserted")
        
        # Insert your admin account (as requested)
        admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO administrators (admin_id, admin_name, email, phone, password, is_super_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('admin', 'Atrey (Creator)', 'atrey@smartportal.com', '1234567890', admin_password, True))
        logger.info("Main administrator account created (ID: admin)")
        
        # Insert sample materials uploaded by admin
        sample_materials = [
            ('Introduction to Python Programming', 'https://drive.google.com/file/d/1abc123', 'pdf', 2048, 'Programming', 'Python Basics', 'Complete guide to Python programming fundamentals', 'python,programming,basics', 'admin'),
            ('Database Design Principles', 'https://drive.google.com/file/d/2def456', 'pdf', 1536, 'Database', 'SQL Fundamentals', 'Learn database design and SQL queries', 'database,sql,design', 'admin'),
            ('Web Development with Flask', 'https://drive.google.com/file/d/3ghi789', 'pdf', 3072, 'Web Development', 'Flask Framework', 'Building web applications with Python Flask', 'flask,web,python', 'admin'),
            ('Mathematics for Computer Science', 'https://drive.google.com/file/d/4jkl012', 'pdf', 4096, 'Mathematics', 'Discrete Math', 'Mathematical foundations for CS students', 'math,discrete,computer-science', 'admin'),
            ('Data Structures and Algorithms', 'https://drive.google.com/file/d/5mno345', 'pdf', 2560, 'Computer Science', 'Algorithms', 'Essential algorithms and data structures', 'algorithms,data-structures,programming', 'admin')
        ]
        
        cursor.executemany("""
            INSERT INTO materials (material_name, material_link, file_type, file_size, category, subject, description, tags, uploader_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, sample_materials)
        logger.info("Sample materials inserted (uploaded by admin)")
        
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"Table creation error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Setting up Smart Student Portal Database with Admin System...")
    
    # Create database
    create_database()
    
    # Setup tables
    if setup_tables():
        print("✅ Database tables created successfully")
        print("✅ Sample data inserted successfully")
        print("\n🎉 Database setup completed!")
        print("\n👨‍💼 Administrator Account Created:")
        print("Username: admin")
        print("Password: admin123")
        print("Role: Super Administrator")
        print("\n🔐 Features:")
        print("- Separate admin and student authentication")
        print("- Admin can manage students and upload materials")
        print("- Students can only view, search, and download materials")
        print("- Enhanced security and session management")
        print("\nRemember to change the admin password after first login!")
        
    else:
        print("❌ Database setup failed")
