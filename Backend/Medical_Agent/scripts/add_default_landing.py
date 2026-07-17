import pymysql
import os

conn = pymysql.connect(host=os.environ['MYSQL_HOST'], user=os.environ['MYSQL_USER'], password=os.environ['MYSQL_PASSWORD'], db=os.environ['MYSQL_DB'], port=int(os.getenv('MYSQL_PORT', '3306')))
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
