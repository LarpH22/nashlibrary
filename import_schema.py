import pymysql

DB_NAME = 'library_system_v2'


def parse_sql(sql_text):
    sql_text = sql_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = sql_text.split('\n')
    delimiter = ';'
    statement = ''
    statements = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue
        if stripped.upper().startswith('DELIMITER '):
            delimiter = stripped.split(' ', 1)[1]
            continue
        statement += line + '\n'
        if statement.rstrip().endswith(delimiter):
            statements.append(statement.rstrip()[:-len(delimiter)].strip())
            statement = ''

    if statement.strip():
        statements.append(statement.strip())

    return statements


# Read the SQL file
with open('database_schema.sql', 'r', encoding='utf8') as f:
    sql_content = f.read()

# Connect to MySQL without specifying a database initially
conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME}')
        print(f'Database {DB_NAME} created/verified')
    conn.commit()

    conn.close()
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='',
        database=DB_NAME,
        charset='utf8mb4'
    )

    with conn.cursor() as cur:
        statements = parse_sql(sql_content)
        for statement in statements:
            if not statement:
                continue
            try:
                cur.execute(statement)
            except pymysql.Error as e:
                print('SQL error:', e)
                print('  Statement:', statement[:200].replace('\n', ' '))

    conn.commit()

    with conn.cursor() as cur:
        cur.execute('SHOW TABLES')
        tables = cur.fetchall()
        print(f'Imported {len(tables)} tables into {DB_NAME}')
        for table in tables:
            print('  -', table[0])

except Exception as e:
    print('Error:', e)
finally:
    conn.close()

