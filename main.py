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

@app.route('/login', methods=['POST'])
def login():
    student_id = request.form['student_id']
    password = request.form['password']
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM students WHERE student_id=%s AND password=%s"
    cursor.execute(query, (student_id, password))
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
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('search.html', users=users)

@app.route('/profile/<int:id>')
def profile(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT id, name, email, phone FROM users WHERE id = %s"
    cursor.execute(query, (id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return render_template('profile.html', user=user)
    else:
        return "User not found"

if __name__ == '__main__':
    app.run()
