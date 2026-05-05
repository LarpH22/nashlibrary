import requests
from urllib.parse import urljoin

base = 'http://127.0.0.1:5000'
cred = {
    'email': 'nashandreimonteiro@gmail.com',
    'password': 'Farmville2',
    'role': 'librarian',
}

r = requests.post(urljoin(base, '/api/auth/login'), json=cred)
print('login', r.status_code)
print(r.text)
if r.status_code != 200:
    raise SystemExit('Login failed')
token = r.json().get('access_token') or r.json().get('token')
print('token', token[:20] if token else None)
headers = {'Authorization': f'Bearer {token}'}
r2 = requests.get(urljoin(base, '/books/ebooks'), headers=headers)
print('/books/ebooks', r2.status_code)
print(r2.text[:500])
if r2.status_code == 200:
    ebooks = r2.json().get('ebooks', [])
    print('ebook count', len(ebooks))
    if ebooks:
        ebook = ebooks[0]
        print('first ebook', ebook)
        rid = ebook['ebook_id']
        r3 = requests.get(urljoin(base, f'/books/ebooks/{rid}/download'), headers=headers, stream=True)
        print('download status', r3.status_code)
        print('content-type', r3.headers.get('content-type'))
        print('content-disposition', r3.headers.get('content-disposition'))
        r4 = requests.delete(urljoin(base, f'/books/ebooks/{rid}'), headers=headers)
        print('delete status', r4.status_code)
        print(r4.text)
