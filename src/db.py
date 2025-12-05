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
        """
        Initialize the database driver.
        Creates a connection to the SQLite database and initializes all tables.
        """
        self.conn = sqlite3.connect(
            "tables.db", check_same_thread=False
        )
        self.create_users_table()
        self.create_beverages_table()
        self.create_consumption_log_table()

    def create_users_table(self):
        """
        Create the users table if it doesn't already exist.
        
        Table schema:
        - id: Primary key (auto-increment)
        - username: Unique username (required)
        - email: User's email address (required)
        - password_hash: Hashed password (required)
        - created_at: Account creation timestamp
        - daily_caffeine_limit: Daily caffeine limit in mg (required)
        - weight_lbs: User's weight in pounds (default: 160.0)
        """
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
        """
        Create the beverages table if it doesn't already exist.
        
        Table schema:
        - id: Primary key (auto-increment)
        - name: Beverage name (required)
        - caffeine_content_mg: Caffeine content in milligrams (required)
        - image_url: URL to beverage image (optional)
        - category: Beverage category (optional)
        """
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
        """
        Create the consumption_log table if it doesn't already exist.
        
        Table schema:
        - id: Primary key (auto-increment)
        - user_id: Foreign key to users table (required)
        - beverage_id: Foreign key to beverages table (required)
        - consumption_time: Timestamp of consumption
        - serving_count: Number of servings consumed (default: 1)
        """
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
        """
        Retrieve all users from the database.
        
        Returns:
            list: A list of dictionaries, each containing user information:
                  id, username, email, password_hash, created_at, 
                  daily_caffeine_limit, weight_lbs
        """
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
        """
        Insert a new user into the database.
        
        Args:
            username (str): Unique username for the user
            email (str): User's email address
            password_hash (str): Hashed password
            daily_caffeine_limit (int): Daily caffeine limit in mg
            weight_lbs (float, optional): User's weight in pounds. Defaults to 160.0
        
        Returns:
            int: The ID of the newly inserted user
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password_hash, daily_caffeine_limit, weight_lbs) VALUES (?, ?, ?, ?, ?);",
            (username, email, password_hash, daily_caffeine_limit, weight_lbs))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_by_id(self, id):
        """
        Retrieve a user by their ID.
        
        Args:
            id (int): The user's ID
        
        Returns:
            dict or None: A dictionary containing user information if found,
                         None otherwise
        """
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
        """
        Retrieve a user by their username.
        
        Args:
            username (str): The user's username
        
        Returns:
            dict or None: A dictionary containing user information if found,
                         None otherwise
        """
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
        """
        Update a user's information by their ID.
        
        Args:
            id (int): The user's ID
            username (str): New username
            email (str): New email address
            password_hash (str): New hashed password
            daily_caffeine_limit (int): New daily caffeine limit in mg
            weight_lbs (float, optional): New weight in pounds. Defaults to 160.0
        """
        self.conn.execute("""
            UPDATE users
            SET username = ?, email = ?, password_hash = ?, daily_caffeine_limit = ?, weight_lbs = ?
            WHERE id = ?;
        """, (username, email, password_hash, daily_caffeine_limit, weight_lbs, id))
        self.conn.commit()

    def delete_user_by_id(self, id):
        """
        Delete a user from the database by their ID.
        
        Args:
            id (int): The user's ID to delete
        """
        self.conn.execute("DELETE FROM users WHERE id = ?;", (id,))
        self.conn.commit()

    def get_all_beverages(self):
        """
        Retrieve all beverages from the database.
        
        Returns:
            list: A list of dictionaries, each containing beverage information:
                  id, name, caffeine_content_mg, image_url, category
        """
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
        """
        Insert a new beverage into the database.
        
        Args:
            name (str): Beverage name
            caffeine_content_mg (int): Caffeine content in milligrams
            image_url (str, optional): URL to beverage image. Defaults to None
            category (str, optional): Beverage category. Defaults to None
        
        Returns:
            int: The ID of the newly inserted beverage
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO beverages (name, caffeine_content_mg, image_url, category) VALUES (?, ?, ?, ?);",
            (name, caffeine_content_mg, image_url, category))
        self.conn.commit()
        return cursor.lastrowid

    def get_beverage_by_id(self, id):
        """
        Retrieve a beverage by its ID.
        
        Args:
            id (int): The beverage's ID
        
        Returns:
            dict or None: A dictionary containing beverage information if found,
                         None otherwise
        """
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
        """
        Update a beverage's information by its ID.
        
        Args:
            id (int): The beverage's ID
            name (str): New beverage name
            caffeine_content_mg (int): New caffeine content in milligrams
            image_url (str, optional): New image URL. Defaults to None
            category (str, optional): New category. Defaults to None
        """
        self.conn.execute("""
            UPDATE beverages
            SET name = ?, caffeine_content_mg = ?, image_url = ?, category = ?
            WHERE id = ?;
        """, (name, caffeine_content_mg, image_url, category, id))
        self.conn.commit()

    def delete_beverage_by_id(self, id):
        """
        Delete a beverage from the database by its ID.
        
        Args:
            id (int): The beverage's ID to delete
        """
        self.conn.execute("DELETE FROM beverages WHERE id = ?;", (id,))
        self.conn.commit()

    def insert_consumption(self, user_id, beverage_id, serving_count=1):
        """
        Insert a new consumption log entry.
        
        Args:
            user_id (int): The ID of the user who consumed the beverage
            beverage_id (int): The ID of the beverage consumed
            serving_count (int, optional): Number of servings consumed. Defaults to 1
        
        Returns:
            int: The ID of the newly inserted consumption log entry
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO consumption_log (user_id, beverage_id, serving_count) VALUES (?, ?, ?);",
            (user_id, beverage_id, serving_count))
        self.conn.commit()
        return cursor.lastrowid

    def get_consumption_by_user_id(self, user_id):
        """
        Retrieve all consumption log entries for a specific user.
        
        Args:
            user_id (int): The user's ID
        
        Returns:
            list: A list of dictionaries, each containing consumption log information:
                  id, user_id, beverage_id, consumption_time, serving_count
        """
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
        """
        Retrieve consumption log entries for a specific user on a specific date.
        
        Args:
            user_id (int): The user's ID
            date (str): The date in 'YYYY-MM-DD' format
        
        Returns:
            list: A list of dictionaries, each containing consumption log information:
                  id, user_id, beverage_id, consumption_time, serving_count
        """
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
        """
        Delete a consumption log entry by its ID.
        
        Args:
            id (int): The consumption log entry's ID to delete
        """
        self.conn.execute("DELETE FROM consumption_log WHERE id = ?;", (id,))
        self.conn.commit()


# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)