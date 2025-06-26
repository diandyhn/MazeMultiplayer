# maze_client.py
import pygame
import sys
import io
import socket
import logging
import json
import base64

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape The Maze - Multiplayer")

clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_GRAY = (64, 64, 64)

class ClientInterface:
    def __init__(self, player_id='1'):
        self.player_id = player_id
        self.server_address = ('127.0.0.1', 55556)  # Use IP address instead of localhost

    def send_command(self, command_str=""):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # Add timeout
        try:
            sock.connect(self.server_address)
            
            sock.sendall((command_str + '\r\n').encode())
            
            data_received = ""
            sock.settimeout(2.0)  # Shorter timeout for receiving
            while True:
                data = sock.recv(1024)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            
            # Remove the trailing \r\n\r\n
            data_received = data_received.replace('\r\n\r\n', '')
            if data_received.strip():
                hasil = json.loads(data_received)
                return hasil
            else:
                return {'status': 'ERROR', 'message': 'Empty response'}
            
        except socket.timeout:
            return {'status': 'ERROR', 'message': 'Connection timeout'}
        except ConnectionRefusedError:
            return {'status': 'ERROR', 'message': 'Server not running'}
        except Exception as e:
            return {'status': 'ERROR', 'message': str(e)}
        finally:
            sock.close()

    def add_player(self):
        command_str = f"add_player {self.player_id}"
        return self.send_command(command_str)

    def get_players_face(self):
        command_str = f"get_players_face {self.player_id}"
        hasil = self.send_command(command_str)
        if hasil['status'] == 'OK':
            return hasil['face']
        return None

    def get_all_players(self):
        command_str = "get_all_players"
        hasil = self.send_command(command_str)
        if hasil['status'] == 'OK':
            return hasil['players']
        return []

    def set_location(self, x, y):
        command_str = f"set_location {self.player_id} {x} {y}"
        hasil = self.send_command(command_str)
        return hasil['status'] == 'OK'

    def get_location(self, player_id=None):
        if player_id is None:
            player_id = self.player_id
        command_str = f"get_location {player_id}"
        hasil = self.send_command(command_str)
        if hasil['status'] == 'OK':
            location = hasil['location'].split(',')
            return (int(location[0]), int(location[1]))
        return None

    def get_game_state(self):
        command_str = "get_game_state"
        hasil = self.send_command(command_str)
        if hasil['status'] == 'OK':
            return hasil['game_state']
        return None

    def reset_game(self):
        command_str = "reset_game"
        return self.send_command(command_str)

class MazeRenderer:
    def __init__(self, game_state):
        self.maze = game_state['maze']
        self.maze_width = game_state['maze_width']
        self.maze_height = game_state['maze_height']
        self.cell_size = game_state['cell_size']
        self.start_pos = game_state['start_pos']
        self.end_pos = game_state['end_pos']

    def draw_maze(self, surface):
        """Draw the maze on the given surface"""
        for y in range(self.maze_height):
            for x in range(self.maze_width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, 
                                 self.cell_size, self.cell_size)
                
                if self.maze[y][x] == 1:  # Wall
                    pygame.draw.rect(surface, DARK_GRAY, rect)
                    pygame.draw.rect(surface, BLACK, rect, 1)
                else:  # Path
                    pygame.draw.rect(surface, WHITE, rect)
                    pygame.draw.rect(surface, GRAY, rect, 1)

        # Draw start position
        start_rect = pygame.Rect(self.start_pos[0] * self.cell_size + 2, 
                               self.start_pos[1] * self.cell_size + 2,
                               self.cell_size - 4, self.cell_size - 4)
        pygame.draw.rect(surface, GREEN, start_rect)

        # Draw end position
        end_rect = pygame.Rect(self.end_pos[0] * self.cell_size + 2, 
                             self.end_pos[1] * self.cell_size + 2,
                             self.cell_size - 4, self.cell_size - 4)
        pygame.draw.rect(surface, RED, end_rect)

class Player:
    def __init__(self, player_id, is_local=False):
        self.player_id = player_id
        self.is_local = is_local
        self.x = 30  # Default position
        self.y = 30
        self.speed = 5
        self.client_interface = ClientInterface(player_id)
        
        # Get player avatar from server
        face_data = None
        try:
            if is_local:
                result = self.client_interface.add_player()
                if result['status'] != 'OK':
                    print(f"Warning: Could not add player to server: {result['message']}")
            
            face_data = self.client_interface.get_players_face()
        except Exception as e:
            print(f"Warning: Could not get player avatar: {e}")
        
        if face_data:
            try:
                self.image = pygame.image.load(io.BytesIO(base64.b64decode(face_data)))
            except Exception as e:
                print(f"Warning: Could not decode avatar image: {e}")
                self.image = self.create_default_image()
        else:
            self.image = self.create_default_image()

    def create_default_image(self):
        """Create a simple default player image"""
        image = pygame.Surface((24, 24))
        color = BLUE if self.is_local else RED
        image.fill(color)
        pygame.draw.circle(image, WHITE, (12, 12), 10)
        pygame.draw.circle(image, color, (12, 12), 8)
        return image

    def move(self, keys, maze_renderer):
        """Move player based on input (only for local player)"""
        if not self.is_local:
            # Get position from server for remote players
            pos = self.client_interface.get_location()
            if pos:
                self.x, self.y = pos
            return

        # Handle local player movement
        new_x, new_y = self.x, self.y

        if keys[pygame.K_UP]:
            new_y -= self.speed
        elif keys[pygame.K_DOWN]:
            new_y += self.speed
        elif keys[pygame.K_LEFT]:
            new_x -= self.speed
        elif keys[pygame.K_RIGHT]:
            new_x += self.speed

        # Check if new position is valid by testing with server
        if new_x != self.x or new_y != self.y:
            if self.client_interface.set_location(new_x, new_y):
                self.x, self.y = new_x, new_y

    def draw(self, surface):
        """Draw the player on the surface"""
        surface.blit(self.image, (self.x, self.y))

