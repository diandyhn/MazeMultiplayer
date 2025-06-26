# maze_server.py
from socket import *
import socket
import threading
import time
import sys
import logging
import json
import base64
import random
from io import BytesIO
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(level=logging.WARNING)

class MazeGame:
    def __init__(self):
        # Maze dimensions (must be odd numbers for proper maze generation)
        self.maze_width = 21
        self.maze_height = 15
        self.cell_size = 30
        
        # Game state
        self.players = {}
        self.player_positions = {}
        self.game_started = False
        self.winner = None
        
        # Generate maze
        self.maze = self.generate_maze()
        self.start_pos = (1, 1)  # Top-left corner
        self.end_pos = (self.maze_width-2, self.maze_height-2)  # Bottom-right corner
        
        # Player colors for avatar generation
        self.player_colors = [
            (255, 100, 100),  # Red
            (100, 255, 100),  # Green  
            (100, 100, 255),  # Blue
            (255, 255, 100),  # Yellow
            (255, 100, 255),  # Magenta
            (100, 255, 255),  # Cyan
        ]

    def generate_maze(self):
        """Generate a random maze using recursive backtracking"""
        # Initialize maze with all walls
        maze = [[1 for _ in range(self.maze_width)] for _ in range(self.maze_height)]
        
        def carve_path(x, y):
            maze[y][x] = 0  # Mark as path
            
            # Randomize directions
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 < nx < self.maze_width-1 and 0 < ny < self.maze_height-1 and 
                    maze[ny][nx] == 1):
                    # Carve wall between current and next cell
                    maze[y + dy//2][x + dx//2] = 0
                    carve_path(nx, ny)
        
        # Start carving from (1,1)
        carve_path(1, 1)
        
        # Ensure start and end are clear
        maze[1][1] = 0
        maze[self.maze_height-2][self.maze_width-2] = 0
        
        return maze

    def add_player(self, player_id):
        """Add a new player to the game"""
        if player_id not in self.players:
            color_index = len(self.players) % len(self.player_colors)
            self.players[player_id] = {
                'color': self.player_colors[color_index],
                'avatar': self.generate_player_avatar(self.player_colors[color_index])
            }
            # Place player at start position
            self.player_positions[player_id] = {
                'x': self.start_pos[0] * self.cell_size,
                'y': self.start_pos[1] * self.cell_size
            }
            logging.warning(f"Player {player_id} added to game")

    def generate_player_avatar(self, color):
        """Generate a simple circular avatar for the player"""
        size = 24
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw circle
        draw.ellipse([2, 2, size-2, size-2], fill=color, outline=(0, 0, 0), width=2)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str

    def is_valid_position(self, x, y):
        """Check if position is valid (not in a wall)"""
        # Convert pixel coordinates to maze coordinates
        maze_x = x // self.cell_size
        maze_y = y // self.cell_size
        
        # Check bounds
        if (maze_x < 0 or maze_x >= self.maze_width or 
            maze_y < 0 or maze_y >= self.maze_height):
            return False
            
        # Check if it's a wall
        return self.maze[maze_y][maze_x] == 0

    def move_player(self, player_id, new_x, new_y):
        """Move player if the new position is valid"""
        if player_id not in self.player_positions:
            return False
            
        if self.is_valid_position(new_x, new_y):
            self.player_positions[player_id]['x'] = new_x
            self.player_positions[player_id]['y'] = new_y
            
            # Check win condition
            maze_x = new_x // self.cell_size
            maze_y = new_y // self.cell_size
            if (maze_x, maze_y) == self.end_pos and not self.winner:
                self.winner = player_id
                logging.warning(f"Player {player_id} won the game!")
            
            return True
        return False

    def get_game_state(self):
        """Get current game state for clients"""
        return {
            'maze': self.maze,
            'maze_width': self.maze_width,
            'maze_height': self.maze_height,
            'cell_size': self.cell_size,
            'players': self.player_positions,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'winner': self.winner
        }

# Global game instance
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
                game.add_player(player_id)
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
                # Reset game state
                game.winner = None
                game.maze = game.generate_maze()
                for player_id in game.player_positions:
                    game.player_positions[player_id] = {
                        'x': game.start_pos[0] * game.cell_size,
                        'y': game.start_pos[1] * game.cell_size
                    }
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
            logging.warning("✅ Maze game server started successfully on port 55556")
            print("✅ Server is running on port 55556")
            print("🎮 Players can now connect!")
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