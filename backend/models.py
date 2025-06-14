#to create and check database users.db
import sqlite3
import os

DATABASE = 'users.db'

def init_db():
    """Ensures the database and users table exist."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Ensure the users table is created
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                allergies TEXT,
                health_conditions TEXT,
                diet TEXT
            )
        ''')
        conn.commit()
        print("✅ Database and users table ensured.")

def fetch_all_users():
    """Fetch and print all users and their details."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username, email, allergies, health_conditions, diet FROM users")
            users = cursor.fetchall()

            if not users:
                print("⚠️ No users found in the database.")
            else:
                print("\n📋 User Details:\n")
                for user in users:
                    user_id, username, email, allergies, health_conditions, diet = user
                    print(f"🆔 ID: {user_id}")
                    print(f"👤 Username: {username}")
                    print(f"📧 Email: {email}")
                    print(f"🚫 Allergies: {allergies or 'None'}")
                    print(f"💊 Health Conditions: {health_conditions or 'None'}")
                    print(f"🥗 Diet: {diet or 'Not Specified'}")
                    print("-" * 40)
        except sqlite3.OperationalError as e:
            print(f"❌ Error: {e}")
            print("⚠️ Make sure the users table exists. Try running init_db() again.")

# Run when executing models.py alone
if __name__ == '__main__':
    init_db()  # Ensure DB and table exist
    fetch_all_users()  # Print all users