class Game:
    def __init__(self, player_id):
        self.player_id = player_id
        self.client_interface = ClientInterface(player_id)
        self.current_player = None
        self.other_players = {}
        self.maze_renderer = None
        self.winner = None
        self.font = pygame.font.Font(None, 36)
        self.connection_error = None
        
        # Test connection and initialize
        if not self.initialize_game():
            return

    def initialize_game(self):
        """Initialize game state and test server connection"""
        try:
            # Add player to server
            result = self.client_interface.add_player()
            if result['status'] == 'ERROR':
                self.connection_error = f"Failed to add player: {result['message']}"
                return False
            
            # Create local player
            self.current_player = Player(self.player_id, is_local=True)
            
            # Get initial game state
            if not self.update_game_state():
                self.connection_error = "Failed to get game state from server"
                return False
                
            return True
            
        except Exception as e:
            self.connection_error = f"Game initialization error: {e}"
            return False

    def update_game_state(self):
        """Update game state from server"""
        try:
            game_state = self.client_interface.get_game_state()
            if not game_state or game_state.get('status') == 'ERROR':
                return False
                
            self.maze_renderer = MazeRenderer(game_state)
            
            # Update other players
            all_players = self.client_interface.get_all_players()
            if all_players:
                for player_id in all_players:
                    if player_id != self.player_id and player_id not in self.other_players:
                        self.other_players[player_id] = Player(player_id, is_local=False)
            
            # Check for winner
            self.winner = game_state.get('winner')
            return True
            
        except Exception as e:
            logging.warning(f"Failed to update game state: {e}")
            return False

    def draw_ui(self, surface):
        """Draw game UI elements"""
        # Draw instructions
        if not self.winner:
            text1 = self.font.render("Use arrow keys to move", True, BLACK)
            text2 = self.font.render("Reach the RED square to win!", True, BLACK)
            text3 = self.font.render("Press R to reset game", True, BLACK)
            
            surface.blit(text1, (WIDTH - 300, 10))
            surface.blit(text2, (WIDTH - 300, 50))
            surface.blit(text3, (WIDTH - 300, 90))
        else:
            # Draw winner message
            if self.winner == self.player_id:
                win_text = "YOU WON!"
                color = GREEN
            else:
                win_text = f"Player {self.winner} Won!"
                color = RED
                
            text = self.font.render(win_text, True, color)
            text_rect = text.get_rect(center=(WIDTH//2, 50))
            surface.blit(text, text_rect)
            
            reset_text = self.font.render("Press R to play again", True, BLACK)
            reset_rect = reset_text.get_rect(center=(WIDTH//2, 100))
            surface.blit(reset_text, reset_rect)

    def handle_reset(self):
        """Reset the game"""
        self.client_interface.reset_game()
        self.winner = None
        self.update_game_state()

    def run(self):
        """Main game loop"""
        if self.connection_error:
            print(f"❌ Cannot start game: {self.connection_error}")
            return
            
        running = True
        last_update = 0
        
        print("🎮 Game window should open now...")
        
        while running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.handle_reset()

            # Get pressed keys
            keys = pygame.key.get_pressed()

            # Update game state periodically (every 1000ms instead of 500ms to reduce spam)
            if current_time - last_update > 1000:
                self.update_game_state()
                last_update = current_time

            # Move players
            if self.maze_renderer and self.current_player and not self.winner:
                self.current_player.move(keys, self.maze_renderer)
                for player in self.other_players.values():
                    player.move(keys, self.maze_renderer)

            # Draw everything
            screen.fill(WHITE)
            
            if self.maze_renderer:
                self.maze_renderer.draw_maze(screen)
                
            # Draw players
            if self.current_player:
                self.current_player.draw(screen)
            for player in self.other_players.values():
                player.draw(screen)

            # Draw UI
            self.draw_ui(screen)

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

def main():
    print("=" * 50)
    print("    ESCAPE THE MAZE - Multiplayer Game")
    print("=" * 50)
    print("Instructions:")
    print("1. Use arrow keys to move your character")
    print("2. Navigate through the maze to reach the red exit")
    print("3. First player to reach the exit wins!")
    print("4. Press R to reset the game")
    print("=" * 50)
    
    player_number = input("Enter your player ID (1-6): ").strip()
    
    if not player_number:
        player_number = "1"
    
    # Test server connection first
    print(f"Testing connection to server...")
    test_client = ClientInterface(player_number)
    test_result = test_client.send_command("get_all_players")
    
    if test_result['status'] == 'ERROR':
        print(f"❌ Cannot connect to server: {test_result['message']}")
        print("\n🔧 Make sure:")
        print("1. Server is running: python maze_server.py")
        print("2. Server is on the correct port (55556)")
        print("3. No firewall is blocking the connection")
        input("\nPress Enter to exit...")
        return
    
    print("✅ Server connection successful!")
    print("🎮 Starting game...")
    
    try:
        # Initialize pygame display
        import os
        os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'  # Position window
        
        game = Game(player_number)
        game.run()
    except Exception as e:
        print(f"❌ Error starting game: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have a display/desktop environment")
        print("2. Try: export DISPLAY=:0 (if using SSH)")
        print("3. Install pygame properly: pip install pygame")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()