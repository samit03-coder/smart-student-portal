#!/usr/bin/env python3
"""
Final Check and Run Script for Smart Student Portal
This script performs final checks and starts the application
"""

import os
import sys
import mysql.connector
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

def check_database_connection():
    """Check if database connection is working"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "nopass"),
            database=os.getenv("DB_NAME", "smart_portal"),
            port=int(os.getenv("DB_PORT", "3306"))
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM materials")
        material_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM student_data")
        student_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Database Connection: SUCCESS")
        print(f"✅ Materials in database: {material_count}")
        print(f"✅ Students in database: {student_count}")
        return True
    except Exception as e:
        print(f"❌ Database Connection: FAILED - {e}")
        return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        "main_admin.py",
        "static/js/main.js",
        "static/css/style.css",
        "templates/admin_dashboard.html",
        "templates/admin_profile.html",
        ".env"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_pdf_files():
    """Check PDF files in static/files directory"""
    pdf_dir = "static/files"
    if not os.path.exists(pdf_dir):
        print(f"❌ PDF directory not found: {pdf_dir}")
        return False
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    print(f"✅ PDF files found: {len(pdf_files)}")
    for pdf in pdf_files[:5]:  # Show first 5
        print(f"   📄 {pdf}")
    if len(pdf_files) > 5:
        print(f"   ... and {len(pdf_files) - 5} more")
    
    return len(pdf_files) > 0

def main():
    print("🔧 Smart Student Portal - Final Check")
    print("=" * 50)
    
    # Check environment file
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    # Run all checks
    checks = [
        check_required_files(),
        check_pdf_files(),
        check_database_connection()
    ]
    
    if all(checks):
        print("\n🎉 ALL CHECKS PASSED!")
        print("\n🚀 Starting Smart Student Portal...")
        print("=" * 50)
        print("📱 Access URLs:")
        print("   🏠 Main Portal: http://localhost:5000")
        print("   👨‍💼 Admin Login: http://localhost:5000/admin/login")
        print("   👨‍🎓 Student Login: http://localhost:5000/login")
        print("\n📋 Default Admin Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n📋 Sample Student Credentials:")
        print("   ID: BWU/001, Password: pass@Samit")
        print("   ID: BWU/002, Password: pass@soumi")
        print("   ID: BWU/003, Password: pass@sriparna")
        print("\n⚡ Features Ready:")
        print("   ✅ PDF Download")
        print("   ✅ Email Sharing")
        print("   ✅ WhatsApp Sharing")
        print("   ✅ Admin Panel")
        print("   ✅ Student Management")
        print("   ✅ Material Upload")
        print("\n" + "=" * 50)
        
        # Start the application
        try:
            subprocess.run([sys.executable, "main_admin.py"], check=True)
        except KeyboardInterrupt:
            print("\n\n👋 Application stopped by user")
        except Exception as e:
            print(f"\n❌ Error starting application: {e}")
        
        return True
    else:
        print("\n❌ SOME CHECKS FAILED!")
        print("Please fix the issues above before running the portal.")
        return False

if __name__ == "__main__":
    main()
