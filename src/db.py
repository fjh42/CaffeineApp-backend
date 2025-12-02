import os
import sqlite3

# From: https://goo.gl/YzypOI
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class DatabaseDriver(object):
    """
    Database driver for the Caffeine Tracker app.
    Handles reading and writing data with the database.

    """

    def __init__(self):
        self.conn = sqlite3.connect(
            "tables.db", check_same_thread=False
        )
        self.create_users_table()
        self.create_beverages_table()
        self.create_consumption_log_table()

    def create_users_table(self):
        try:
            self.conn.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    daily_caffeine_limit INTEGER NOT NULL,
                    weight_lbs REAL DEFAULT 160.0
                );
            """)
        except Exception as e:
            print(e)

    def create_beverages_table(self):
        try:
            self.conn.execute("""
                CREATE TABLE beverages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    caffeine_content_mg INTEGER NOT NULL,
                    image_url TEXT,
                    category TEXT
                );
            """)
        except Exception as e:
            print(e)

    def create_consumption_log_table(self):
        try:
            self.conn.execute("""
                CREATE TABLE consumption_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    beverage_id INTEGER NOT NULL,
                    consumption_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    serving_count INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (beverage_id) REFERENCES beverages(id)
                );
            """)
        except Exception as e:
            print(e)

    def get_all_users(self):
        cursor = self.conn.execute("SELECT * FROM users;")
        users = []
        for row in cursor:
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "password_hash": row[3],
                "created_at": row[4],
                "daily_caffeine_limit": row[5],
                "weight_lbs": row[6]
            })
        return users

    def insert_user(self, username, email, password_hash, daily_caffeine_limit, weight_lbs=160.0):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password_hash, daily_caffeine_limit, weight_lbs) VALUES (?, ?, ?, ?, ?);",
            (username, email, password_hash, daily_caffeine_limit, weight_lbs))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_by_id(self, id):
        cursor = self.conn.execute("SELECT * FROM users WHERE id = ?;", (id,))
        for row in cursor:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "password_hash": row[3],
                "created_at": row[4],
                "daily_caffeine_limit": row[5],
                "weight_lbs": row[6]
            }
        return None

    def get_user_by_username(self, username):
        cursor = self.conn.execute("SELECT * FROM users WHERE username = ?;", (username,))
        for row in cursor:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "password_hash": row[3],
                "created_at": row[4],
                "daily_caffeine_limit": row[5],
                "weight_lbs": row[6]
            }
        return None

    def update_user_by_id(self, id, username, email, password_hash, daily_caffeine_limit, weight_lbs=160.0):
        self.conn.execute("""
            UPDATE users
            SET username = ?, email = ?, password_hash = ?, daily_caffeine_limit = ?, weight_lbs = ?
            WHERE id = ?;
        """, (username, email, password_hash, daily_caffeine_limit, weight_lbs, id))
        self.conn.commit()

    def delete_user_by_id(self, id):
        self.conn.execute("DELETE FROM users WHERE id = ?;", (id,))
        self.conn.commit()

    def get_all_beverages(self):
        cursor = self.conn.execute("SELECT * FROM beverages;")
        beverages = []
        for row in cursor:
            beverages.append({
                "id": row[0],
                "name": row[1],
                "caffeine_content_mg": row[2],
                "image_url": row[3],
                "category": row[4]
            })
        return beverages

    def insert_beverage(self, name, caffeine_content_mg, image_url=None, category=None):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO beverages (name, caffeine_content_mg, image_url, category) VALUES (?, ?, ?, ?);",
            (name, caffeine_content_mg, image_url, category))
        self.conn.commit()
        return cursor.lastrowid

    def get_beverage_by_id(self, id):
        cursor = self.conn.execute("SELECT * FROM beverages WHERE id = ?;", (id,))
        for row in cursor:
            return {
                "id": row[0],
                "name": row[1],
                "caffeine_content_mg": row[2],
                "image_url": row[3],
                "category": row[4]
            }
        return None

    def update_beverage_by_id(self, id, name, caffeine_content_mg, image_url=None, category=None):
        self.conn.execute("""
            UPDATE beverages
            SET name = ?, caffeine_content_mg = ?, image_url = ?, category = ?
            WHERE id = ?;
        """, (name, caffeine_content_mg, image_url, category, id))
        self.conn.commit()

    def delete_beverage_by_id(self, id):
        self.conn.execute("DELETE FROM beverages WHERE id = ?;", (id,))
        self.conn.commit()

    def insert_consumption(self, user_id, beverage_id, serving_count=1):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO consumption_log (user_id, beverage_id, serving_count) VALUES (?, ?, ?);",
            (user_id, beverage_id, serving_count))
        self.conn.commit()
        return cursor.lastrowid

    def get_consumption_by_user_id(self, user_id):
        cursor = self.conn.execute("SELECT * FROM consumption_log WHERE user_id = ?;", (user_id,))
        consumptions = []
        for row in cursor:
            consumptions.append({
                "id": row[0],
                "user_id": row[1],
                "beverage_id": row[2],
                "consumption_time": row[3],
                "serving_count": row[4]
            })
        return consumptions

    def get_consumption_by_user_and_date(self, user_id, date):
        cursor = self.conn.execute("SELECT * FROM consumption_log WHERE user_id = ? AND DATE(consumption_time) = ?;", (user_id, date))
        consumptions = []
        for row in cursor:
            consumptions.append({
                "id": row[0],
                "user_id": row[1],
                "beverage_id": row[2],
                "consumption_time": row[3],
                "serving_count": row[4]
            })
        return consumptions

    def delete_consumption_by_id(self, id):
        self.conn.execute("DELETE FROM consumption_log WHERE id = ?;", (id,))
        self.conn.commit()


# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)