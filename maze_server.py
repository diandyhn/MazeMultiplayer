from socket import *
import socket
import threading
import time
import sys
import logging
import json
import urllib.parse
from http_server import HttpServer
from maze_game import MazeGame

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Global game instance
game = MazeGame()

class MazeHttpServer(HttpServer):
    def __init__(self):
        super().__init__()
        self.game = game

    def http_get(self, object_address, headers):
        """Handle GET requests for maze game"""
        try:
            # Parse URL and parameters
            if '?' in object_address:
                path, query_string = object_address.split('?', 1)
                params = urllib.parse.parse_qs(query_string)
            else:
                path = object_address
                params = {}

            # API endpoints
            if path == '/api/status':
                return self.create_json_response({'status': 'OK', 'message': 'Maze server running'})
            
            elif path == '/api/players':
                players = list(self.game.players.keys())
                return self.create_json_response({'status': 'OK', 'players': players})
            
            elif path == '/api/player/face':
                player_id = params.get('id', [''])[0]
                if player_id and player_id in self.game.players:
                    face = self.game.players[player_id]['avatar']
                    return self.create_json_response({'status': 'OK', 'face': face})
                else:
                    return self.create_json_response({'status': 'ERROR', 'message': 'Player not found'}, 404)
            
            elif path == '/api/player/location':
                player_id = params.get('id', [''])[0]
                if player_id and player_id in self.game.player_positions:
                    pos = self.game.player_positions[player_id]
                    location = f"{pos['x']},{pos['y']}"
                    return self.create_json_response({'status': 'OK', 'location': location})
                else:
                    return self.create_json_response({'status': 'ERROR', 'message': 'Player not found'}, 404)
            
            elif path == '/api/gamestate':
                game_state = self.game.get_game_state()
                return self.create_json_response({'status': 'OK', 'game_state': game_state})
            
            else:
                # Default file serving
                return super().http_get(object_address, headers)
                
        except Exception as e:
            logging.error(f"Error in GET request: {e}")
            return self.create_json_response({'status': 'ERROR', 'message': str(e)}, 500)

    def http_post(self, object_address, headers, body):
        """Handle POST requests for maze game"""
        try:
            # Parse JSON body
            if body:
                data = json.loads(body)
            else:
                data = {}

            if object_address == '/api/player/add':
                player_id = data.get('player_id', '')
                player_name = data.get('player_name', 'Unknown')
                
                if not player_id:
                    return self.create_json_response({'status': 'ERROR', 'message': 'Player ID required'}, 400)
                
                self.game.add_player(player_id, player_name)
                return self.create_json_response({'status': 'OK', 'message': 'Player added'})
            
            elif object_address == '/api/player/move':
                player_id = data.get('player_id', '')
                x = data.get('x', 0)
                y = data.get('y', 0)
                
                if not player_id:
                    return self.create_json_response({'status': 'ERROR', 'message': 'Player ID required'}, 400)
                
                if self.game.move_player(player_id, x, y):
                    return self.create_json_response({'status': 'OK', 'message': 'Position updated'})
                else:
                    return self.create_json_response({'status': 'ERROR', 'message': 'Invalid position'}, 400)
            
            elif object_address == '/api/game/reset':
                self.game.reset_game()
                return self.create_json_response({'status': 'OK', 'message': 'Game reset'})
            
            else:
                return self.create_json_response({'status': 'ERROR', 'message': 'Unknown endpoint'}, 404)
                
        except json.JSONDecodeError:
            return self.create_json_response({'status': 'ERROR', 'message': 'Invalid JSON'}, 400)
        except Exception as e:
            logging.error(f"Error in POST request: {e}")
            return self.create_json_response({'status': 'ERROR', 'message': str(e)}, 500)

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        maze_server = MazeHttpServer()
        
        try:
            while True:
                data = self.connection.recv(1024)
                if data:
                    d = data.decode()
                    rcv = rcv + d
                    
                    # Check if we have complete HTTP request
                    if "\r\n\r\n" in rcv:
                        logging.warning("Request from client: {}".format(rcv.split('\r\n')[0]))
                        hasil = maze_server.proses(rcv)
                        logging.warning("Response sent to client")
                        self.connection.sendall(hasil)
                        rcv = ""
                        break
                else:
                    break
        except Exception as e:
            logging.warning(f"Client error: {e}")
        finally:
            self.connection.close()

class MazeServer(threading.Thread):
    def __init__(self, port=55556):
        self.port = port
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.my_socket.bind(('0.0.0.0', self.port))
            self.my_socket.listen(10)
            logging.warning(f"Maze HTTP server started on port {self.port}")
            print(f"Maze HTTP Server running on port {self.port}")
            print("Game endpoints available:")
            print(f"   GET  http://localhost:{self.port}/api/status")
            print(f"   GET  http://localhost:{self.port}/api/gamestate")
            print(f"   POST http://localhost:{self.port}/api/player/add")
            print(f"   POST http://localhost:{self.port}/api/player/move")
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"ERROR: Port {self.port} is already in use!")
                print("\nSolutions:")
                print(f"1. Kill existing server: sudo lsof -i :{self.port}")
                print("2. Wait a few minutes and try again")
                print("3. Use different port")
                return
            else:
                print(f"Server error: {e}")
                return
        
        while True:
            try:
                self.connection, self.client_address = self.my_socket.accept()
                logging.warning("Connection from {}".format(self.client_address))
                
                clt = ProcessTheClient(self.connection, self.client_address)
                clt.start()
                self.the_clients.append(clt)
            except Exception as e:
                logging.warning(f"Accept error: {e}")

def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 55556
        
    print("=" * 60)
    print("    🎮 MAZE GAME SERVER")
    print("=" * 60)
    
    svr = MazeServer(port)
    svr.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning("Server shutting down...")
        print("\n👋 Server shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
