import socket
import time
import queue
from lib.database import Database

db = Database()

class VirtualSocket:
    def __init__(self):
        self.cmd_queue = queue.Queue()
        self.resp_queue = queue.Queue()
        self.connected = True
    def send(self, data): self.cmd_queue.put(data)
    def recv(self, size):
        try: return self.resp_queue.get(timeout=4.0)
        except queue.Empty: return b""
    def close(self): self.connected = False
    def setblocking(self, mode): pass
    def settimeout(self, t): pass

class SessionManager:
    def __init__(self):
        self.sessions = {}
        # FIX: Start counting from the last known ID in the DB
        self.next_id = db.get_max_session_id() + 1 

    def add_session(self, client_socket, address, is_http=False):
        uid = "UNKNOWN"
        if not is_http:
            try:
                client_socket.settimeout(2.0)
                handshake = client_socket.recv(1024).decode()
                if handshake.startswith("AUTH:"):
                    uid = handshake.split(":")[1]
            except: pass 
            finally: client_socket.settimeout(None)

        proto = "HTTP" if is_http else "TCP"
        final_id = db.register_session(uid, self.next_id, address[0], proto)
        
        if final_id == self.next_id:
            self.next_id += 1

        self.sessions[final_id] = {
            'socket': client_socket,
            'address': address,
            'is_http': is_http,
            'uid': uid,
            'status': 'Active'
        }
        return final_id

    def remove_session(self, sid):
        if sid in self.sessions:
            uid = self.sessions[sid]['uid']
            db.update_status(uid, 'Dead')
            try: self.sessions[sid]['socket'].close()
            except: pass
            del self.sessions[sid]

    def list_sessions(self):
        all_sessions = db.get_all_sessions()
        if not all_sessions: return "No sessions found."
        
        # We now highlight the UID since that is what you will use
        lines = ["\nSession History:", "ID   Proto   IP Address       Status   UID (Use This)", "---  -----   ---------------  ------   --------------"]
        for sid, proto, ip, status, uid in all_sessions:
            lines.append(f"{sid:<4} {proto:<7} {ip:<16} {status:<8} {uid}")
        
        return "\n".join(lines)

    # --- NEW HELPER FOR UUID LOOKUP ---
    def get_session_by_uid(self, target_uid):
        """Find an active session socket by its UUID string"""
        for sid, info in self.sessions.items():
            if info['uid'] == target_uid:
                return sid, info
        return None, None