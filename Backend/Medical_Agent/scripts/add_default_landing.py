import pymysql

conn = pymysql.connect(host='localhost', user='root', password='TANXIAOYU', db='traditional_medical', port=3306)
cursor = conn.cursor()

try:
    cursor.execute("SHOW COLUMNS FROM api_doctor LIKE 'default_landing'")
    if not cursor.fetchone():
        cursor.execute('ALTER TABLE api_doctor ADD COLUMN default_landing VARCHAR(50) NOT NULL DEFAULT \'queue\' AFTER description')
        print('Added default_landing to api_doctor')
    
    conn.commit()
    print('Done')
except Exception as e:
    conn.rollback()
    print(f'Error: {e}')
finally:
    cursor.close()
    conn.close()