from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, abort
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, EmailField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, ValidationError
import mysql.connector
import os
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['WTF_CSRF_ENABLED'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
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
        logger.error(f"Database connection error: {e}")
        return None

# Security utilities
def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def send_study_material_email(recipient_email, material_name, material_link, student_name="Student"):
    """Send study material via email from admin"""
    try:
        # Admin email configuration
        admin_email = "bwubta24398@brainwareuniversity.ac.in"
        admin_password = os.getenv('ADMIN_EMAIL_PASSWORD', 'your_app_password_here')  # You need to set this in .env
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = admin_email
        msg['To'] = recipient_email
        msg['Subject'] = f"📚 Study Material: {material_name} - Smart Study Portal"
        
        # Email body
        body = f"""
        Dear {student_name},
        
        📖 You have requested the following study material from Smart Study Portal:
        
        📋 Material Name: {material_name}
        🔗 Access Link: {material_link}
        
        📥 Instructions:
        1. Click the link above to access the material
        2. You can download or view the material online
        3. Save it to your device for offline access
        
        📚 This material has been shared from our Smart Study Portal by the administration.
        
        For any queries, feel free to contact us.
        
        Best regards,
        Smart Study Portal Administration
        Brainware University
        📧 {admin_email}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(admin_email, admin_password)
        
        text = msg.as_string()
        server.sendmail(admin_email, recipient_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully from {admin_email} to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Admin access required. Please log in as administrator.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Decorator to require student login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

# Forms
class AdminLoginForm(FlaskForm):
    admin_id = StringField('Admin ID', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])

class StudentLoginForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])

class AddStudentForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=3, max=20)])
    username = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class UploadMaterialForm(FlaskForm):
    material_name = StringField('Material Name', validators=[DataRequired(), Length(max=255)])
    material_link = StringField('Material Link/URL', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired(), Length(max=100)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    tags = StringField('Tags (comma-separated)')

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if 'admin' in session:
        return redirect(url_for('dashboard'))
    elif 'student' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Clear any existing session
        session.clear()
        
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
            
            if admin:
                # Admin found, check password
                if verify_password(password, admin['password'].encode('utf-8')):
                    session['admin'] = {
                        'id': admin['admin_id'],
                        'name': admin['admin_name'],
                        'email': admin['email'],
                        'is_super_admin': admin['is_super_admin']
                    }
                    session.permanent = True
                    cursor.execute("UPDATE administrators SET last_login = NOW() WHERE admin_id = %s", (user_id,))
                    logger.info(f"Admin login successful: {user_id}")
                    flash('Welcome Administrator!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid admin password. Please try again.', 'error')
            else:
                # No admin found, check student
                cursor.execute("SELECT * FROM student_data WHERE id = %s AND is_active = TRUE", (user_id,))
                student = cursor.fetchone()
                
                if student:
                    # Student found, check password
                    logger.info(f"Student found: {student['id']}, checking password")
                    if verify_password(password, student['password'].encode('utf-8')):
                        session['student'] = {
                            'id': student['id'],
                            'username': student['username'],
                            'email': student['email'],
                            'phone': student['phone']
                        }
                        session.permanent = True
                        cursor.execute("UPDATE student_data SET last_login = NOW() WHERE id = %s", (user_id,))
                        logger.info(f"Student login successful: {user_id}")
                        flash('Welcome back!', 'success')
                        return redirect(url_for('dashboard'))
                    else:
                        logger.error(f"Password verification failed for student: {user_id}")
                        flash('Invalid student password. Please try again.', 'error')
                else:
                    flash('User ID not found. Please check your credentials.', 'error')
        except mysql.connector.Error as e:
            logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    logger.info(f"Dashboard accessed. Session contains: {list(session.keys())}")
    if 'admin' in session:
        logger.info(f"Loading admin dashboard for: {session['admin']['id']}")
        return admin_dashboard_view()
    elif 'student' in session:
        logger.info(f"Loading student dashboard for: {session['student']['id']}")
        return student_dashboard_view()
    else:
        logger.info("No session found, redirecting to login")
        return redirect(url_for('login'))

def admin_dashboard_view():
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
            
            # Get materials with search
            if search:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    WHERE material_name LIKE %s OR category LIKE %s OR subject LIKE %s OR description LIKE %s
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
            materials = cursor.fetchall()
            
        except mysql.connector.Error as e:
            logger.error(f"Dashboard error: {e}")
        finally:
            conn.close()
    
    return render_template('admin_dashboard.html', admin=admin, materials=materials, search=search, stats=stats)

def student_dashboard_view():
    student = session['student']
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    materials = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get materials with search
            if search:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    WHERE is_public = TRUE AND (material_name LIKE %s OR category LIKE %s OR subject LIKE %s OR description LIKE %s)
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
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
    
    return render_template('student_dashboard.html', student=student, materials=materials, search=search)

@app.route('/admin_profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    admin = session['admin']
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT password FROM administrators WHERE admin_id = %s", (admin['id'],))
                admin_data = cursor.fetchone()
                
                if admin_data and verify_password(password, admin_data['password'].encode('utf-8')):
                    return render_template('admin_profile.html', admin=admin, verified=True)
                else:
                    flash('Incorrect password.', 'error')
            except mysql.connector.Error as e:
                logger.error(f"Admin profile error: {e}")
            finally:
                conn.close()
    
    return render_template('admin_profile.html', admin=admin, verified=False)

@app.route('/admin/students')
@admin_required  
def admin_students():
    admin = session['admin']
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    students = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if search:
                cursor.execute("""
                    SELECT id, username, email, phone, is_active, last_login, created_at 
                    FROM student_data 
                    WHERE username LIKE %s OR id LIKE %s OR email LIKE %s
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT id, username, email, phone, is_active, last_login, created_at 
                    FROM student_data 
                    ORDER BY created_at DESC
                """)
            students = cursor.fetchall()
        except mysql.connector.Error as e:
            logger.error(f"Students fetch error: {e}")
        finally:
            conn.close()
    
    return render_template('admin_students.html', admin=admin, students=students, search=search)

@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    admin = session['admin']
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone') 
        password = request.form.get('password')
        
        if not all([student_id, username, email, phone, password]):
            flash('All fields are required.', 'error')
            return render_template('admin_add_student.html', admin=admin)
            
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if student ID already exists
                cursor.execute("SELECT id FROM student_data WHERE id = %s", (student_id,))
                if cursor.fetchone():
                    flash('Student ID already exists.', 'error')
                    return render_template('admin_add_student.html', admin=admin)
                
                hashed_password = hash_password(password)
                cursor.execute("""
                    INSERT INTO student_data (id, username, email, phone, password, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, TRUE, NOW())
                """, (student_id, username, email, phone, hashed_password.decode('utf-8')))
                
                logger.info(f"Student added by admin {admin['id']}: {student_id}")
                flash(f'Student {student_id} added successfully!', 'success')
                return redirect(url_for('admin_students'))
                
            except mysql.connector.Error as e:
                logger.error(f"Add student error: {e}")
                flash('Failed to add student. Please try again.', 'error')
            finally:
                conn.close()
    
    return render_template('admin_add_student.html', admin=admin)

@app.route('/admin/materials')
@admin_required
def admin_materials():
    admin = session['admin']
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    materials = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if search:
                cursor.execute("""
                    SELECT material_id, material_name, category, subject, uploader_id, created_at, download_count
                    FROM materials 
                    WHERE material_name LIKE %s OR category LIKE %s OR subject LIKE %s
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("""
                    SELECT material_id, material_name, category, subject, uploader_id, created_at, download_count
                    FROM materials 
                    ORDER BY created_at DESC
                """)
            materials = cursor.fetchall()
        except mysql.connector.Error as e:
            logger.error(f"Materials fetch error: {e}")
        finally:
            conn.close()
    
    return render_template('admin_materials.html', admin=admin, materials=materials, search=search)

@app.route('/admin/materials/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload_material():
    admin = session['admin']
    
    if request.method == 'POST':
        material_name = request.form.get('material_name')
        material_link = request.form.get('material_link')
        category = request.form.get('category')
        subject = request.form.get('subject')
        description = request.form.get('description')
        tags = request.form.get('tags')
        
        if not all([material_name, material_link, category, subject]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin_upload_material.html', admin=admin)
            
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO materials (material_name, material_link, category, subject, 
                                         description, tags, uploader_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """, (material_name, material_link, category, subject, description, tags, admin['id']))
                
                logger.info(f"Material uploaded by admin {admin['id']}: {material_name}")
                flash('Study material uploaded successfully!', 'success')
                return redirect(url_for('admin_materials'))
                
            except mysql.connector.Error as e:
                logger.error(f"Upload material error: {e}")
                flash('Failed to upload material. Please try again.', 'error')
            finally:
                conn.close()
    
    return render_template('admin_upload_material.html', admin=admin)

@app.route('/logout')
def logout():
    if 'admin' in session:
        logger.info(f"Admin logged out: {session['admin']['id']}")
        session.pop('admin', None)
    elif 'student' in session:
        logger.info(f"Student logged out: {session['student']['id']}")
        session.pop('student', None)
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# Student Routes
@app.route('/profile')
def profile():
    if 'student' in session:
        student = session['student']
        return render_template('student_profile.html', student=student)
    elif 'admin' in session:
        return redirect(url_for('admin_profile'))
    else:
        return redirect(url_for('login'))

@app.route('/student/dashboard')
@student_required
def student_dashboard():
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
            
            # Get materials with search
            if search:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, description, created_at
                    FROM materials 
                    WHERE is_public = TRUE AND (material_name LIKE %s OR category LIKE %s OR subject LIKE %s OR description LIKE %s)
                    ORDER BY created_at DESC
                """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
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
    
    return render_template('student/dashboard.html', student=student, materials=materials, 
                         search=search, stats=stats)

@app.route('/student/profile')
@student_required
def student_profile():
    student = session['student']
    return render_template('student/profile.html', student=student)

@app.route('/api/send_email', methods=['POST'])
@student_required
def send_email():
    data = request.get_json()
    material_name = data.get('material_name')
    material_link = data.get('material_link')
    recipient_email = data.get('email')
    
    if not all([material_name, material_link, recipient_email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Email validation
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient_email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Get student info
    student = session['student']
    student_name = student['username']
    
    # Send actual email
    logger.info(f"Sending email from {student['id']} ({student_name}): '{material_name}' to {recipient_email}")
    
    if send_study_material_email(recipient_email, material_name, material_link, student_name):
        return jsonify({'message': f'Material "{material_name}" sent to {recipient_email} successfully from Brainware University!'})
    else:
        return jsonify({'error': 'Failed to send email. Please check your internet connection and try again.'}), 500

@app.route('/api/send_whatsapp', methods=['POST'])
@student_required
def send_whatsapp():
    data = request.get_json()
    material_name = data.get('material_name')
    material_link = data.get('material_link')
    phone_number = data.get('phone')
    
    if not all([material_name, material_link, phone_number]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Clean phone number
    clean_phone = re.sub(r'[^0-9]', '', phone_number)
    
    # Add country code if not present (assuming India +91)
    if len(clean_phone) == 10 and not clean_phone.startswith('91'):
        clean_phone = '91' + clean_phone
    
    # Validate phone number
    if len(clean_phone) < 10 or len(clean_phone) > 15:
        return jsonify({'error': 'Invalid phone number format'}), 400
    
    # Get student info
    student = session['student']
    student_name = student['username']
    
    # Create WhatsApp message
    message = f"""📚 *Study Material from Smart Portal*

🎓 Hi! {student_name} has shared a study material with you:

📖 *Material:* {material_name}
🔗 *Access Link:* {material_link}

📥 *Instructions:*
1. Click the link above to access the material
2. Download or view online
3. Save for offline access

📚 Shared via Smart Study Portal
🏛️ Brainware University
📧 bwubta24398@brainwareuniversity.ac.in"""
    
    # Create WhatsApp Web URL
    whatsapp_url = f"https://wa.me/{clean_phone}?text={requests.utils.quote(message)}"
    
    logger.info(f"WhatsApp request from {student['id']}: '{material_name}' to {phone_number}")
    
    return jsonify({
        'success': True,
        'message': f'WhatsApp ready for {phone_number}',
        'whatsapp_url': whatsapp_url,
        'action': 'open_whatsapp'
    })

@app.route('/student/logout')
def student_logout():
    if 'student' in session:
        logger.info(f"Student logged out: {session['student']['id']}")
        session.pop('student', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# Template functions
@app.template_global()
def is_admin():
    return 'admin' in session

@app.template_global()
def is_student():
    return 'student' in session

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
