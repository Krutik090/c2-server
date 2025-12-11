import sqlite3

class Database:
    def __init__(self, db_file="c2.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS listeners (
                port INTEGER PRIMARY KEY, 
                protocol TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                uid TEXT PRIMARY KEY,
                session_id INTEGER,
                ip TEXT,
                protocol TEXT,
                status TEXT
            )
        """)
        self.conn.commit()

    def add_listener(self, protocol, port):
        try:
            self.cursor.execute("INSERT INTO listeners (protocol, port) VALUES (?, ?)", (protocol, port))
            self.conn.commit()
        except sqlite3.IntegrityError: pass

    def remove_listener(self, port):
        self.cursor.execute("DELETE FROM listeners WHERE port=?", (port,))
        self.conn.commit()

    def get_listeners(self):
        self.cursor.execute("SELECT protocol, port FROM listeners")
        return self.cursor.fetchall()

    def register_session(self, uid, session_id, ip, protocol):
        self.cursor.execute("SELECT session_id FROM sessions WHERE uid=?", (uid,))
        data = self.cursor.fetchone()
        
        if data:
            old_id = data[0]
            self.cursor.execute("UPDATE sessions SET status='Active', ip=? WHERE uid=?", (ip, uid))
            self.conn.commit()
            return old_id
        else:
            self.cursor.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, 'Active')", (uid, session_id, ip, protocol))
            self.conn.commit()
            return session_id

    def update_status(self, uid, status):
        self.cursor.execute("UPDATE sessions SET status=? WHERE uid=?", (status, uid))
        self.conn.commit()

    def get_all_sessions(self):
        self.cursor.execute("SELECT session_id, protocol, ip, status, uid FROM sessions")
        return self.cursor.fetchall()

    # --- NEW FUNCTION ---
    def get_max_session_id(self):
        """Find the highest Session ID so we don't duplicate them on restart"""
        self.cursor.execute("SELECT MAX(session_id) FROM sessions")
        data = self.cursor.fetchone()
        if data and data[0] is not None:
            return data[0]
        return -1 # So the next one starts at 0