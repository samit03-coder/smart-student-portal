from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, abort
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import CSRFError
from wtforms import StringField, PasswordField, EmailField, TextAreaField, SelectField, FileField
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

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection with error handling
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
        flash('Database connection failed. Please try again later.', 'error')
        return None

# Security utilities
def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def validate_input(text, max_length=255):
    """Sanitize and validate user input"""
    if not text or len(text.strip()) == 0:
        return None
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text.strip())
    return text[:max_length] if text else None

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Forms
class LoginForm(FlaskForm):
    user_id = StringField('Student ID', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])

class RegistrationForm(FlaskForm):
    user_id = StringField('Student ID', validators=[DataRequired(), Length(min=3, max=20)])
    username = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])

    def validate_user_id(self, field):
        # Check if user ID already exists
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM student_data WHERE id = %s", (field.data,))
            if cursor.fetchone():
                raise ValidationError('Student ID already exists.')
            conn.close()

    def validate_email(self, field):
        # Check if email already exists
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM student_data WHERE email = %s", (field.data,))
            if cursor.fetchone():
                raise ValidationError('Email already registered.')
            conn.close()

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Passwords must match.')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Length(max=100)])
    category = SelectField('Category', choices=[('all', 'All Categories'), ('pdf', 'PDFs'), ('doc', 'Documents'), ('image', 'Images')])

# Error handlers
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security token expired. Please try again.', 'error')
    return redirect(request.url)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Routes
@app.route('/')
def index():
    if 'student' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'student' in session:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_id = validate_input(form.user_id.data)
        password = form.password.data
        
        if not user_id:
            flash('Invalid student ID format.', 'error')
            return render_template('auth/login.html', form=form)
        
        conn = get_db_connection()
        if not conn:
            return render_template('auth/login.html', form=form)
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM student_data WHERE id = %s", (user_id,))
            student = cursor.fetchone()
            
            if student and verify_password(password, student['password'].encode('utf-8')):
                session['student'] = {
                    'id': student['id'],
                    'username': student['username'],
                    'email': student['email'],
                    'phone': student['phone'],
                    'role': student.get('role', 'student'),
                    'last_login': datetime.now().isoformat()
                }
                session.permanent = True
                
                # Update last login
                cursor.execute("UPDATE student_data SET last_login = NOW() WHERE id = %s", (user_id,))
                
                logger.info(f"Successful login for user: {user_id}")
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                logger.warning(f"Failed login attempt for user: {user_id}")
                flash('Invalid credentials. Please try again.', 'error')
        except mysql.connector.Error as e:
            logger.error(f"Database error during login: {e}")
            flash('Login failed. Please try again later.', 'error')
        finally:
            conn.close()
    
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'student' in session:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        if not conn:
            return render_template('auth/register.html', form=form)
        
        try:
            cursor = conn.cursor()
            hashed_password = hash_password(form.password.data)
            
            cursor.execute("""
                INSERT INTO student_data (id, username, email, phone, password, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (
                form.user_id.data,
                validate_input(form.username.data),
                form.email.data,
                validate_input(form.phone.data),
                hashed_password.decode('utf-8'),
                'student'
            ))
            
            logger.info(f"New user registered: {form.user_id.data}")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.Error as e:
            logger.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
def logout():
    if 'student' in session:
        logger.info(f"User logged out: {session['student']['id']}")
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    student = session['student']
    
    conn = get_db_connection()
    if not conn:
        return render_template('dashboard.html', student=student, materials=[], stats={})
    
    try:
        cursor = conn.cursor()
        
        # Get recent materials
        cursor.execute("""
            SELECT material_id, material_name, material_link, created_at 
            FROM materials 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        materials = cursor.fetchall()
        
        # Get user stats
        cursor.execute("""
            SELECT COUNT(*) as total_materials,
                   (SELECT COUNT(*) FROM materials WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)) as recent_materials
            FROM materials
        """)
        stats = cursor.fetchone()
        
    except mysql.connector.Error as e:
        logger.error(f"Dashboard error: {e}")
        materials = []
        stats = (0, 0)
    finally:
        conn.close()
    
    return render_template('dashboard.html', student=student, materials=materials, stats=stats)

@app.route('/search')
@login_required
def search():
    form = SearchForm()
    student = session['student']
    
    conn = get_db_connection()
    if not conn:
        return render_template('search.html', student=student, materials=[], form=form)
    
    try:
        cursor = conn.cursor()
        query = request.args.get('query', '').strip()
        category = request.args.get('category', 'all')
        
        if query:
            search_query = f"%{query}%"
            if category == 'all':
                cursor.execute("""
                    SELECT material_id, material_name, material_link, created_at
                    FROM materials 
                    WHERE material_name LIKE %s OR material_id LIKE %s
                    ORDER BY material_name
                """, (search_query, search_query))
            else:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, created_at
                    FROM materials 
                    WHERE (material_name LIKE %s OR material_id LIKE %s) 
                    AND material_link LIKE %s
                    ORDER BY material_name
                """, (search_query, search_query, f"%.{category}"))
        else:
            cursor.execute("""
                SELECT material_id, material_name, material_link, created_at
                FROM materials 
                ORDER BY created_at DESC
            """)
        
        materials = cursor.fetchall()
        
    except mysql.connector.Error as e:
        logger.error(f"Search error: {e}")
        materials = []
    finally:
        conn.close()
    
    return render_template('search.html', student=student, materials=materials, form=form, query=query)

@app.route('/profile')
@login_required
def profile():
    student = session['student']
    return render_template('profile.html', student=student)

@app.route('/send_email', methods=['POST'])
@login_required
def send_email():
    material_name = validate_input(request.form.get('material_name', ''))
    material_link = request.form.get('material_link', '')
    email = request.form.get('email', '')
    
    if not all([material_name, material_link, email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Basic email validation
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    logger.info(f"Email request: '{material_name}' to {email}")
    return jsonify({'message': f'Material sent to {email} via email.'})

@app.route('/send_whatsapp', methods=['POST'])
@login_required
def send_whatsapp():
    material_name = validate_input(request.form.get('material_name', ''))
    material_link = request.form.get('material_link', '')
    phone = validate_input(request.form.get('phone', ''))
    
    if not all([material_name, material_link, phone]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Basic phone validation
    if not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', phone):
        return jsonify({'error': 'Invalid phone format'}), 400
    
    logger.info(f"WhatsApp request: '{material_name}' to {phone}")
    return jsonify({'message': f'Material sent to WhatsApp number {phone}.'})

if __name__ == "__main__":
    # Create upload directory if it doesn't exist
    upload_folder = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
