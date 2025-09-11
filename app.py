from flask import Flask, render_template, request, redirect, session, flash, jsonify
import mysql.connector
import os
import bcrypt
import secrets
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with error handling"""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "nopass"),
            database=os.getenv("DB_NAME", "smart_portal"),
            port=int(os.getenv("DB_PORT", "3306")),
            autocommit=True,
            charset='utf8mb4',
            use_unicode=True
        )
    except mysql.connector.Error as e:
        logger.error(f"Database error: {e}")
        return None

def verify_password(password, hashed):
    """Verify password against hash - handle both string and bytes"""
    try:
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

@app.route('/')
def index():
    if 'admin' in session:
        return redirect('/admin/dashboard')
    elif 'student' in session:
        return redirect('/student/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin' in session or 'student' in session:
        return redirect('/')
    
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '')
        
        if not user_id or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed. Please try again later.', 'error')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check admin first
            cursor.execute("SELECT * FROM administrators WHERE admin_id = %s AND is_active = TRUE", (user_id,))
            admin = cursor.fetchone()
            
            if admin and verify_password(password, admin['password']):
                session['admin'] = {
                    'id': admin['admin_id'],
                    'name': admin['admin_name'],
                    'email': admin['email'],
                    'is_super_admin': admin.get('is_super_admin', False)
                }
                session.permanent = True
                cursor.execute("UPDATE administrators SET last_login = NOW() WHERE admin_id = %s", (user_id,))
                logger.info(f"Admin login successful: {user_id}")
                flash('Welcome Administrator!', 'success')
                return redirect('/admin/dashboard')
            
            # Check student
            cursor.execute("SELECT * FROM student_data WHERE id = %s AND is_active = TRUE", (user_id,))
            student = cursor.fetchone()
            
            if student and verify_password(password, student['password']):
                session['student'] = {
                    'id': student['id'],
                    'username': student['username'],
                    'email': student['email'],
                    'phone': student['phone'],
                    'role': student.get('role', 'student')
                }
                session.permanent = True
                cursor.execute("UPDATE student_data SET last_login = NOW() WHERE id = %s", (user_id,))
                logger.info(f"Student login successful: {user_id}")
                flash('Login successful! Welcome back!', 'success')
                return redirect('/student/dashboard')
            
            flash('Invalid credentials. Please check your ID and password.', 'error')
            
        except mysql.connector.Error as e:
            logger.error(f"Login error: {e}")
            flash('Login failed. Please try again later.', 'error')
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash('Admin access required.', 'error')
        return redirect('/login')
    
    admin = session['admin']
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    stats = {'total_students': 0, 'total_materials': 0, 'recent_logins': 0}
    materials = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get stats
            cursor.execute("SELECT COUNT(*) as count FROM student_data WHERE is_active = TRUE")
            stats['total_students'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM materials")
            stats['total_materials'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM student_data WHERE last_login >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
            stats['recent_logins'] = cursor.fetchone()['count']
            
            # Get materials
            if search:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    WHERE material_name LIKE %s OR category LIKE %s OR subject LIKE %s
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
            materials = cursor.fetchall()
            
        except mysql.connector.Error as e:
            logger.error(f"Admin dashboard error: {e}")
        finally:
            conn.close()
    
    return render_template('admin_dashboard.html', admin=admin, materials=materials, search=search, stats=stats)

@app.route('/student/dashboard')
def student_dashboard():
    if 'student' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect('/login')
    
    student = session['student']
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    materials = []
    stats = {'total_materials': 0}
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get stats
            cursor.execute("SELECT COUNT(*) as count FROM materials WHERE is_public = TRUE")
            stats['total_materials'] = cursor.fetchone()['count']
            
            # Get materials
            if search:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    WHERE is_public = TRUE AND (material_name LIKE %s OR category LIKE %s OR subject LIKE %s)
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    WHERE is_public = TRUE
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
            materials = cursor.fetchall()
            
        except mysql.connector.Error as e:
            logger.error(f"Student dashboard error: {e}")
        finally:
            conn.close()
    
    return render_template('student_dashboard.html', student=student, materials=materials, search=search, stats=stats)

@app.route('/profile')
def profile():
    if 'admin' in session:
        return render_template('admin_profile.html', admin=session['admin'])
    elif 'student' in session:
        return render_template('student_profile.html', student=session['student'])
    else:
        return redirect('/login')

@app.route('/api/search')
def api_search():
    if 'student' not in session and 'admin' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'materials': []})
    
    conn = get_db_connection()
    materials = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT material_id, material_name, material_link, category, subject
                FROM materials 
                WHERE is_public = TRUE AND (material_name LIKE %s OR category LIKE %s OR subject LIKE %s)
                ORDER BY material_name
                LIMIT 10
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            
            materials = cursor.fetchall()
            
        except mysql.connector.Error as e:
            logger.error(f"Search error: {e}")
        finally:
            conn.close()
    
    return jsonify({'materials': materials})

@app.route('/api/send_email', methods=['POST'])
def api_send_email():
    if 'student' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    material_name = data.get('material_name')
    material_link = data.get('material_link')
    
    if not all([material_name, material_link]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get student info
    student = session['student']
    student_name = student['username']
    
    # Create email subject and body
    subject = f"Study Material: {material_name} - Smart Study Portal"
    body = f"""Hi,

I'm sharing a study material with you from Smart Study Portal:

📖 Material: {material_name}
🔗 Download Link: {material_link}

📥 Instructions:
1. Click the link above to download the material
2. Save it to your device for offline access

📚 Shared via Smart Study Portal
🏛️ Brainware University

Best regards,
{student_name}"""
    
    # Create mailto URL that opens user's email app
    import urllib.parse
    mailto_url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    
    logger.info(f"Email sharing initiated by {student['id']} ({student_name}): '{material_name}'")
    
    return jsonify({
        'success': True,
        'message': f'Opening email app to share "{material_name}"',
        'mailto_url': mailto_url,
        'action': 'open_email'
    })

@app.route('/api/send_whatsapp', methods=['POST'])
def api_send_whatsapp():
    if 'student' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    material_name = data.get('material_name')
    material_link = data.get('material_link')
    
    if not all([material_name, material_link]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get student info
    student = session['student']
    student_name = student['username']
    
    # Create WhatsApp message
    message = f"""📚 *Study Material from Smart Portal*

🎓 Hi! {student_name} has shared a study material with you:

📖 *Material:* {material_name}
🔗 *Download Link:* {material_link}

📥 *Instructions:*
1. Click the link above to download the material
2. Save it to your device for offline access

📚 Shared via Smart Study Portal
🏛️ Brainware University

Best regards,
{student_name}"""
    
    # Create WhatsApp URL that opens user's WhatsApp app
    import urllib.parse
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(message)}"
    
    logger.info(f"WhatsApp sharing initiated by {student['id']} ({student_name}): '{material_name}'")
    
    return jsonify({
        'success': True,
        'message': f'Opening WhatsApp to share "{material_name}"',
        'whatsapp_url': whatsapp_url,
        'action': 'open_whatsapp'
    })

@app.route('/logout')
def logout():
    if 'admin' in session:
        logger.info(f"Admin logged out: {session['admin']['id']}")
    elif 'student' in session:
        logger.info(f"Student logged out: {session['student']['id']}")
    
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect('/login')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
