import requests
for username, password in [('admin1@test.com','pass123'),('librarian1@test.com','pass123'),('student1@test.com','pass123')]:
    try:
        resp = requests.post('http://127.0.0.1:5000/login', json={'username': username, 'password': password})
        print(username, resp.status_code, resp.text)
    except Exception as e:
        print('exception', username, e)
