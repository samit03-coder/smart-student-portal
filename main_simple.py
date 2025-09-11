from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
import mysql.connector
import os
import bcrypt
import secrets
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['WTF_CSRF_ENABLED'] = True

# Initialize CSRF protection
csrf = CSRFProtect(app)

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
        print(f"Database connection error: {e}")
        return None

# Security utilities
def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Forms
class LoginForm(FlaskForm):
    user_id = StringField('Student ID', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])

# Routes
@app.route('/')
def index():
    if 'student' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'student' in session:
        return redirect(url_for('profile'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data.strip()
        password = form.password.data
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed. Please try again later.', 'error')
            return render_template('login_simple.html', form=form)
        
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
                    'last_login': student.get('last_login').strftime('%Y-%m-%dT%H:%M:%S') if student.get('last_login') else None
                }
                session.permanent = True
                
                # Update last login
                cursor.execute("UPDATE student_data SET last_login = NOW() WHERE id = %s", (user_id,))
                
                flash('Login successful!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
        except mysql.connector.Error as e:
            print(f"Database error during login: {e}")
            flash('Login failed. Please try again later.', 'error')
        finally:
            conn.close()
    
    return render_template('login_simple.html', form=form)

@app.route('/logout')
def logout():
    if 'student' in session:
        print(f"User logged out: {session['student']['id']}")
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    student = session['student']
    return render_template('profile_simple.html', student=student)

@app.route('/dashboard')
@login_required
def dashboard():
    # Simple redirect to profile for now
    return redirect(url_for('profile'))

@app.route('/search')
@login_required
def search():
    # Simple redirect to profile for now
    return redirect(url_for('profile'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
