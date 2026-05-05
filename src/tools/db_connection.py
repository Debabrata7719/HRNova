"""
MySQL Database Connection Utility for NovaHR
Simple connection management for leave management system
"""

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class DatabaseConnection:
    """Handle MySQL database connections and queries"""

    def __init__(self):
        """Initialize database connection with credentials from .env"""
        self.connection = None
        self.connect()

    def connect(self):
        """Establish MySQL connection"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                buffered=True  # Prevent "Unread result found" errors
            )
            if self.connection.is_connected():
                pass  # Connection successful, no need to print
        except Error as e:
            print(f"Connection error: {e}")
            self.connection = None

    def ensure_connected(self):
        """Reconnect if the connection has gone stale (e.g. MySQL timeout)."""
        try:
            if self.connection and self.connection.is_connected():
                return  # Still alive
        except Exception:
            pass
        # Connection lost — reconnect
        print("[DB] Connection lost, reconnecting...")
        self.connect()

    def execute_query(self, query, params=None):
        """
        Execute a query and return results

        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for parameterized query

        Returns:
            list: Query results
        """
        self.ensure_connected()
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # For SELECT queries, fetch results
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                # For INSERT/UPDATE/DELETE, commit and return rows affected
                self.connection.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                return affected_rows

        except Error as e:
            print(f"DB Query Error: {e}")  # Show errors for debugging
            return None

    def insert_query(self, query, params=None):
        """
        Execute insert query and return last inserted ID

        Args:
            query (str): INSERT SQL query
            params (tuple): Parameters for query

        Returns:
            int: Last inserted row ID, or None on error
        """
        self.ensure_connected()
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id

        except Error as e:
            # Log error to console instead of file (cross-platform)
            print(f"DB Insert Error: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            pass  # Connection closed


# Global connection instance - lazy initialization
db = None


def get_db():
    """Get the global database connection instance (lazy initialization)"""
    global db
    if db is None:
        db = DatabaseConnection()
    return db
