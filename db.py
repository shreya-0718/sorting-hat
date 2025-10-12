# to put all database related functions here (because my bot.py is getting messy)

import sqlite3
import requests
import html

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            user_id TEXT,
            question_id TEXT,
            correct_answer TEXT,
            difficulty TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    testing = cursor.fetchone()
    print(testing)
    conn.close()

    if result:
        return result[0]
    else:
        return "points could not be found"
    
def get_user_house(user_id):
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT house FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return "(house could not be found sorry)"
    
def get_house_points(house):
    if house.startswith("("):
        return "N/A"

    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(points) FROM users WHERE house = ?", (house,))
    result = cursor.fetchone()
    conn.close()

    return result[0] or 0

def add_points(user_id, points):
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))    
    print(f"added {points} to user")
    conn.commit()
    conn.close()

def get_quiz(user_id):
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM quiz_sessions WHERE user_id = ?", (user_id,))

    response = requests.get("https://opentdb.com/api.php?amount=5&type=multiple")

    
    for q in response.json()["results"]:
        question_id = q["question"]
        correct = html.unescape(q["correct_answer"])
        difficulty = q["difficulty"]
        cursor.execute("""
            INSERT INTO quiz_sessions (user_id, question_id, correct_answer, difficulty)
            VALUES (?, ?, ?, ?)
        """, (user_id, question_id, correct, difficulty))
    conn.commit()
    conn.close()


    return response.json()["results"]

def get_quiz_row(user_id):
    conn = sqlite3.connect("hogwarts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question_id, correct_answer, difficulty FROM quiz_sessions WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    return rows