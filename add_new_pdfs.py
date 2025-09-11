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

def get_next_material_id():
    """Get the next available BWU/MATERIAL/XXX ID"""
    conn = get_db_connection()
    if not conn:
        return "BWU/MATERIAL/014"
    
    cursor = conn.cursor()
    cursor.execute("SELECT material_id FROM materials ORDER BY material_id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        last_id = result[0]  # e.g., "BWU/MATERIAL/013"
        number = int(last_id.split('/')[-1]) + 1
        return f"BWU/MATERIAL/{number:03d}"
    else:
        return "BWU/MATERIAL/001"

def scan_and_add_pdfs():
    """Scan static/files directory and add new PDFs to database"""
    files_dir = "static/files"
    
    if not os.path.exists(files_dir):
        print(f"❌ Directory {files_dir} not found")
        return
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    # Get existing files from database
    cursor.execute("SELECT material_link FROM materials WHERE material_link LIKE 'http://localhost:5000/static/files/%'")
    existing_files = {row[0].split('/')[-1].replace('%20', ' ') for row in cursor.fetchall()}
    
    # Scan for PDF files
    pdf_files = [f for f in os.listdir(files_dir) if f.lower().endswith('.pdf')]
    new_files = [f for f in pdf_files if f not in existing_files]
    
    if not new_files:
        print("✅ No new PDF files found to add")
        return
    
    print(f"📚 Found {len(new_files)} new PDF files:")
    for i, filename in enumerate(new_files, 1):
        print(f"{i}. {filename}")
    
    print("\n" + "="*50)
    print("For each file, provide:")
    print("1. Material Name (or press Enter to use filename)")
    print("2. Category (e.g., Computer Science, Mathematics)")
    print("3. Subject (e.g., Data Structures, Calculus)")
    print("4. Description")
    print("="*50 + "\n")
    
    added_count = 0
    
    for filename in new_files:
        print(f"\n📄 Processing: {filename}")
        
        # Get material details from user
        material_name = input(f"Material Name [{filename[:-4]}]: ").strip()
        if not material_name:
            material_name = filename[:-4].replace('_', ' ').replace('-', ' ')
        
        category = input("Category: ").strip()
        if not category:
            category = "General"
        
        subject = input("Subject: ").strip()
        if not subject:
            subject = "Study Material"
        
        description = input("Description: ").strip()
        if not description:
            description = f"Study material: {material_name}"
        
        # Generate material details
        material_id = get_next_material_id()
        file_size = os.path.getsize(os.path.join(files_dir, filename))
        encoded_filename = quote(filename)
        material_link = f"http://localhost:5000/static/files/{encoded_filename}"
        tags = f"{category.lower()},{subject.lower()},pdf,study-material"
        
        try:
            # Insert into database
            cursor.execute("""
                INSERT INTO materials 
                (material_id, material_name, material_link, file_type, file_size, 
                 category, subject, description, tags, uploader_id, is_public, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (material_id, material_name, material_link, 'pdf', file_size, 
                  category, subject, description, tags, 'admin', True))
            
            print(f"✅ Added: {material_id} - {material_name}")
            added_count += 1
            
        except mysql.connector.Error as e:
            print(f"❌ Error adding {filename}: {e}")
    
    conn.close()
    print(f"\n🎉 Successfully added {added_count} new PDF materials!")

if __name__ == "__main__":
    print("📚 Smart Student Portal - Add New PDFs")
    print("This script will scan static/files directory and add new PDFs to the database")
    print("-" * 70)
    scan_and_add_pdfs()
