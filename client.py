import socket
import json
import sys
try:
    import readline # Enables Up-Arrow History on Linux
except ImportError:
    pass # Windows doesn't have standard readline, but will run fine without history

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

def send_request(data):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))
        client.send(json.dumps(data).encode())
        # Increase buffer size slightly to handle larger session lists
        response = client.recv(16384).decode()
        client.close()
        return response
    except ConnectionRefusedError:
        return "[-] Could not connect to Team Server. Is it running?"
    except Exception as e:
        return f"[-] Error: {e}"

def interact_shell(uid):
    # UPDATED: Now accepts a UUID string (uid) instead of an integer (sid)
    print(f"[*] Entered Session {uid}. Type 'background' to exit.")
    while True:
        try:
            cmd = input(f"Shell({uid})> ")
            if cmd == 'background': break
            if not cmd.strip(): continue

            # UPDATED: Sends 'uid' key to match the new teamserver logic
            req = {'action': 'exec_command', 'uid': uid, 'cmd': cmd}
            print(send_request(req))
        except KeyboardInterrupt:
            print("\n[*] Backgrounding...")
            break

def print_help():
    print("\n--- C2 Help Menu ---")
    print(f"{'listener -g <proto> -p <port>':<35} : Start a listener (tcp/http)")
    print(f"{'jobs':<35} : List active listeners")
    print(f"{'killjob <id>':<35} : Stop a listener")
    print(f"{'sessions':<35} : List active shells")
    # UPDATED: Help text now correctly asks for UUID
    print(f"{'use <uuid>':<35} : Interact with a shell") 
    print(f"{'exit':<35} : Quit the client")

def main():
    print("--- C2 Client (UI) ---")
    print("Type 'help' for commands.")
    
    while True:
        try:
            cmd_str = input("C2_Client> ")
            cmd = cmd_str.split()
            if not cmd: continue

            if cmd[0] == 'help':
                print_help()

            elif cmd[0] == 'listener':
                try:
                    if '-g' not in cmd or '-p' not in cmd:
                        print("[-] Usage: listener -g <protocol> -p <port>")
                        continue

                    g_index = cmd.index('-g') + 1
                    p_index = cmd.index('-p') + 1
                    
                    protocol = cmd[g_index]
                    port = int(cmd[p_index])
                    
                    req = {'action': 'start_listener', 'protocol': protocol, 'port': port}
                    print(send_request(req))
                except (ValueError, IndexError):
                    print("[-] Error: Port must be a number and protocol specified.")

            elif cmd[0] == 'jobs':
                print(send_request({'action': 'get_jobs'}))

            elif cmd[0] == 'killjob':
                if len(cmd) < 2:
                    print("[-] Usage: killjob <id>")
                    continue
                try:
                    jid = int(cmd[1])
                    print(send_request({'action': 'stop_job', 'job_id': jid}))
                except ValueError:
                    print("[-] Job ID must be an integer.")

            elif cmd[0] == 'sessions':
                print(send_request({'action': 'get_sessions'}))

            elif cmd[0] == 'use':
                # UPDATED: Removed int() conversion
                if len(cmd) < 2:
                    print("[-] Usage: use <uuid>")
                    continue
                
                # Pass the raw string (UUID) to the interaction function
                target_uid = cmd[1]
                interact_shell(target_uid)

            elif cmd[0] == 'exit':
                sys.exit(0)
            
            else:
                print("[-] Unknown command. Type 'help'.")

        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"[-] Client Error: {e}")

if __name__ == "__main__":
    main()