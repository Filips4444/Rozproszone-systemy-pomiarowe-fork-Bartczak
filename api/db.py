import psycopg2

DB_HOST = "database"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

def get_connection():
    return psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)