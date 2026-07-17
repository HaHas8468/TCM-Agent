import pymysql

conn = pymysql.connect(host='localhost', user='root', password='TANXIAOYU', db='traditional_medical', port=3306)
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
    
    cursor.execute("UPDATE api_doctor SET username='doctor.lin', password='Prototype123' WHERE doctor_id='D001'")
    cursor.execute("UPDATE api_doctor SET username='doctor.zhou', password='Prototype123' WHERE doctor_id='D002'")
    cursor.execute("UPDATE api_doctor SET username='doctor.zhang', password='Prototype123' WHERE doctor_id='D003'")
    cursor.execute("UPDATE api_doctor SET username='doctor.chen', password='Prototype123' WHERE doctor_id='D004'")
    print('Updated doctor data')
    
    conn.commit()
    print('Schema updated successfully!')
except Exception as e:
    conn.rollback()
    print(f'Error: {e}')
finally:
    cursor.close()
    conn.close()