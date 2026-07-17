import pymysql

conn = pymysql.connect(host='localhost', user='root', password='TANXIAOYU', db='traditional_medical', port=3306)
cursor = conn.cursor()

try:
    cursor.execute("SHOW COLUMNS FROM api_doctor LIKE 'username'")
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE api_doctor ADD COLUMN username VARCHAR(150) NULL AFTER doctor_id')
        print('Added username to api_doctor (nullable)')
        
        cursor.execute("UPDATE api_doctor SET username = CONCAT('doctor_', doctor_id) WHERE doctor_id IS NOT NULL")
        print('Updated doctor usernames')
        
        cursor.execute('ALTER TABLE api_doctor MODIFY COLUMN username VARCHAR(150) NOT NULL UNIQUE')
        print('Made username NOT NULL UNIQUE')
    
    cursor.execute("SHOW COLUMNS FROM api_doctor LIKE 'password'")
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE api_doctor ADD COLUMN password VARCHAR(128) NOT NULL DEFAULT \'Prototype123\' AFTER username')
        print('Added password to api_doctor')
    
    cursor.execute("SHOW COLUMNS FROM api_doctor LIKE 'user_id'")
    if cursor.fetchone():
        cursor.execute('ALTER TABLE api_doctor DROP COLUMN user_id')
        print('Dropped user_id from api_doctor')
    
    cursor.execute("SHOW COLUMNS FROM api_patient LIKE 'username'")
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE api_patient ADD COLUMN username VARCHAR(150) NULL AFTER patient_id')
        print('Added username to api_patient (nullable)')
        
        cursor.execute("UPDATE api_patient SET username = CONCAT('patient_', patient_id) WHERE patient_id IS NOT NULL")
        print('Updated patient usernames')
        
        cursor.execute('ALTER TABLE api_patient MODIFY COLUMN username VARCHAR(150) NOT NULL UNIQUE')
        print('Made username NOT NULL UNIQUE')
    
    cursor.execute("SHOW COLUMNS FROM api_patient LIKE 'password'")
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE api_patient ADD COLUMN password VARCHAR(128) NOT NULL DEFAULT \'123456\' AFTER username')
        print('Added password to api_patient')
    
    cursor.execute("SHOW COLUMNS FROM api_patient LIKE 'user_id'")
    if cursor.fetchone():
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