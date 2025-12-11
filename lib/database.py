import sqlite3

class Database:
    def __init__(self, db_file="c2.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Creates the necessary tables if they don't exist"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS listeners (
                port INTEGER PRIMARY KEY, 
                protocol TEXT
            )
        """)
        self.conn.commit()

    def add_listener(self, protocol, port):
        """Saves a listener configuration"""
        try:
            self.cursor.execute("INSERT INTO listeners (protocol, port) VALUES (?, ?)", (protocol, port))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass # Already exists

    def remove_listener(self, port):
        """Removes a listener configuration"""
        self.cursor.execute("DELETE FROM listeners WHERE port=?", (port,))
        self.conn.commit()

    def get_listeners(self):
        """Returns a list of (protocol, port) tuples to restore"""
        self.cursor.execute("SELECT protocol, port FROM listeners")
        return self.cursor.fetchall()