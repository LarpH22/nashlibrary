import pymysql

from ..config import Config


def _candidate_ports():
    ports = [int(Config.DB_PORT)]
    for port in getattr(Config, 'DB_FALLBACK_PORTS', []):
        port = int(port)
        if port not in ports:
            ports.append(port)
    return ports


def _connect(port):
    return pymysql.connect(
        host=Config.DB_HOST,
        port=int(port),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )


def get_connection():
    last_error = None
    for port in _candidate_ports():
        try:
            return _connect(port)
        except pymysql.MySQLError as exc:
            last_error = exc
    raise last_error
