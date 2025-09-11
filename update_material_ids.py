import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASS', 'nopass'),
    database=os.getenv('DB_NAME', 'smart_portal'),
    port=int(os.getenv('DB_PORT', '3306'))
)

cursor = conn.cursor()

# Update material IDs to BWU/MATERIAL/001 format
cursor.execute('UPDATE materials SET material_id = CONCAT("BWU/MATERIAL/", LPAD(material_id - 5, 3, "0")) WHERE material_id >= 6')

conn.commit()
conn.close()
print('✅ Material IDs updated to BWU/MATERIAL/001 format!')
