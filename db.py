import sqlite3

DATABASE = 'harry_potter.db'

def get_connection():
    return sqlite3.connect(DATABASE)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT,
                        faculty TEXT,
                        year INTEGER,
                        quidditch_role TEXT,
                        astronomy INTEGER,
                        charms INTEGER,
                        dada INTEGER,
                        potions INTEGER,
                        history_of_magic INTEGER,
                        herbology INTEGER,
                        transfiguration INTEGER,
                        flying INTEGER
                    )''')
    conn.commit()


def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def update_columns():
    conn = get_connection()
    cursor = conn.cursor()
    columns = [
        ('name', 'TEXT'),
        ('faculty', 'TEXT'),
        ('year', 'INTEGER'),
        ('quidditch_role', 'TEXT'),
        ('astronomy', 'INTEGER'),
        ('charms', 'INTEGER'),
        ('dada', 'INTEGER'),
        ('potions', 'INTEGER'),
        ('history_of_magic', 'INTEGER'),
        ('herbology', 'INTEGER'),
        ('transfiguration', 'INTEGER'),
        ('flying', 'INTEGER')
    ]
    for column_name, column_type in columns:
        add_column_if_not_exists(cursor, 'users', column_name, column_type)
    conn.commit()