import requests

print("=== 测试医生登录 ===")
r = requests.post('http://localhost:8000/api/doctor/auth/login', json={
    'username': 'doctor.lin',
    'password': 'Prototype123'
})
print(f"医生登录响应: {r.status_code}")
print(r.text)
print()

print("=== 测试患者注册 ===")
r = requests.post('http://localhost:8000/api/auth/register', json={
    'username': 'test_patient',
    'password': '123456',
    'confirm_password': '123456',
    'name': '测试患者',
    'phone': '13800138000'
})
print(f"患者注册响应: {r.status_code}")
print(r.text)
print()

print("=== 测试患者登录 ===")
r = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'test_patient',
    'password': '123456'
})
print(f"患者登录响应: {r.status_code}")
print(r.text)