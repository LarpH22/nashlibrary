import requests
try:
    r = requests.post('http://127.0.0.1:5000/login', json={'username':'admin','password':'admin123'})
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')
except Exception as e:
    print(f'Error: {e}')