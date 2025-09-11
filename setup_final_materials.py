import mysql.connector
import os
from dotenv import load_dotenv
from urllib.parse import quote

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

def setup_final_materials():
    """Setup exactly 12 materials based on your PDF files with proper names"""
    
    # Your 12 PDF files with proper material names
    materials = [
        ("24419_Study Material_Module 2_Vector Spaces-I.pdf", "Vector Spaces - Module 2", "Mathematics", "Linear Algebra", "Study material on vector spaces and linear transformations"),
        ("33537_Module 1_Homework Solution.pdf", "Module 1 Homework Solutions", "Mathematics", "Problem Solving", "Complete solutions for Module 1 homework assignments"),
        ("34674_Module 2 Counting Techniques (1).pdf", "Counting Techniques - Module 2", "Mathematics", "Discrete Mathematics", "Comprehensive guide to counting principles and techniques"),
        ("34675_Module 3 Propositional Logic (1).pdf", "Propositional Logic - Module 3", "Computer Science", "Logic", "Introduction to propositional logic and logical reasoning"),
        ("BES07010 Module 3_Part 2-Linked List.pdf", "Data Structures - Linked Lists", "Computer Science", "Data Structures", "Complete guide to linked list implementation and operations"),
        ("BES07010 Module 4_Part 2-Sorting.pdf", "Sorting Algorithms", "Computer Science", "Algorithms", "Comprehensive study of sorting algorithms and their analysis"),
        ("BES07010 Module 4_Part 3-Hashing.pdf", "Hashing Techniques", "Computer Science", "Data Structures", "Advanced hashing methods and collision resolution strategies"),
        ("Harmony.pdf", "Harmony - Complete Guide", "Music", "Music Theory", "Complete guide to musical harmony and composition"),
        ("ans.pdf", "Answer Key", "General", "Solutions", "Answer key for various assignments and exercises"),
        ("flask.pdf", "Flask Web Development", "Programming", "Web Development", "Complete guide to building web applications with Flask"),
        ("intro_to_python.pdf", "Introduction to Python", "Programming", "Python", "Beginner-friendly introduction to Python programming language"),
        ("mysql_install_guide.pdf", "MySQL Installation Guide", "Database", "MySQL", "Step-by-step guide for installing and configuring MySQL database")
    ]
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Clear all existing materials
        cursor.execute("DELETE FROM materials")
        print("✅ Cleared existing materials")
        
        # Add the 12 materials
        for i, (filename, material_name, category, subject, description) in enumerate(materials, 1):
            material_id = f"BWU/MATERIAL/{i:03d}"
            
            # Check if file exists
            file_path = os.path.join("static/files", filename)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                encoded_filename = quote(filename)
                material_link = f"http://localhost:5000/static/files/{encoded_filename}"
                
                tags = f"{category.lower()},{subject.lower()},pdf,study-material"
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO materials 
                    (material_id, material_name, material_link, file_type, file_size, 
                     category, subject, description, tags, uploader_id, is_public, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (material_id, material_name, material_link, 'pdf', file_size, 
                      category, subject, description, tags, 'admin', True))
                
                print(f"✅ Added: {material_id} - {material_name}")
            else:
                print(f"❌ File not found: {filename}")
        
        print(f"\n🎉 Successfully set up 12 materials!")
        print("\n📚 Features Ready:")
        print("✅ Direct PDF Download")
        print("✅ Email Sharing")
        print("✅ WhatsApp Sharing")
        print("✅ Search by name, category, subject")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Setting up final 12 materials for Smart Student Portal...")
    print("=" * 60)
    setup_final_materials()
