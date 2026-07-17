import pymysql
import os

conn = pymysql.connect(host=os.environ['MYSQL_HOST'], user=os.environ['MYSQL_USER'], password=os.environ['MYSQL_PASSWORD'], db=os.environ['MYSQL_DB'], port=int(os.getenv('MYSQL_PORT', '3306')))
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE api_doctor ADD COLUMN username VARCHAR(150) NOT NULL UNIQUE AFTER doctor_id')
    print('Added username to api_doctor')
    
    cursor.execute('ALTER TABLE api_doctor ADD COLUMN password VARCHAR(128) NOT NULL AFTER username')
    print('Added password to api_doctor')
    
    cursor.execute('ALTER TABLE api_doctor ADD INDEX idx_doctor_username (username)')
    print('Added index to api_doctor')
    
    cursor.execute('ALTER TABLE api_patient ADD COLUMN username VARCHAR(150) NOT NULL UNIQUE AFTER patient_id')
    print('Added username to api_patient')
    
    cursor.execute('ALTER TABLE api_patient ADD COLUMN password VARCHAR(128) NOT NULL AFTER username')
    print('Added password to api_patient')
    
    cursor.execute('ALTER TABLE api_patient ADD INDEX idx_patient_username (username)')
    print('Added index to api_patient')
    
    cursor.execute('ALTER TABLE api_doctor DROP COLUMN user_id')
    print('Dropped user_id from api_doctor')
    
    cursor.execute('ALTER TABLE api_patient DROP COLUMN user_id')
    print('Dropped user_id from api_patient')
    
    print('Updated doctor data')
    
    conn.commit()
    print('Schema updated successfully!')
except Exception as e:
    conn.rollback()
    print(f'Error: {e}')
finally:
    cursor.close()
    conn.close()
