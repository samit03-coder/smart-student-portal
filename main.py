import sqlite3
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

import mysql.connector

def validate_login(student_id, password):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_mysql_password",  # Replace with your actual MySQL password
        database="smart_portal"
    )
    cursor = conn.cursor()
    query = "SELECT * FROM students WHERE student_id=%s AND password=%s"
    cursor.execute(query, (student_id, password))
    result = cursor.fetchone()
    conn.close()
    return result
@app.route('/search')
def search():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('search.html', users=users)
@app.route('/profile/<int:user_id>')
def profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('profile.html', user=user)
