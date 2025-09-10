import mysql.connector
import bcrypt
import os

# Quick database setup
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASS', 'nopass'),
    database=os.getenv('DB_NAME', 'smart_portal'),
    port=int(os.getenv('DB_PORT', '3306'))
)

cursor = conn.cursor()

# Clear and insert students
cursor.execute('DELETE FROM materials')
cursor.execute('DELETE FROM student_data WHERE id != "admin"')

# Insert students with hashed passwords
students = [
    ('BWU/001','Samit','pass@Samit','samitbinku@gmail.com',8910816531),
    ('BWU/002','soumi','pass@soumi','soumidhara279@gmail.com',9330870623),
    ('BWU/003','sriparna','pass@sriparna','sriparnachatterjee45@gmail.com',6295762865),
    ('BWU/004','rajanya','pass@rajanya','rajanya_sadhu_23@gmail.com',7908553061),
    ('BWU/005','asif','pass@asif','Asif_6754@gmail.com',9735440963),
    ('BWU/006','rohit','pass@rohit','rohit_45@gmail.com',9087654326),
    ('BWU/007','bumba','pass@bumba','BuMbA.SiNgHa.8888@gmail.com',6543289075),
    ('BWU/008','sandip','pass@sandip','sandip.xor.89@gmail.com',9876598764),
    ('BWU/009','sougata','pass@sougata','sougata_2004@gmail.com',9786543865),
    ('BWU/010','aritri','pass@aritri','aritri.saha.8975@gmail.com',8967543276),
    ('BWU/011','kankana','pass@kankana','kan_kana_77@gmail.com',9907865345),
    ('BWU/012','soumyadeep','pass@soumyadeep','soumya_2005@gmail.com',7865987654),
    ('BWU/013','joyta','pass@joyta','joyta.jana_67@gmail.com',6543789065),
    ('BWU/014','ankana','pass@ankana','Ankana_das.2005@gmail.com',7789065476),
    ('BWU/015','gopi','pass@gopi','Gpoinath_mithy.890@gmail.com',9954372786)
]

for student in students:
    hashed_password = bcrypt.hashpw(student[2].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('INSERT INTO student_data (id, username, password, email, phone, role, email_verified) VALUES (%s, %s, %s, %s, %s, %s, %s)', (student[0], student[1], hashed_password, student[3], student[4], 'student', True))

# Insert materials
materials = [
    ('Introduction to Python Programming', 'https://drive.google.com/file/d/1abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567/view', 'pdf', 'Programming', 'Python Basics', 'Complete guide to Python programming fundamentals for beginners', 'BWU/001'),
    ('Database Design Principles', 'https://drive.google.com/file/d/2def456ghi789jkl012mno345pqr678stu901vwx234yz567abc123/view', 'pdf', 'Database', 'SQL Fundamentals', 'Learn database design and SQL queries from scratch', 'BWU/002'),
    ('Web Development with Flask', 'https://drive.google.com/file/d/3ghi789jkl012mno345pqr678stu901vwx234yz567abc123def456/view', 'pdf', 'Web Development', 'Flask Framework', 'Building web applications with Python Flask framework', 'BWU/003'),
    ('Mathematics for Computer Science', 'https://drive.google.com/file/d/4jkl012mno345pqr678stu901vwx234yz567abc123def456ghi789/view', 'pdf', 'Mathematics', 'Discrete Math', 'Mathematical foundations for computer science students', 'BWU/004'),
    ('Data Structures and Algorithms', 'https://drive.google.com/file/d/5mno345pqr678stu901vwx234yz567abc123def456ghi789jkl012/view', 'pdf', 'Computer Science', 'Algorithms', 'Essential algorithms and data structures for programming', 'BWU/005'),
    ('Machine Learning Basics', 'https://drive.google.com/file/d/6pqr678stu901vwx234yz567abc123def456ghi789jkl012mno345/view', 'pdf', 'AI/ML', 'Machine Learning', 'Introduction to machine learning concepts and applications', 'BWU/006'),
    ('Software Engineering Principles', 'https://drive.google.com/file/d/7stu901vwx234yz567abc123def456ghi789jkl012mno345pqr678/view', 'pdf', 'Software Engineering', 'Development', 'Best practices and principles in software development', 'BWU/007'),
    ('Computer Networks Fundamentals', 'https://drive.google.com/file/d/8vwx234yz567abc123def456ghi789jkl012mno345pqr678stu901/view', 'pdf', 'Networking', 'Network Security', 'Understanding computer networks and network protocols', 'BWU/008'),
    ('Operating Systems Concepts', 'https://drive.google.com/file/d/9yz567abc123def456ghi789jkl012mno345pqr678stu901vwx234/view', 'pdf', 'Operating Systems', 'System Programming', 'Core concepts of operating systems and system programming', 'BWU/009'),
    ('Cybersecurity Essentials', 'https://drive.google.com/file/d/0abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567/view', 'pdf', 'Security', 'Cybersecurity', 'Essential cybersecurity concepts and best practices', 'BWU/010'),
    ('Cloud Computing Basics', 'https://drive.google.com/file/d/1bcd234efg567hij890klm123nop456qrs789tuv012wxy345zab678/view', 'pdf', 'Cloud Computing', 'AWS/Azure', 'Introduction to cloud computing platforms and services', 'BWU/011'),
    ('Mobile App Development', 'https://drive.google.com/file/d/2cde345fgh678ijk901lmn234opq567rst890uvw123xyz456abc789/view', 'pdf', 'Mobile Development', 'React Native', 'Building mobile applications using React Native', 'BWU/012'),
    ('DevOps Fundamentals', 'https://drive.google.com/file/d/3def456ghi789jkl012mno345pqr678stu901vwx234yz567abc123def456/view', 'pdf', 'DevOps', 'CI/CD', 'DevOps practices and continuous integration/deployment', 'BWU/013'),
    ('Blockchain Technology', 'https://drive.google.com/file/d/4efg567hij890klm123nop456qrs789tuv012wxy345zab678cde901/view', 'pdf', 'Blockchain', 'Cryptocurrency', 'Understanding blockchain technology and cryptocurrencies', 'BWU/014'),
    ('Artificial Intelligence', 'https://drive.google.com/file/d/5fgh678ijk901lmn234opq567rst890uvw123xyz456abc789def012/view', 'pdf', 'AI', 'Deep Learning', 'Introduction to artificial intelligence and deep learning', 'BWU/015')
]

for material in materials:
    cursor.execute('INSERT INTO materials (material_name, material_link, file_type, category, subject, description, uploader_id, is_public) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (material[0], material[1], material[2], material[3], material[4], material[5], material[6], True))

conn.commit()
conn.close()
print('✅ DONE! Students and materials inserted!')
print('📧 Test: samitbinku@gmail.com, soumidhara279@gmail.com')
print('📱 Test: 8910816531, 9330870623')
