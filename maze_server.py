from socket import *
import socket
import threading
import time
import sys
import logging
import json
from maze_game import MazeGame

game = MazeGame()

class GameServer:
    def __init__(self):
        pass

    def proses(self, data):
        """Process client commands"""
        try:
            command_parts = data.strip().split()
            command = command_parts[0]
            
            response = {'status': 'ERROR', 'message': 'Unknown command'}
            
            if command == 'add_player':
                player_id = command_parts[1]
                player_name = command_parts[2] if len(command_parts) > 2 else "Unknown"
                # Handle names with spaces (join remaining parts)
                if len(command_parts) > 3:
                    player_name = ' '.join(command_parts[2:])
                game.add_player(player_id, player_name)
                response = {'status': 'OK', 'message': 'Player added'}
                
            elif command == 'get_players_face':
                player_id = command_parts[1]
                if player_id in game.players:
                    response = {
                        'status': 'OK', 
                        'face': game.players[player_id]['avatar']
                    }
                else:
                    response = {'status': 'ERROR', 'message': 'Player not found'}
                    
            elif command == 'get_all_players':
                response = {
                    'status': 'OK',
                    'players': list(game.players.keys())
                }
                
            elif command == 'set_location':
                player_id = command_parts[1]
                x = int(command_parts[2])
                y = int(command_parts[3])
                
                if game.move_player(player_id, x, y):
                    response = {'status': 'OK', 'message': 'Position updated'}
                else:
                    response = {'status': 'ERROR', 'message': 'Invalid position'}
                    
            elif command == 'get_location':
                player_id = command_parts[1]
                if player_id in game.player_positions:
                    pos = game.player_positions[player_id]
                    response = {
                        'status': 'OK',
                        'location': f"{pos['x']},{pos['y']}"
                    }
                else:
                    response = {'status': 'ERROR', 'message': 'Player not found'}
                    
            elif command == 'get_game_state':
                response = {
                    'status': 'OK',
                    'game_state': game.get_game_state()
                }
                
            elif command == 'reset_game':
                game.reset_game()
                response = {'status': 'OK', 'message': 'Game reset'}
            
            return json.dumps(response).encode()
            
        except Exception as e:
            logging.error(f"Error processing command: {e}")
            response = {'status': 'ERROR', 'message': str(e)}
            return json.dumps(response).encode()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        game_server = GameServer()
        
        while True:
            try:
                data = self.connection.recv(32)
                if data:
                    d = data.decode()
                    rcv = rcv + d
                    if rcv[-2:] == '\r\n':
                        logging.warning("Data from client: {}".format(rcv.strip()))
                        hasil = game_server.proses(rcv.strip())
                        hasil = hasil + "\r\n\r\n".encode()
                        logging.warning("Response to client: {}".format(hasil))
                        self.connection.sendall(hasil)
                        rcv = ""
                        self.connection.close()
                        break
                else:
                    break
            except OSError as e:
                logging.warning(f"OSError: {e}")
                pass
        self.connection.close()

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.my_socket.bind(('0.0.0.0', 55556))
            self.my_socket.listen(10)
            logging.warning("✅ Enhanced Maze game server started successfully on port 55556")
            print("✅ Enhanced Server is running on port 55556")
            print("🎮 Players can now connect!")
            print("🌟 New features: Player names, scores, collectibles, and enhanced UI!")
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print("❌ ERROR: Port 55556 is already in use!")
                print("\n🔧 Solutions:")
                print("1. Kill existing server: sudo lsof -i :55556")
                print("2. Wait a few minutes and try again")
                print("3. Restart your computer")
                return
            else:
                print(f"❌ Server error: {e}")
                return
        
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning("Connection from {}".format(self.client_address))
            
            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    svr = Server()
    svr.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning("Server shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()