"""
MySQL Database Connection Utility for NovaHR
Uses tenacity for retry logic and proper logging.
"""

import mysql.connector
from mysql.connector import Error
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception,
    before_sleep_log,
)
from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)

# MySQL errno codes that mean the connection was dropped by the server
_CONNECTION_ERRORS = {2006, 2013, 2055}


def _is_connection_error(exc: BaseException) -> bool:
    """Return True only for transient MySQL connection errors worth retrying."""
    if isinstance(exc, Error):
        return getattr(exc, "errno", None) in _CONNECTION_ERRORS
    # Also retry if reconnect itself failed (no connection available)
    if isinstance(exc, RuntimeError) and "No database connection" in str(exc):
        return True
    return False


class DatabaseConnection:
    """
    MySQL connection wrapper with automatic reconnection and query retry.

    - ping(reconnect=True) verifies the socket is alive before every query
    - tenacity retries on connection-drop errors (errno 2006/2013/2055)
    - Proper logging replaces print() statements
    """

    def __init__(self):
        self.connection = None
        self._connect()

    # ── Connection management ─────────────────────────────────────────

    def _connect(self):
        """Open a fresh MySQL connection."""
        cfg = get_settings()
        try:
            self.connection = mysql.connector.connect(
                host=cfg.DB_HOST,
                user=cfg.DB_USER,
                password=cfg.DB_PASSWORD,
                database=cfg.DB_NAME,
                buffered=True,
                autocommit=False,
                connection_timeout=10,
            )
            logger.info("Connected to MySQL database '%s'", cfg.DB_NAME)
        except Error as e:
            logger.error("MySQL connection failed: %s", e)
            self.connection = None

    def _ensure_connected(self):
        """Guarantee the connection is alive using ping."""
        try:
            if self.connection:
                self.connection.ping(reconnect=True, attempts=3, delay=1)
                return  # ping succeeded — connection is alive
        except Exception:
            pass
        # ping failed — force close the old connection and open a fresh one
        try:
            if self.connection:
                self.connection.close()
        except Exception:
            pass
        self.connection = None
        logger.warning("MySQL connection lost — reconnecting...")
        self._connect()

    # ── Query execution ───────────────────────────────────────────────

    def execute_query(self, query: str, params=None):
        """
        Execute a SQL query with tenacity retry on connection errors.

        Returns:
            list  — SELECT results (list of dicts)
            int   — rows affected for INSERT/UPDATE/DELETE
            None  — on unrecoverable error
        """
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_fixed(1),
            retry=retry_if_exception(_is_connection_error),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=False,
        )
        def _run():
            self._ensure_connected()
            if not self.connection:
                raise RuntimeError("No database connection available")

            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params) if params else cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                affected = cursor.rowcount
                cursor.close()
                return affected

        try:
            return _run()
        except Exception as e:
            logger.error("Query failed: %s | Query: %.120s", e, query)
            return None

    def insert_query(self, query: str, params=None):
        """
        Execute an INSERT and return the last inserted row ID.

        Returns:
            int  — last inserted row ID
            None — on error
        """
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_fixed(1),
            retry=retry_if_exception(_is_connection_error),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=False,
        )
        def _run():
            self._ensure_connected()
            if not self.connection:
                raise RuntimeError("No database connection available")

            cursor = self.connection.cursor()
            cursor.execute(query, params) if params else cursor.execute(query)
            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id

        try:
            return _run()
        except Exception as e:
            logger.error("Insert failed: %s | Query: %.120s", e, query)
            return None

    def close(self):
        """Close the database connection."""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("MySQL connection closed")
        except Exception:
            pass


# ── Global singleton ──────────────────────────────────────────────────────────

import logging  # noqa: E402  (needed for before_sleep_log)

_db: DatabaseConnection | None = None


def get_db() -> DatabaseConnection:
    """
    Return the global DatabaseConnection instance.
    Recreates it if the connection is gone or broken.
    """
    global _db
    if _db is None or _db.connection is None:
        _db = DatabaseConnection()
    return _db
