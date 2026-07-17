import pymysql
import os

conn = pymysql.connect(host=os.environ['MYSQL_HOST'], user=os.environ['MYSQL_USER'], password=os.environ['MYSQL_PASSWORD'], db=os.environ['MYSQL_DB'], port=int(os.getenv('MYSQL_PORT', '3306')))
cursor = conn.cursor()

cursor.execute("DESCRIBE api_doctor")
print("api_doctor columns:")
for row in cursor.fetchall():
    print(row)

print("\napi_doctor data:")
cursor.execute("SELECT doctor_id, username, password, name FROM api_doctor")
for row in cursor.fetchall():
    print(row)

cursor.execute("DESCRIBE api_patient")
print("\napi_patient columns:")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()
