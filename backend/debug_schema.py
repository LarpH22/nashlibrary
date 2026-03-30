from backend.app import get_connection

def print_schema():
    with get_connection() as conn:
        with conn.cursor() as cur:
            for t in ['users', 'students', 'librarians', 'books', 'borrow_records', 'fines']:
                try:
                    cur.execute(f"SHOW CREATE TABLE {t}")
                    row = cur.fetchone()
                    print('---', t, '---')
                    print(row['Create Table'] if row else 'no row')
                except Exception as e:
                    print('---', t, 'error', e)

if __name__ == '__main__':
    print_schema()
