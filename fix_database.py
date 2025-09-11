import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
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
        print(f"Database connection error: {e}")
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
        print(f"✅ Database '{db_name}' created or verified")
        
        conn.close()
    except mysql.connector.Error as e:
        print(f"❌ Database creation error: {e}")

def setup_tables():
    """Create tables and add students"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Drop and recreate student_data table
        cursor.execute("DROP TABLE IF EXISTS student_data")
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
        print("✅ Student table created")
        
        print("✅ Tables recreated")
        
        # Insert students with hashed passwords
        students = [
            ('BWU/001', 'Samit', 'pass@Samit', 'samitbinku@gmail.com', '8910816531'),
            ('BWU/002', 'soumi', 'pass@soumi', 'soumidhara279@gmail.com', '9330870623'),
            ('BWU/003', 'sriparna', 'pass@sriparna', 'sriparnachatterjee45@gmail.com', '6295762865'),
            ('BWU/004', 'rajanya', 'pass@rajanya', 'rajanya_sadhu_23@gmail.com', '7908553061'),
            ('BWU/005', 'asif', 'pass@asif', 'Asif_6754@gmail.com', '9735440963'),
            ('BWU/006', 'rohit', 'pass@rohit', 'rohit_45@gmail.com', '9087654326'),
            ('BWU/007', 'bumba', 'pass@bumba', 'BuMbA.SiNgHa.8888@gmail.com', '6543289075'),
            ('BWU/008', 'sandip', 'pass@sandip', 'sandip.xor.89@gmail.com', '9876598764'),
            ('BWU/009', 'sougata', 'pass@sougata', 'sougata_2004@gmail.com', '9786543865'),
            ('BWU/010', 'aritri', 'pass@aritri', 'aritri.saha.8975@gmail.com', '8967543276'),
            ('BWU/011', 'kankana', 'pass@kankana', 'kan_kana_77@gmail.com', '9907865345'),
            ('BWU/012', 'soumyadeep', 'pass@soumyadeep', 'soumya_2005@gmail.com', '7865987654'),
            ('BWU/013', 'joyta', 'pass@joyta', 'joyta.jana_67@gmail.com', '6543789065'),
            ('BWU/014', 'ankana', 'pass@ankana', 'Ankana_das.2005@gmail.com', '7789065476'),
            ('BWU/015', 'gopi', 'pass@gopi', 'Gpoinath_mithy.890@gmail.com', '9954372786')
        ]
        
        for student_id, username, password, email, phone in students:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert student
            cursor.execute("""
                INSERT INTO student_data (id, username, email, phone, password, role, is_active, email_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (student_id, username, email, phone, hashed_password, 'student', True, True))
            
            print(f"✅ Added student: {student_id} - {username}")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n👥 Test Login Credentials:")
        print("Student ID: BWU/001, Password: pass@Samit")
        print("Student ID: BWU/002, Password: pass@soumi")
        print("Student ID: BWU/003, Password: pass@sriparna")
        print("And so on...")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Setup error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Fixing Smart Student Portal Database...")
    create_database()
    setup_tables()
