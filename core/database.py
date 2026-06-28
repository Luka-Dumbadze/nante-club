import sqlite3

def initialize_db():
    conn = sqlite3.connect('nante_club.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Admin', 'Cashier'))
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Spaces (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        type TEXT NOT NULL, rate_per_hour REAL NOT NULL, is_active BOOLEAN DEFAULT 0
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        price REAL NOT NULL, stock_quantity INTEGER NOT NULL DEFAULT 0
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, space_id INTEGER,
        start_time DATETIME NOT NULL, end_time DATETIME,
        time_amount REAL DEFAULT 0, status TEXT DEFAULT 'Active',
        FOREIGN KEY(space_id) REFERENCES Spaces(id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER,
        cash_amount REAL DEFAULT 0, card_amount REAL DEFAULT 0,
        terminal_type TEXT, total_paid REAL NOT NULL,
        transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        cashier_name TEXT,
        FOREIGN KEY(session_id) REFERENCES Sessions(id)
    )''')
    
    try:
        cursor.execute("ALTER TABLE Transactions ADD COLUMN cashier_name TEXT")
    except sqlite3.OperationalError:
        pass 

    cursor.execute('''CREATE TABLE IF NOT EXISTS SessionOrders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER,
        product_id INTEGER, quantity INTEGER NOT NULL, subtotal REAL NOT NULL,
        FOREIGN KEY(session_id) REFERENCES Sessions(id), FOREIGN KEY(product_id) REFERENCES Products(id)
    )''')

    # --- 🆕 აქ დაემატა ჯავშნების ცხრილი ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS Reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        space_id INTEGER,
        customer_name TEXT,
        reserved_time DATETIME NOT NULL,
        FOREIGN KEY(space_id) REFERENCES Spaces(id)
    )''')

    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        cursor.execute("INSERT INTO Users (username, password, role) VALUES ('cashier1', 'cashier123', 'Cashier')")

    cursor.execute("SELECT COUNT(*) FROM Spaces")
    if cursor.fetchone()[0] == 0:
        spaces_data = [('Billiard Table 1', 'Standard Billiard', 20.0), ('Billiard Table 2', 'Standard Billiard', 20.0),
                       ('Billiard Table 3', 'Standard Billiard', 20.0), ('VIP Billiard Room', 'VIP Billiard', 40.0),
                       ('PlayStation Room 1', 'PS Room', 15.0), ('PlayStation Room 2', 'PS Room', 15.0),
                       ('PlayStation Room 3', 'PS Room', 15.0), ('PlayStation Room 4', 'PS Room', 15.0)]
        cursor.executemany("INSERT INTO Spaces (name, type, rate_per_hour) VALUES (?, ?, ?)", spaces_data)

    cursor.execute("SELECT COUNT(*) FROM Products")
    if cursor.fetchone()[0] == 0:
        products = [('კოკა-კოლა 0.5ლ', 3.0, 50), ('წყალი ბაკურიანი', 2.0, 100), ('ჩიფსი ლეისი', 4.5, 30)]
        cursor.executemany("INSERT INTO Products (name, price, stock_quantity) VALUES (?, ?, ?)", products)

    conn.commit()
    conn.close()