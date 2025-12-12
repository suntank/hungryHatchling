"""
Network Discovery for LAN Multiplayer
Uses UDP broadcast for automatic server discovery (Quake 3 style)
"""

import socket
import threading
import time

# Discovery constants
DISCOVERY_PORT = 50000          # UDP port for discovery broadcasts
GAME_PORT = 5555                # TCP port for actual game connections
DISCOVERY_MAGIC = b"PYSNAKE_DISCOVER_V1"
RESPONSE_MAGIC = b"PYSNAKE_RESPONSE_V1"
HEARTBEAT_INTERVAL = 1.0        # Seconds between heartbeat broadcasts


class DiscoveryServer:
    """Broadcasts server presence on LAN via UDP heartbeats"""
    
    def __init__(self, server_name: str, game_port: int = GAME_PORT):
        self.server_name = server_name
        self.game_port = game_port
        self.running = False
        self.socket = None
        self.broadcast_thread = None
        
    def start(self):
        """Start broadcasting server presence"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.running = True
            self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.broadcast_thread.start()
            
            print(f"[discovery] Broadcasting server '{self.server_name}' on port {DISCOVERY_PORT}")
            return True
        except Exception as e:
            print(f"[discovery] Failed to start: {e}")
            return False
    
    def _broadcast_loop(self):
        """Periodically broadcast server heartbeat"""
        while self.running:
            try:
                # Build heartbeat payload: magic|name|port
                payload = f"{self.server_name}|{self.game_port}".encode("utf-8")
                message = RESPONSE_MAGIC + b"|" + payload
                
                # Broadcast to LAN
                self.socket.sendto(message, ("<broadcast>", DISCOVERY_PORT))
            except Exception as e:
                if self.running:
                    print(f"[discovery] Broadcast error: {e}")
            
            time.sleep(HEARTBEAT_INTERVAL)
    
    def stop(self):
        """Stop broadcasting"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        print("[discovery] Stopped broadcasting")


class DiscoveryClient:
    """Listens for server heartbeats on LAN"""
    
    def __init__(self):
        self.running = False
        self.socket = None
        self.listen_thread = None
        self.servers = {}  # {ip: (name, port, last_seen_time)}
        self.servers_lock = threading.Lock()
        self.server_timeout = 5.0  # Remove servers not seen for this many seconds
        
    def start(self):
        """Start listening for server heartbeats"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.bind(("", DISCOVERY_PORT))
            self.socket.settimeout(0.5)  # Non-blocking with short timeout
            
            self.running = True
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            print(f"[discovery] Listening for servers on port {DISCOVERY_PORT}")
            return True
        except Exception as e:
            print(f"[discovery] Failed to start listener: {e}")
            return False
    
    def _listen_loop(self):
        """Listen for server heartbeats"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                
                # Check for valid response magic
                if not data.startswith(RESPONSE_MAGIC + b"|"):
                    continue
                
                # Parse payload: name|port
                payload = data[len(RESPONSE_MAGIC) + 1:]
                try:
                    name_str, port_str = payload.decode("utf-8").split("|", 1)
                    port = int(port_str)
                except ValueError:
                    continue
                
                server_ip = addr[0]
                
                # Update server list
                with self.servers_lock:
                    self.servers[server_ip] = (name_str, port, time.time())
                    
            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    print(f"[discovery] Listen error: {e}")
            
            # Clean up stale servers
            self._cleanup_stale_servers()
    
    def _cleanup_stale_servers(self):
        """Remove servers that haven't been seen recently"""
        current_time = time.time()
        with self.servers_lock:
            stale = [ip for ip, (_, _, last_seen) in self.servers.items()
                     if current_time - last_seen > self.server_timeout]
            for ip in stale:
                del self.servers[ip]
    
    def get_servers(self):
        """Get list of discovered servers as [(name, ip, port), ...]"""
        with self.servers_lock:
            return [(name, ip, port) for ip, (name, port, _) in self.servers.items()]
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        with self.servers_lock:
            self.servers.clear()
        print("[discovery] Stopped listening")
