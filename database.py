import sqlite3

def connect_db(db_name='databaseA.db'):
    return sqlite3.connect(db_name, check_same_thread=False)

def initialize_db(conn, schema_file='schema.sql'):
    with open(schema_file, 'r') as f:
        schema = f.read()
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()

def get_account(conn, account_name):
    cursor = conn.cursor()
    cursor.execute("SELECT account_id, account_name, balance, is_logged_in FROM accounts WHERE account_name = ?", (account_name,))
    row = cursor.fetchone()
    return row if row else None

def update_account_login_status(conn, account_id, status):
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET is_logged_in = ? WHERE account_id = ?", (status, account_id))
    conn.commit()

def update_balance(conn, account_id, new_balance):
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?", (new_balance, account_id))
    conn.commit()

def add_transaction(conn, account_id, transaction_type, amount):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (account_id, transaction_type, amount) VALUES (?, ?, ?)",
                   (account_id, transaction_type, amount))
    conn.commit()

def create_account(conn, account_name):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (account_name, balance) VALUES (?, ?)", (account_name, 0.0))
    conn.commit()
    return cursor.lastrowid  # Trả về ID của tài khoản mới được tạo
