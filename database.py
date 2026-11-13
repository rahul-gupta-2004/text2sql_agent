import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect("business.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            category TEXT,
            units_sold INTEGER,
            revenue REAL,
            sale_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            stock_level INTEGER,
            warehouse_location TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        sample_sales = [
            ("Laptop Pro", "Electronics", 15, 18750.0, "2026-10-01"),
            ("Wireless Mouse", "Electronics", 50, 1250.0, "2026-10-02"),
            ("Ergonomic Chair", "Furniture", 8, 2400.0, "2026-10-03"),
            ("Standing Desk", "Furniture", 5, 3500.0, "2026-10-04"),
            ("USB-C Hub", "Electronics", 30, 900.0, "2026-10-05"),
            ("Monitor 4K", "Electronics", 12, 7200.0, "2026-10-06")
        ]
        cursor.executemany("INSERT INTO sales (product_name, category, units_sold, revenue, sale_date) VALUES (?, ?, ?, ?, ?)", sample_sales)
        
        sample_inventory = [
            ("Laptop Pro", 45, "Mumbai"),
            ("Wireless Mouse", 120, "Bangalore"),
            ("Ergonomic Chair", 15, "Mumbai"),
            ("Standing Desk", 10, "Bangalore"),
            ("USB-C Hub", 200, "Mumbai"),
            ("Monitor 4K", 25, "Bangalore")
        ]
        cursor.executemany("INSERT INTO inventory (product_name, stock_level, warehouse_location) VALUES (?, ?, ?)", sample_inventory)
        conn.commit()
    return conn

def get_table_data(table_name, conn):
    return pd.read_sql(f"SELECT * FROM {table_name}", conn)