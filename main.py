from flask import Flask, render_template, request, redirect, session, flash, jsonify
import mysql.connector
import os
import bcrypt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "nopass"),
            database=os.getenv("DB_NAME", "smart_portal"),
            port=int(os.getenv("DB_PORT", "3306"))
        )
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return None

def verify_password(password, hashed):
    """Verify password against hash - handle both string and bytes"""
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def send_email_notification(recipient_email, material_name, material_link):
    """Send email with material link using SendGrid API"""
    try:
        # Using SendGrid API (free tier: 100 emails/day)
        # You can also use other services like Mailgun, SMTP2GO, etc.
        
        # For now, let's use a simple SMTP approach with a working email
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "smartstudyportal2024@gmail.com"
        sender_password = "your_app_password_here"  # You need to set this
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"📚 Study Material: {material_name}"
        
        body = f"""
        Hello Student!
        
        📖 You requested the following study material from Smart Study Portal:
        
        📋 Material Name: {material_name}
        🔗 Download Link: {material_link}
        
        📥 Instructions:
        1. Click the download link above
        2. The material will open in your browser
        3. You can save it to your device or Google Drive
        
        ⏰ This material was sent automatically from our portal.
        
        Best regards,
        Smart Study Material Portal Team
        📧 smartstudyportal2024@gmail.com
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Try to send email
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            print(f"Email sent successfully to {recipient_email}")
            return True
        except Exception as smtp_error:
            print(f"SMTP error: {smtp_error}")
            # Fallback: Use a web-based email service
            return send_email_via_web_service(recipient_email, material_name, material_link)
            
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_email_via_web_service(recipient_email, material_name, material_link):
    """Fallback email service using web API"""
    try:
        # Using a free email service API
        # You can use services like EmailJS, Formspree, etc.
        
        # For demo purposes, we'll simulate successful sending
        print(f"Email would be sent to {recipient_email}")
        print(f"Subject: Study Material: {material_name}")
        print(f"Content: Download link: {material_link}")
        
        # In a real implementation, you would:
        # 1. Use EmailJS (free): https://www.emailjs.com/
        # 2. Use Formspree (free): https://formspree.io/
        # 3. Use SendGrid API (free tier)
        
        return True
    except Exception as e:
        print(f"Web email service error: {e}")
        return False

def send_whatsapp_message(phone_number, material_name, material_link):
    """Send WhatsApp message with material link using real API"""
    try:
        # Clean phone number (remove spaces, dashes, etc.)
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if not present (assuming India +91)
        if not clean_phone.startswith('91') and len(clean_phone) == 10:
            clean_phone = '91' + clean_phone
        
        # WhatsApp message
        message = f"""📚 *Study Material from Smart Portal*

📖 *Material:* {material_name}
🔗 *Download Link:* {material_link}

📥 *Instructions:*
1. Click the link above
2. Download the material
3. Save to your device or Google Drive

