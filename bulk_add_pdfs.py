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
    cursor.execute("SELECT material_id FROM materials ORDER BY CAST(SUBSTRING(material_id, 14) AS UNSIGNED) DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        last_id = result[0]  # e.g., "BWU/MATERIAL/013"
        number = int(last_id.split('/')[-1]) + 1
        return f"BWU/MATERIAL/{number:03d}"
    else:
        return "BWU/MATERIAL/001"

def add_bulk_materials():
    """Add multiple materials at once - modify this function with your PDF details"""
    
    # MODIFY THIS LIST WITH YOUR REAL PDF DETAILS
    # Format: (filename, material_name, category, subject, description, link_or_local_path)
    new_materials = [
        # Example entries - replace with your real PDFs:
        # ("example.pdf", "Example Study Material", "Computer Science", "Programming", "Description here", "local"),
        # ("math_guide.pdf", "Mathematics Guide", "Mathematics", "Calculus", "Advanced calculus concepts", "https://drive.google.com/file/d/your_file_id/view"),
    ]
    
    if not new_materials:
        print("📝 Please edit this script and add your PDF details in the 'new_materials' list")
        print("\nFormat: (filename, material_name, category, subject, description, link_or_path)")
        print("\nExample:")
        print('("physics.pdf", "Physics Notes", "Science", "Physics", "Mechanics and thermodynamics", "local")')
        return
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    added_count = 0
    
    for filename, material_name, category, subject, description, link_type in new_materials:
        try:
            material_id = get_next_material_id()
            
            # Determine the link based on type
            if link_type == "local":
                # For local files in static/files directory
                encoded_filename = quote(filename)
                material_link = f"http://localhost:5000/static/files/{encoded_filename}"
                
                # Get file size if file exists
                file_path = os.path.join("static/files", filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                else:
                    file_size = 0
                    print(f"⚠️  Warning: {filename} not found in static/files directory")
            else:
                # For external links (Google Drive, etc.)
                material_link = link_type
                file_size = 0  # Unknown size for external files
            
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
            added_count += 1
            
        except mysql.connector.Error as e:
            print(f"❌ Error adding {material_name}: {e}")
    
    conn.close()
    print(f"\n🎉 Successfully added {added_count} materials!")
    print("\n📧 Students can now:")
    print("- Download these PDFs directly")
    print("- Share them via email")
    print("- Share them via WhatsApp")

if __name__ == "__main__":
    print("📚 Smart Student Portal - Bulk Add Materials")
    print("=" * 50)
    add_bulk_materials()
