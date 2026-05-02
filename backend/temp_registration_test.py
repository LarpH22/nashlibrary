import requests

url = 'http://127.0.0.1:5000/api/auth/register'
files = {'registration_document': ('test.pdf', b'PDFDATA', 'application/pdf')}
data = {'email': 'test@gmail.com', 'full_name': 'Test User', 'password': 'Test123!', 'student_id': '241-0449'}
response = requests.post(url, data=data, files=files)
print(response.status_code)
print(response.text)