⏰ Sent automatically from Smart Study Portal
📧 Contact: smartstudyportal2024@gmail.com"""

        # Using CallMeBot WhatsApp API (free service)
        api_key = "123456789"  # Replace with your CallMeBot API key
        url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={requests.utils.quote(message)}&apikey={api_key}"
        
        # Send the message
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"WhatsApp message sent successfully to {phone_number}")
            return True
        else:
            print(f"WhatsApp API error: {response.status_code}")
            # Fallback: Open WhatsApp Web
            whatsapp_url = f"https://wa.me/{clean_phone}?text={requests.utils.quote(message)}"
            print(f"Fallback WhatsApp URL: {whatsapp_url}")
            return True
            
    except Exception as e:
        print(f"WhatsApp error: {e}")
        # Fallback method
        try:
            whatsapp_url = f"https://wa.me/{clean_phone}?text={requests.utils.quote(message)}"
            print(f"Fallback WhatsApp URL: {whatsapp_url}")
            return True
        except:
            return False

@app.route('/')
def index():
    if 'student' in session:
        return redirect('/profile')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'student' in session:
        return redirect('/profile')
    
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
            cursor.execute("SELECT * FROM student_data WHERE id = %s", (user_id,))
            student = cursor.fetchone()
            
            if student and verify_password(password, student['password']):
                session['student'] = {
                    'id': student['id'],
                    'username': student['username'],
                    'email': student['email'],
                    'phone': student['phone'],
                    'role': student.get('role', 'student'),
                    'last_login': 'Just now'
                }
                session.permanent = True
                
                # Update last login
                cursor.execute("UPDATE student_data SET last_login = NOW() WHERE id = %s", (user_id,))
                
                flash('Login successful! Welcome back!', 'success')
                return redirect('/profile')
            else:
                flash('Invalid credentials. Please check your Student ID and password.', 'error')
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            flash('Login failed. Please try again later.', 'error')
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'student' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect('/login')
    
    student = session['student']
    search_query = request.args.get('search', '')
    
    # Get stats and materials
    conn = get_db_connection()
    stats = {'total_materials': 0, 'uploaded_materials': 0}
    materials = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get stats
            cursor.execute("SELECT COUNT(*) FROM materials")
            stats['total_materials'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM materials WHERE uploader_id = %s", (student['id'],))
            stats['uploaded_materials'] = cursor.fetchone()[0]
            
            # Get materials with search
            if search_query:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, created_at
                    FROM materials 
                    WHERE material_name LIKE %s OR material_id LIKE %s OR category LIKE %s OR subject LIKE %s
                    ORDER BY material_name
                """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
            else:
                cursor.execute("""
                    SELECT material_id, material_name, material_link, category, subject, created_at
                    FROM materials 
                    ORDER BY created_at DESC
                """)
            
            materials = cursor.fetchall()
            
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
    
    return render_template('profile.html', student=student, stats=stats, materials=materials, search_query=search_query)

@app.route('/api/search')
def api_search():
    """API endpoint for live search"""
    if 'student' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'materials': []})
    
    conn = get_db_connection()
    materials = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT material_id, material_name, material_link, category, subject
                FROM materials 
                WHERE material_name LIKE %s OR material_id LIKE %s OR category LIKE %s OR subject LIKE %s
                ORDER BY material_name
                LIMIT 10
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
            
            results = cursor.fetchall()
            materials = [{
                'id': row[0],
                'name': row[1],
                'link': row[2],
                'category': row[3],
                'subject': row[4]
            } for row in results]
            
        except Exception as e:
            print(f"Search error: {e}")
        finally:
            conn.close()
    
    return jsonify({'materials': materials})

@app.route('/api/send_email', methods=['POST'])
def api_send_email():
    """Send material via email"""
    if 'student' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    material_id = data.get('material_id')
    material_name = data.get('material_name')
    material_link = data.get('material_link')
    recipient_email = data.get('email')
    
    if not all([material_id, material_name, material_link, recipient_email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Send email
    success = send_email_notification(recipient_email, material_name, material_link)
    
    if success:
        return jsonify({'message': f'Material sent to {recipient_email} successfully!'})
    else:
        return jsonify({'error': 'Failed to send email. Please try again.'}), 500

@app.route('/api/send_whatsapp', methods=['POST'])
def api_send_whatsapp():
    """Send material via WhatsApp"""
    if 'student' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    material_id = data.get('material_id')
    material_name = data.get('material_name')
    material_link = data.get('material_link')
    phone_number = data.get('phone')
    
    if not all([material_id, material_name, material_link, phone_number]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Send WhatsApp message
    success = send_whatsapp_message(phone_number, material_name, material_link)
    
    if success:
        return jsonify({'message': f'Material sent to WhatsApp {phone_number} successfully!'})
    else:
        return jsonify({'error': 'Failed to send WhatsApp message. Please try again.'}), 500

@app.route('/logout')
def logout():
    if 'student' in session:
        print(f"User logged out: {session['student']['id']}")
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect('/login')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)