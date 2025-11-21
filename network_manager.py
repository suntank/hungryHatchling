"""
Network Manager for LAN Multiplayer
Handles host-client connections for up to 4 players
"""

import socket
import threading
import json
import time
from enum import Enum

class NetworkRole(Enum):
    """Role in the network game"""
    NONE = 0
    HOST = 1
    CLIENT = 2

class NetworkManager:
    """Manages network connections for LAN multiplayer"""
    
    def __init__(self):
        self.role = NetworkRole.NONE
        self.socket = None
        self.clients = []  # List of client sockets (host only)
        self.client_addresses = []  # List of client addresses for display
        self.host_address = None  # Host IP:Port (client only)
        self.running = False
        self.receive_thread = None
        self.message_queue = []  # Incoming messages
        self.connected = False
        
        # Network settings
        self.port = 5555  # Default port for game
        self.buffer_size = 4096
        
    def start_host(self, max_players=4):
        """Start hosting a game (server mode)"""
        try:
            self.role = NetworkRole.HOST
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to all available interfaces
            host_ip = self.get_local_ip()
            self.socket.bind((host_ip, self.port))
            self.socket.listen(max_players - 1)  # Host is player 1
            self.socket.settimeout(1.0)  # Non-blocking with timeout
            
            self.running = True
            self.connected = True
            
            # Start accepting connections in background
            self.receive_thread = threading.Thread(target=self._accept_clients_loop, daemon=True)
            self.receive_thread.start()
            
            print(f"Host started on {host_ip}:{self.port}")
            return True, host_ip
            
        except Exception as e:
            print(f"Failed to start host: {e}")
            self.cleanup()
            return False, str(e)
    
    def connect_to_host(self, host_ip):
        """Connect to a host as a client"""
        try:
            self.role = NetworkRole.CLIENT
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout for connection
            
            self.socket.connect((host_ip, self.port))
            self.host_address = f"{host_ip}:{self.port}"
            self.socket.settimeout(None)  # Remove timeout after connection
            
            self.running = True
            self.connected = True
            
            # Start receiving messages
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            print(f"Connected to host at {host_ip}:{self.port}")
            return True, None
            
        except Exception as e:
            print(f"Failed to connect to host: {e}")
            self.cleanup()
            return False, str(e)
    
    def _accept_clients_loop(self):
        """Background thread to accept incoming client connections (host only)"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                client_socket.setblocking(False)  # Non-blocking mode
                
                self.clients.append(client_socket)
                self.client_addresses.append(f"{address[0]}:{address[1]}")
                
                print(f"Client connected from {address}")
                
                # Notify about new player
                self.message_queue.append({
                    'type': 'player_joined',
                    'player_id': len(self.clients),  # Client IDs start at 1
                    'address': f"{address[0]}:{address[1]}"
                })
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting client: {e}")
    
    def _receive_loop(self):
        """Background thread to receive messages (client only)"""
        while self.running:
            try:
                data = self.socket.recv(self.buffer_size)
                if not data:
                    print("Connection closed by host")
                    self.connected = False
                    break
                
                # Decode and queue message
                message = json.loads(data.decode('utf-8'))
                self.message_queue.append(message)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error receiving data: {e}")
                    self.connected = False
                break
    
    def send_to_host(self, message):
        """Send a message to the host (client only)"""
        if self.role != NetworkRole.CLIENT or not self.connected:
            return False
        
        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.sendall(data)
            return True
        except Exception as e:
            print(f"Error sending to host: {e}")
            self.connected = False
            return False
    
    def send_to_client(self, client_id, message):
        """Send a message to a specific client (host only)"""
        if self.role != NetworkRole.HOST or client_id >= len(self.clients):
            return False
        
        try:
            data = json.dumps(message).encode('utf-8')
            self.clients[client_id].sendall(data)
            return True
        except Exception as e:
            print(f"Error sending to client {client_id}: {e}")
            # Remove disconnected client
            self._remove_client(client_id)
            return False
    
    def broadcast_to_clients(self, message):
        """Send a message to all connected clients (host only)"""
        if self.role != NetworkRole.HOST:
            return
        
        data = json.dumps(message).encode('utf-8')
        disconnected = []
        
        for i, client in enumerate(self.clients):
            try:
                client.sendall(data)
            except Exception as e:
                print(f"Error broadcasting to client {i}: {e}")
                disconnected.append(i)
        
        # Remove disconnected clients
        for client_id in reversed(disconnected):
            self._remove_client(client_id)
    
    def _remove_client(self, client_id):
        """Remove a disconnected client"""
        if client_id < len(self.clients):
            try:
                self.clients[client_id].close()
            except:
                pass
            
            del self.clients[client_id]
            del self.client_addresses[client_id]
            
            self.message_queue.append({
                'type': 'player_left',
                'player_id': client_id + 1
            })
    
    def get_messages(self):
        """Get all queued messages and clear the queue"""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages
    
    def get_connected_players(self):
        """Get number of connected players (including host)"""
        if self.role == NetworkRole.HOST:
            return len(self.clients) + 1  # +1 for host
        elif self.role == NetworkRole.CLIENT:
            return -1  # Client doesn't know total
        return 0
    
    def get_local_ip(self):
        """Get the local IP address for LAN"""
        try:
            # Create a temporary socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def cleanup(self):
        """Clean up network resources"""
        self.running = False
        self.connected = False
        
        # Close client connections (host)
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close main socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.clients.clear()
        self.client_addresses.clear()
        self.message_queue.clear()
        self.role = NetworkRole.NONE
        
        print("Network cleaned up")
    
    def is_host(self):
        """Check if this instance is the host"""
        return self.role == NetworkRole.HOST
    
    def is_client(self):
        """Check if this instance is a client"""
        return self.role == NetworkRole.CLIENT
    
    def is_connected(self):
        """Check if connected to network game"""
        return self.connected
