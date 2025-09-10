from flask import Flask, render_template, request, redirect, session
import os
import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )    

# 🔹 Route: Login Page
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    user_id = request.form['id']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_data WHERE id = %s AND password = %s", (user_id, password))
    student = cursor.fetchone()
    conn.close()

    print("Login attempt:", student)  # Add this line

    if student:
        session['student'] = {
            'id': student[0],
            'username': student[1],
            'email': student[3],
            'phone': student[4]
        }
        return redirect('/search')
    else:
        session.clear()  # Clear any existing session
        return "Invalid credentials"


@app.route('/search')
def search():
    if 'student' not in session:
        return redirect('/')

    student = session['student']  # This should be a dictionary with correct keys

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT material_id, material_name, material_link FROM materials")
    raw_materials = cursor.fetchall()
    conn.close()

    materials = [(m[0], m[1], m[2]) for m in raw_materials]
    return render_template("search.html", student=student, materials=materials)

@app.route('/results')
def results():
    query = request.args.get('query')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT material_id, material_name, material_link 
        FROM materials 
        WHERE material_id = %s OR material_name LIKE %s
    """, (query, f"%{query}%"))
    raw_materials = cursor.fetchall()
    conn.close()

    # Optional: transform link if needed
    def transform_drive_link(link):
        if "drive.google.com/file/d/" in link:
            file_id = link.split("/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        return link

    materials = [(m[0], m[1], transform_drive_link(m[2])) for m in raw_materials]
    return render_template("results.html", query=query, materials=materials)

@app.route('/send_email', methods=['POST'])
def send_email():
    material_name = request.form['material_name']
    material_link = request.form['material_link']
    email = request.form['email']
    print(f"Sending '{material_name}' to {email} via email. Link: {material_link}")
    return f"✅ Material sent to {email} via email."

@app.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
    material_name = request.form['material_name']
    material_link = request.form['material_link']
    phone = request.form['phone']
    print(f"Sending '{material_name}' to WhatsApp number {phone}. Link: {material_link}")
    return f"✅ Material sent to WhatsApp number {phone}."

# 🔹 Run the App
if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
