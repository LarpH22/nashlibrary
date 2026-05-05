#!/usr/bin/env python
import pymysql
from backend.config import Config

def column_exists(table, column):
    with pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4'
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS cnt
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
            """, (Config.DB_NAME, table, column))
            return cur.fetchone()[0] > 0

def get_table_primary_key(table, candidate_columns):
    for column in candidate_columns:
        if column_exists(table, column):
            return column
    return None

def get_books_id_column():
    return get_table_primary_key('books', ['book_id', 'id']) or 'book_id'

result = get_books_id_column()
print(f'get_books_id_column() returns: {result}')
print(f'column_exists("books", "book_id"): {column_exists("books", "book_id")}')
print(f'column_exists("books", "id"): {column_exists("books", "id")}')
