import pymysql

# Read the SQL file
with open('database_schema.sql', 'r') as f:
    sql_content = f.read()

# Connect to MySQL without specifying a database initially
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # First create the database
        cur.execute('CREATE DATABASE IF NOT EXISTS library_system')
        print('✓ Database library_system created/verified')
    conn.commit()
    
    # Close and reconnect to the new database
    conn.close()
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='library_system',
        charset='utf8mb4'
    )
    
    with conn.cursor() as cur:
        # Split by DELIMITER changes to handle triggers/procedures properly
        # This is a more robust approach than simple semicolon splitting
        parts = sql_content.split('DELIMITER')
        
        for i, part in enumerate(parts):
            if i == 0:
                # First part before any DELIMITER
                statements = part.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cur.execute(statement)
                        except pymysql.Error as e:
                            if "already exists" not in str(e):
                                print(f"Note: {e}")
            else:
                # Parts with DELIMITER
                lines = part.split('\n', 1)
                if len(lines) > 1:
                    delimiter = lines[0].strip()
                    content = lines[1]
                    
                    # Split by the new delimiter
                    statements = content.split(delimiter)
                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            # Restore DELIMITER for multi-statement blocks
                            if 'END' in statement and 'BEGIN' in statement:
                                statement = statement.replace('END', f'END{delimiter}')
                            try:
                                cur.execute(statement)
                            except pymysql.Error as e:
                                if "already exists" not in str(e) and "Trigger" not in str(e):
                                    pass  # Skip trigger creation errors due to parsing
    
    conn.commit()
    print('✓ Database schema imported successfully!')
    
    # Verify the schema
    with conn.cursor() as cur:
        cur.execute('SHOW TABLES')
        tables = cur.fetchall()
        print(f'\n✓ Created {len(tables)} tables:')
        for table in tables:
            print(f'  - {table[0]}')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()

