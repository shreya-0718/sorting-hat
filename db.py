# to put all database related functions here (because my bot.py is getting messy)

import sqlite3


def init_db():
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            house TEXT,
            points INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


"""
    note to self, the database is being assigned like so:
    (user_id, house, points)
    the house is in lowercase!
"""

def assign_to_house(user_id, house):
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("""
            INSERT INTO users (id, house, points)
            VALUES (?, ?, COALESCE((SELECT points FROM users WHERE id = ?), 0))
            ON CONFLICT(id) DO UPDATE SET house=excluded.house
        """, (user_id, house, user_id))  # sets person's house! and updates the house!


    conn.commit()
    conn.close()


def print_all_assignments():
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()

    print("all current students:") # for my own sake haha
    for row in rows:
        print(row)

def get_user_points(user_id):
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]