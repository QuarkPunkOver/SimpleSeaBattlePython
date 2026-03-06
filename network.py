import socket
import json
import threading
import queue
from config import Debug_status

class NetworkGame:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.opponent_ready = False
        self.both_ready = False
        self.my_turn = False
        self.game_started = False
        self.is_server = False
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.message_queue = queue.Queue()
        self.listener_thread = None
        self.local_ip = self.get_local_ip()
        self.players_count = 0
        self.host_connected = False
        self.lock = threading.Lock()
        self.clients = []
        
    def debug_print(self, message):
        if Debug_status:
            print(f"[NETWORK] {message}")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def scan_network(self, progress_callback=None):
        servers = []
        local_ip = self.get_local_ip()
        
        ip_parts = local_ip.split('.')
        if len(ip_parts) != 4:
            return servers
            
        base_ip = '.'.join(ip_parts[:3])
        
        ips_to_scan = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            ips_to_scan.append(ip)
        
        total_ips = len(ips_to_scan)
        scanned = 0
        scan_lock = threading.Lock()
        
        def scan_ip(ip):
            nonlocal scanned
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                result = sock.connect_ex((ip, 5555))
                
                if result == 0:
                    try:
                        sock.send(json.dumps({"type": "server_info"}).encode())
                        sock.settimeout(0.3)
                        data = sock.recv(1024).decode()
                        
                        if data:
                            response = json.loads(data)
                            if response.get("type") == "server_info_response":
                                with scan_lock:
                                    servers.append({
                                        "ip": ip,
                                        "name": response.get("name", "Сервер"),
                                        "players": response.get("players", 0),
                                        "max_players": response.get("max_players", 2)
                                    })
                    except Exception as e:
                        pass
                
                sock.close()
            except Exception as e:
                pass
            finally:
                with scan_lock:
                    scanned += 1
                    if progress_callback and scanned % 10 == 0:
                        progress_callback(scanned, total_ips)
        
        threads = []
        for i in range(0, len(ips_to_scan), 20):
            batch = ips_to_scan[i:i + 20]
            for ip in batch:
                thread = threading.Thread(target=scan_ip, args=(ip,))
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join(timeout=0.3)
            threads = []
        
        if progress_callback:
            progress_callback(total_ips, total_ips)
        
        return servers
    
    def start_server(self):
        self.is_server = True
        self.running = True
        with self.lock:
            self.players_count = 1
            self.host_connected = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def _run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', 5555))
        self.server_socket.listen(10)
        self.server_socket.settimeout(1.0)
        
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                
                client.settimeout(0.5)
                try:
                    data = client.recv(1024).decode()
                    if data:
                        message = json.loads(data)
                        
                        if message.get("type") == "server_info":
                            self._handle_info_request(client, addr)
                            continue
                        
                        self._handle_game_client(client, addr, message)
                    else:
                        client.close()
                        
                except socket.timeout:
                    self._handle_game_client(client, addr, None)
                except Exception as e:
                    client.close()
                    
            except socket.timeout:
                continue
            except Exception as e:
                break
        
        if self.server_socket:
            self.server_socket.close()

    def _handle_info_request(self, client_socket, addr):
        try:
            with self.lock:
                players = self.players_count
            
            response = {
                "type": "server_info_response",
                "name": "Морской бой",
                "players": players,
                "max_players": 2
            }
            client_socket.send(json.dumps(response).encode())
        except Exception as e:
            pass
        finally:
            client_socket.close()
    
    def _handle_game_client(self, client_socket, addr, first_message):
        with self.lock:
            current_players = self.players_count
        
        if current_players >= 2:
            try:
                client_socket.send(json.dumps({"type": "error", "message": "Сервер заполнен"}).encode())
            except:
                pass
            client_socket.close()
            return
        
        with self.lock:
            self.players_count += 1
        
        with self.lock:
            self.clients.append(client_socket)
            self.client_socket = client_socket
            self.connected = True
        
        if first_message:
            self.message_queue.put(first_message)
        
        listener = threading.Thread(target=self._listen, args=(client_socket, addr))
        listener.daemon = True
        listener.start()
    
    def connect(self, ip):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(2.0)
            self.socket.connect((ip, 5555))
            
            self.connected = True
            self.running = True
            
            self.listener_thread = threading.Thread(target=self._listen, args=(self.socket, ip))
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            return True
        except Exception as e:
            return False
    
    def _listen(self, sock, addr="unknown"):
        sock.settimeout(1.0)
        
        while self.running and self.connected:
            try:
                data = sock.recv(16384).decode()
                if data:
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        response = {"type": "pong"}
                        try:
                            sock.send(json.dumps(response).encode())
                        except:
                            pass
                    else:
                        self.message_queue.put(message)
                else:
                    break
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                pass
            except Exception as e:
                break
        
        if self.is_server:
            with self.lock:
                if sock in self.clients:
                    self.clients.remove(sock)
                    self.players_count = max(0, self.players_count - 1)
        
        self.connected = False
        try:
            sock.close()
        except:
            pass
    
    def send_data(self, data):
        try:
            if self.is_server:
                with self.lock:
                    for client in self.clients:
                        try:
                            client.send(json.dumps(data).encode())
                        except:
                            pass
            elif self.socket and self.connected:
                self.socket.send(json.dumps(data).encode())
        except Exception as e:
            pass
    
    def get_message(self):
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None
        
    def stop(self):
        self.running = False
        if self.is_server:
            if self.server_socket:
                self.server_socket.close()
            with self.lock:
                for client in self.clients:
                    try:
                        client.close()
                    except:
                        pass
                self.clients = []
        else:
            if self.socket:
                self.socket.close()