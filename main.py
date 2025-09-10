from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME']
    )

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM student_data WHERE username=%s AND password=%s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    conn.close()
    if result:
        return redirect('/search')
    else:
        return "Login failed"

@app.route('/search')
def search():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM student_data")
    students = cursor.fetchall()

    profile_id = request.args.get('profile_id')
    profile = None
    if profile_id:
        cursor.execute("SELECT id, username, email, phone FROM student_data WHERE id = %s", (profile_id,))
        profile = cursor.fetchone()

    conn.close()
    return render_template('search.html', students=students, profile=profile)

@app.route('/profile/<int:id>')
def view_profile(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT id, username, email, phone FROM student_data WHERE id = %s"
    cursor.execute(query, (id,))
    student = cursor.fetchone()
    conn.close()
    if student:
        return render_template('profile.html', student=student)
    else:
        return "Student not found"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
