import sqlite3
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

def validate_login(student_id, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id=? AND password=?", (student_id, password))
    result = cursor.fetchone()
    conn.close()
    return result

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    student_id = request.form['student_id']
    password = request.form['password']
    if validate_login(student_id, password):
        return redirect(url_for('search'))
    else:
        return render_template('login.html', error="Invalid ID or password")

@app.route('/search')
def search():
    return render_template('search.html')
@app.route('/results', methods=['GET'])
def results():
    query = request.args.get('query')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM materials WHERE name LIKE ? OR code LIKE ?", (f"%{query}%", f"%{query}%"))
    materials = cursor.fetchall()
    conn.close()
    return render_template('results.html', materials=materials, query=query)
if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)
