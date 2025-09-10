import mysql.connector
import os
import bcrypt
from dotenv import load_dotenv

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

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def add_students():
    # Your existing students data
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
    
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    try:
        for student_id, username, password, email, phone in students:
            # Check if student already exists
            cursor.execute("SELECT id FROM student_data WHERE id = %s", (student_id,))
            if cursor.fetchone():
                print(f"Student {student_id} already exists, skipping...")
                continue
            
            # Hash the password
            hashed_password = hash_password(password)
            
            # Insert student
            cursor.execute("""
                INSERT INTO student_data (id, username, email, phone, password, is_active, email_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, TRUE, TRUE, NOW())
            """, (student_id, username, email, phone, hashed_password.decode('utf-8')))
            
            print(f"✅ Added student: {student_id} - {username}")
        
        print("\n🎉 All students added successfully!")
        print("\n📝 Student Login Examples:")
        print("Student ID: BWU/001, Password: pass@Samit")
        print("Student ID: BWU/002, Password: pass@soumi")
        print("Student ID: BWU/003, Password: pass@sriparna")
        print("And so on...")
        
    except mysql.connector.Error as e:
        print(f"Error adding students: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Adding existing students to admin database...")
    add_students()
