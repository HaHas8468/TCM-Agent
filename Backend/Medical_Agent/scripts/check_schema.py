import pymysql

conn = pymysql.connect(host='localhost', user='root', password='TANXIAOYU', db='traditional_medical', port=3306)
cursor = conn.cursor()

cursor.execute("DESCRIBE api_doctor")
print("api_doctor columns:")
for row in cursor.fetchall():
    print(row)

print("\napi_doctor data:")
cursor.execute("SELECT doctor_id, username, password FROM api_doctor")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()