import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create students table
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
''')

# Create materials table
cursor.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    code TEXT,
    file_path TEXT
)
''')

# Insert sample student
cursor.execute("INSERT OR IGNORE INTO students (student_id, password) VALUES (?, ?)", ("12345", "pass123"))

# Insert sample materials
cursor.execute("INSERT INTO materials (name, code, file_path) VALUES (?, ?, ?)", 
               ("Physics Notes", "PHY101", "https://drive.google.com/file/d/xyz"))
cursor.execute("INSERT INTO materials (name, code, file_path) VALUES (?, ?, ?)", 
               ("Math Guide", "MTH202", "https://drive.google.com/file/d/abc"))

conn.commit()
conn.close()
