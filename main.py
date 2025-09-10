import sqlite3
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

import mysql.connector

def validate_login(student_id, password):
    import os

conn = mysql.connector.connect(
    host=os.environ['DB_HOST'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME']
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
