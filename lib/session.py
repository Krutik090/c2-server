import socket
import time
import queue

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
        self.next_id = 0

    def add_session(self, client_socket, address, is_http=False):
        sid = self.next_id
        self.sessions[sid] = {
            'socket': client_socket,
            'address': address,
            'is_http': is_http,
            'last_seen': time.time()
        }
        self.next_id += 1
        return sid

    def remove_session(self, sid):
        """Removes a session from the list"""
        if sid in self.sessions:
            try:
                self.sessions[sid]['socket'].close()
            except: pass
            del self.sessions[sid]

    def list_sessions(self):
        if not self.sessions: return "No active sessions."
        lines = ["\nActive Sessions:", "ID   Type   IP Address", "---  ----   ----------"]
        for sid, info in self.sessions.items():
            sType = "HTTP" if info.get('is_http') else "TCP"
            lines.append(f"{sid:<4} {sType:<6} {info['address'][0]}")
        return "\n".join(lines)

    def get_session(self, sid):
        return self.sessions.get(sid)