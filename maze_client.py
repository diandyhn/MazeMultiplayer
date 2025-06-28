import pygame
import sys
import io
import socket
import logging
import json
import base64
import math
import random
import string

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 1024, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎮 Escape The Maze - Enhanced Multiplayer")

clock = pygame.time.Clock()
FPS = 60

# Enhanced Colors
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'GRAY': (128, 128, 128),
    'LIGHT_GRAY': (200, 200, 200),
    'DARK_GRAY': (64, 64, 64),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'ORANGE': (255, 165, 0),
    'PURPLE': (128, 0, 128),
    'CYAN': (0, 255, 255),
    'MAGENTA': (255, 0, 255),
    'GOLD': (255, 215, 0),
    'SILVER': (192, 192, 192),
    'LIME': (50, 205, 50),
    'PINK': (255, 192, 203),
    'NAVY': (0, 0, 128),
    'MAROON': (128, 0, 0),
    'OLIVE': (128, 128, 0),
    'TEAL': (0, 128, 128),
    'CORAL': (255, 127, 80),
    'SALMON': (250, 128, 114),
    'VIOLET': (238, 130, 238),
    'INDIGO': (75, 0, 130),
    'TURQUOISE': (64, 224, 208),
    'MINT': (152, 251, 152),
    'LAVENDER': (230, 230, 250),
    'PEACH': (255, 218, 185),
    'SKYBLUE': (135, 206, 235),
    'FORESTGREEN': (34, 139, 34),
    'CRIMSON': (220, 20, 60),
    'DARKBLUE': (0, 0, 139),
    'LIMEGREEN': (50, 205, 50),
    'HOTPINK': (255, 105, 180),
    'SEAGREEN': (46, 139, 87),
    'DARKORANGE': (255, 140, 0),
    'ROYALBLUE': (65, 105, 225),
    'MEDIUMORCHID': (186, 85, 211),
    'SPRINGGREEN': (0, 255, 127),
    'DEEPPINK': (255, 20, 147),
    'DODGERBLUE': (30, 144, 255),
    'LIGHTSALMON': (255, 160, 122),
    'MEDIUMSEAGREEN': (60, 179, 113),
    'BACKGROUND': (20, 20, 30),
    'UI_BACKGROUND': (40, 40, 60),
    'UI_BORDER': (100, 100, 120),
    'TEXT_PRIMARY': (255, 255, 255),
    'TEXT_SECONDARY': (200, 200, 200),
    'SUCCESS': (46, 204, 113),
    'WARNING': (241, 196, 15),
    'ERROR': (231, 76, 60),
    'INFO': (52, 152, 219)
}

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particle(self, x, y, color, velocity=(0, 0), lifetime=60):
        self.particles.append({
            'x': x,
            'y': y,
            'vx': velocity[0] + random.uniform(-2, 2),
            'vy': velocity[1] + random.uniform(-2, 2),
            'color': color,
            'lifetime': lifetime,
            'max_lifetime': lifetime,
            'size': random.uniform(2, 4)
        })
    
    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # Gravity
            particle['lifetime'] -= 1
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, surface):
        for particle in self.particles:
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            color = (*particle['color'][:3], alpha)
            size = int(particle['size'] * (particle['lifetime'] / particle['max_lifetime']))
            if size > 0:
                pygame.draw.circle(surface, particle['color'][:3], 
                                 (int(particle['x']), int(particle['y'])), size)

class ClientInterface:
    def __init__(self, player_id='1', player_name='Player'):
        self.player_id = player_id
        self.player_name = player_name
        self.server_address = ('localhost', 55556)

    def send_command(self, command_str=""):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        try:
            sock.connect(self.server_address)
            sock.sendall((command_str + '\r\n').encode())
            
            data_received = ""
            sock.settimeout(2.0)
            while True:
                data = sock.recv(1024)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            
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
        command_str = f"add_player {self.player_id} {self.player_name}"
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
        self.collectibles = game_state.get('collectibles', [])
        self.animation_offset = 0

    def draw_maze(self, surface):
        """Draw the enhanced maze with visual effects"""
        self.animation_offset += 0.1
        
        for y in range(self.maze_height):
            for x in range(self.maze_width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, 
                                 self.cell_size, self.cell_size)
                
                if self.maze[y][x] == 1:  # Wall
                    # Gradient effect for walls
                    base_color = COLORS['DARK_GRAY']
                    highlight = tuple(min(255, c + 20) for c in base_color)
                    
                    pygame.draw.rect(surface, base_color, rect)
                    pygame.draw.rect(surface, highlight, 
                                   (rect.x, rect.y, rect.width, 3))
                    pygame.draw.rect(surface, COLORS['BLACK'], rect, 1)
                else:  # Path
                    # Subtle pattern for paths
                    pygame.draw.rect(surface, COLORS['WHITE'], rect)
                    if (x + y) % 2 == 0:
                        pygame.draw.rect(surface, COLORS['LIGHT_GRAY'], rect)
                    pygame.draw.rect(surface, COLORS['GRAY'], rect, 1)

        # Draw animated start position
        start_rect = pygame.Rect(self.start_pos[0] * self.cell_size + 2, 
                               self.start_pos[1] * self.cell_size + 2,
                               self.cell_size - 4, self.cell_size - 4)
        
        # Pulsing effect
        pulse = abs(math.sin(self.animation_offset * 2)) * 50
        green_color = (0, 255 - int(pulse), 0)
        pygame.draw.rect(surface, green_color, start_rect)
        pygame.draw.rect(surface, COLORS['WHITE'], start_rect, 2)

        # Draw animated end position
        end_rect = pygame.Rect(self.end_pos[0] * self.cell_size + 2, 
                             self.end_pos[1] * self.cell_size + 2,
                             self.cell_size - 4, self.cell_size - 4)
        
        # Glowing effect
        glow = abs(math.sin(self.animation_offset * 3)) * 100
        red_color = (255, int(glow), int(glow))
        pygame.draw.rect(surface, red_color, end_rect)
        pygame.draw.rect(surface, COLORS['YELLOW'], end_rect, 2)

        # Draw collectibles
        self.draw_collectibles(surface)

    def draw_collectibles(self, surface):
        """Draw animated collectibles"""
        for collectible in self.collectibles:
            if collectible['collected']:
                continue
                
            x = collectible['x'] * self.cell_size + self.cell_size // 2
            y = collectible['y'] * self.cell_size + self.cell_size // 2
            
            # Animation based on type
            if collectible['type'] == 'coin':
                # Spinning coin
                radius = 8 + int(abs(math.sin(self.animation_offset * 4)) * 3)
                pygame.draw.circle(surface, COLORS['GOLD'], (x, y), radius)
                pygame.draw.circle(surface, COLORS['YELLOW'], (x, y), radius - 2)
                pygame.draw.circle(surface, COLORS['GOLD'], (x, y), radius - 4)
                
            elif collectible['type'] == 'gem':
                # Twinkling gem
                size = 6 + int(abs(math.sin(self.animation_offset * 5)) * 2)
                points = [
                    (x, y - size),
                    (x + size//2, y - size//2),
                    (x + size, y),
                    (x + size//2, y + size//2),
                    (x, y + size),
                    (x - size//2, y + size//2),
                    (x - size, y),
                    (x - size//2, y - size//2)
                ]
                pygame.draw.polygon(surface, COLORS['CYAN'], points)
                pygame.draw.polygon(surface, COLORS['WHITE'], points, 2)
                
            elif collectible['type'] == 'star':
                # Rotating star
                angle = self.animation_offset * 2
                star_points = []
                for i in range(10):
                    radius = 10 if i % 2 == 0 else 5
                    point_angle = angle + (i * math.pi / 5)
                    px = x + radius * math.cos(point_angle)
                    py = y + radius * math.sin(point_angle)
                    star_points.append((px, py))
                
                pygame.draw.polygon(surface, COLORS['YELLOW'], star_points)
                pygame.draw.polygon(surface, COLORS['ORANGE'], star_points, 2)

class Player:
    def __init__(self, player_id, player_name="Player", is_local=False):
        self.player_id = player_id
        self.player_name = player_name
        self.is_local = is_local
        self.x = 30
        self.y = 30
        self.speed = 5
        self.client_interface = ClientInterface(player_id, player_name)
        self.trail = []  # For movement trail effect
        self.last_move_time = 0
        
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
        """Create a default player image with better graphics"""
        image = pygame.Surface((28, 28), pygame.SRCALPHA)
        color = COLORS['BLUE'] if self.is_local else COLORS['RED']
        
        # Draw player with glow effect
        pygame.draw.circle(image, (*color, 100), (14, 14), 16)
        pygame.draw.circle(image, color, (14, 14), 12)
        pygame.draw.circle(image, COLORS['WHITE'], (14, 14), 12, 2)
        
        # Add highlight
        highlight_color = tuple(min(255, c + 60) for c in color)
        pygame.draw.circle(image, highlight_color, (10, 10), 4)
        
        return image

    def move(self, keys, maze_renderer, particle_system):
        """Process player movement input"""
        if not self.is_local:
            pos = self.client_interface.get_location()
            if pos:
                old_x, old_y = self.x, self.y
                self.x, self.y = pos

                if old_x != self.x or old_y != self.y:
                    self.add_trail_particle(old_x + 14, old_y + 14, particle_system)
            return
        
        # Handle player movement
        new_x, new_y = self.x, self.y
        moved = False

        # Check x-direction (left/right)
        proposed_x = new_x
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            proposed_x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            proposed_x += self.speed

        # Send x movement separately to server to test if it's valid
        if proposed_x != self.x:
            if self.client_interface.set_location(proposed_x, self.y):
                self.add_trail_particle(self.x + 14, self.y + 14, particle_system)
                self.x = proposed_x
                moved = True

        # Check y-direction (up/down)
        proposed_y = new_y
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            proposed_y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            proposed_y += self.speed

        if proposed_y != self.y:
            if self.client_interface.set_location(self.x, proposed_y):
                self.add_trail_particle(self.x + 14, self.y + 14, particle_system)
                self.y = proposed_y
                moved = True

        if moved:
            self.last_move_time = pygame.time.get_ticks()

    def add_trail_particle(self, x, y, particle_system):
        """Add trail particle effect"""
        color = COLORS['BLUE'] if self.is_local else COLORS['RED']
        particle_system.add_particle(x, y, color, (0, 0), 30)

    def draw(self, surface):
        """Draw the player with enhanced effects"""
        # Draw glow effect
        glow_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
        color = COLORS['BLUE'] if self.is_local else COLORS['RED']
        pygame.draw.circle(glow_surface, (*color, 50), (20, 20), 20)
        surface.blit(glow_surface, (self.x - 6, self.y - 6))
        
        # Draw main player
        surface.blit(self.image, (self.x, self.y))
        
        # Draw name above player
        font = pygame.font.Font(None, 16)
        name_text = font.render(self.player_name, True, COLORS['WHITE'])
        name_rect = name_text.get_rect(center=(self.x + 14, self.y - 10))
        
        # Draw text background
        bg_rect = name_rect.inflate(4, 2)
        pygame.draw.rect(surface, COLORS['BLACK'], bg_rect)
        pygame.draw.rect(surface, color, bg_rect, 1)
        surface.blit(name_text, name_rect)

class Game:
    def __init__(self):
        self.player_id = self.generate_unique_id()
        self.player_name = self.input_player_name()

        self.client_interface = ClientInterface(self.player_id, self.player_name)
        self.current_player = None
        self.other_players = {}
        self.maze_renderer = None
        self.winner = None
        self.game_state = None
        self.particle_system = ParticleSystem()

        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        self.connection_error = None
        self.ui_animations = {'score_pulse': 0, 'winner_glow': 0}

        if not self.initialize_game():
            return

    def generate_unique_id(self, length=8, max_attempts=10):
        """Generate a unique ID that is not used in the game yet."""
        # Get existing player IDs from the server
        try:
            client = ClientInterface()
            existing_ids = client.get_all_players()
        except Exception as e:
            print(f"Failed to get existing IDs: {e}")
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

        # Generate a unique ID
        for _ in range(max_attempts):
            candidate_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
            if candidate_id not in existing_ids:
                print(f"Using unique player ID: {candidate_id}")
                return candidate_id
            else:
                print(f"ID '{candidate_id}' already exists. Retrying...")

        print("Maximum ID generation attempts reached. Proceeding anyway.")
        return candidate_id

    def input_player_name(self):
        font = pygame.font.Font(None, 48)
        input_box = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 30, 400, 60)
        color_inactive = COLORS['LIGHT_GRAY']
        color_active = COLORS['WHITE']
        color = color_inactive
        active = False
        text = ''

        instructions = font.render("Enter your player name", True, COLORS['WHITE'])
        running = True

        while running:
            screen.fill(COLORS['BACKGROUND'])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    active = input_box.collidepoint(event.pos)
                    color = color_active if active else color_inactive
                elif event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_RETURN and text.strip():
                            return text.strip()
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        elif len(text) < 20:
                            text += event.unicode

            pygame.draw.rect(screen, COLORS['UI_BACKGROUND'], input_box, border_radius=10)
            pygame.draw.rect(screen, color, input_box, 2, border_radius=10)

            txt_surface = font.render(text, True, COLORS['WHITE'])
            screen.blit(txt_surface, (input_box.x + 10, input_box.y + 15))

            instruction_rect = instructions.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
            screen.blit(instructions, instruction_rect)

            pygame.display.flip()
            clock.tick(30)

    def initialize_game(self):
        """Initialize game with enhanced error handling"""
        try:
            result = self.client_interface.add_player()
            if result['status'] == 'ERROR':
                self.connection_error = f"Failed to add player: {result['message']}"
                return False
            
            self.current_player = Player(self.player_id, self.player_name, is_local=True)
            
            if not self.update_game_state():
                self.connection_error = "Failed to get game state from server"
                return False

            return True
            
        except Exception as e:
            self.connection_error = f"Game initialization error: {e}"
            return False

    def update_game_state(self):
        """Update game state with enhanced data"""
        try:
            self.game_state = self.client_interface.get_game_state()
            if not self.game_state or self.game_state.get('status') == 'ERROR':
                return False

            # Check if the game was reset
            previous_round = getattr(self, 'current_round', 0)
            current_round = self.game_state.get('round_number', 1)
            game_was_reset = current_round > previous_round
            self.current_round = current_round

            self.maze_renderer = MazeRenderer(self.game_state)
            
            # Update other players with enhanced info
            all_players = self.client_interface.get_all_players()
            if all_players:
                for player_id in all_players:
                    if player_id != self.player_id and player_id not in self.other_players:
                        player_info = self.game_state.get('player_info', {}).get(player_id, {})
                        player_name = player_info.get('name', f'Player {player_id}')
                        self.other_players[player_id] = Player(player_id, player_name, is_local=False)
            
            #if game was reset, sync player positions
            if game_was_reset and self.maze_renderer:
                start_x = self.maze_renderer.start_pos[0] * self.maze_renderer.cell_size
                start_y = self.maze_renderer.start_pos[1] * self.maze_renderer.cell_size

                if self.current_player:
                    self.current_player.x = start_x
                    self.current_player.y = start_y
                
                for player_id, player in self.other_players.items():
                    server_pos = self.client_interface.get_location(player_id)
                    if server_pos:
                        player.x, player.y = server_pos
                    else:
                        player.x, player.y = start_x, start_y
            
            self.winner = self.game_state.get('winner')
            return True
            
        except Exception as e:
            logging.warning(f"Failed to update game state: {e}")
            return False

    def draw_enhanced_ui(self, surface):
        """Draw enhanced UI with animations and better layout"""
        self.ui_animations['score_pulse'] += 0.1
        self.ui_animations['winner_glow'] += 0.05
        
        # Draw main game panel
        ui_rect = pygame.Rect(WIDTH - 350, 0, 350, HEIGHT)
        pygame.draw.rect(surface, COLORS['UI_BACKGROUND'], ui_rect)
        pygame.draw.rect(surface, COLORS['UI_BORDER'], ui_rect, 2)
        
        y_offset = 20
        
        # Game title
        title_text = self.font_large.render("🎮 MAZE ESCAPE", True, COLORS['TEXT_PRIMARY'])
        surface.blit(title_text, (WIDTH - 340, y_offset))
        y_offset += 60
        
        # Game info
        if self.game_state:
            round_text = self.font_medium.render(f"Round: {self.game_state.get('round_number', 1)}", True, COLORS['INFO'])
            time_text = self.font_medium.render(f"Time: {self.game_state.get('game_time', 0)}s", True, COLORS['INFO'])
            surface.blit(round_text, (WIDTH - 340, y_offset))
            surface.blit(time_text, (WIDTH - 340, y_offset + 30))
            y_offset += 80
        
        # Player stats section
        stats_title = self.font_medium.render("📊 LEADERBOARD", True, COLORS['TEXT_PRIMARY'])
        surface.blit(stats_title, (WIDTH - 340, y_offset))
        y_offset += 40
        
        # Draw player stats
        if self.game_state and 'player_stats' in self.game_state:
            players_stats = []
            for pid, stats in self.game_state['player_stats'].items():
                player_info = self.game_state.get('player_info', {}).get(pid, {})
                name = player_info.get('name', f'Player {pid}')
                players_stats.append((name, stats, pid))
            
            # Sort by score
            players_stats.sort(key=lambda x: x[1]['score'], reverse=True)
            
            for i, (name, stats, pid) in enumerate(players_stats[:6]):
                is_current = pid == self.player_id
                color = COLORS['SUCCESS'] if is_current else COLORS['TEXT_SECONDARY']
                
                # Rank and name
                rank_text = f"#{i+1}"
                name_display = name[:12] + "..." if len(name) > 12 else name
                
                rank_surface = self.font_small.render(rank_text, True, color)
                name_surface = self.font_small.render(name_display, True, color)
                
                # Score with pulse effect for current player
                score = stats['score']
                if is_current:
                    pulse = abs(math.sin(self.ui_animations['score_pulse'])) * 20
                    score_color = tuple(min(255, c + int(pulse)) for c in COLORS['SUCCESS'])
                else:
                    score_color = color
                
                score_surface = self.font_small.render(f"{score}pts", True, score_color)
                
                surface.blit(rank_surface, (WIDTH - 340, y_offset))
                surface.blit(name_surface, (WIDTH - 300, y_offset))
                surface.blit(score_surface, (WIDTH - 120, y_offset))
                
                # Additional stats for current player
                if is_current:
                    wins_text = self.font_tiny.render(f"Wins: {stats['wins']}", True, COLORS['TEXT_SECONDARY'])
                    moves_text = self.font_tiny.render(f"Moves: {stats['total_moves']}", True, COLORS['TEXT_SECONDARY'])
                    surface.blit(wins_text, (WIDTH - 340, y_offset + 18))
                    surface.blit(moves_text, (WIDTH - 250, y_offset + 18))
                    y_offset += 40
                else:
                    y_offset += 25
        
        # Controls section
        y_offset += 20
        controls_title = self.font_medium.render("🎮 CONTROLS", True, COLORS['TEXT_PRIMARY'])
        surface.blit(controls_title, (WIDTH - 340, y_offset))
        y_offset += 35
        
        controls = [
            "↑↓←→ or WASD: Move",
            "R: Reset Game",
            "ESC: Quit Game"
        ]
        
        for control in controls:
            control_text = self.font_tiny.render(control, True, COLORS['TEXT_SECONDARY'])
            surface.blit(control_text, (WIDTH - 340, y_offset))
            y_offset += 20
        
        # Collectibles legend
        y_offset += 20
        legend_title = self.font_medium.render("💎 COLLECTIBLES", True, COLORS['TEXT_PRIMARY'])
        surface.blit(legend_title, (WIDTH - 340, y_offset))
        y_offset += 35
        
        legend_items = [
            ("🟡 Coin: 10pts", COLORS['GOLD']),
            ("💎 Gem: 25pts", COLORS['CYAN']),
            ("⭐ Star: 50pts", COLORS['YELLOW'])
        ]
        
        for item, color in legend_items:
            legend_text = self.font_tiny.render(item, True, color)
            surface.blit(legend_text, (WIDTH - 340, y_offset))
            y_offset += 20
        
        # Winner announcement
        if self.winner:
            winner_info = self.game_state.get('player_info', {}).get(self.winner, {})
            winner_name = winner_info.get('name', f'Player {self.winner}')
            
            # Create winner banner
            banner_rect = pygame.Rect(50, HEIGHT//2 - 100, WIDTH - 450, 200)
            
            # Animated glow effect
            glow = abs(math.sin(self.ui_animations['winner_glow'])) * 100
            glow_color = (*COLORS['GOLD'], int(glow))
            
            pygame.draw.rect(surface, COLORS['UI_BACKGROUND'], banner_rect)
            pygame.draw.rect(surface, COLORS['GOLD'], banner_rect, 4)
            
            if self.winner == self.player_id:
                winner_text = "🎉 YOU WON! 🎉"
                text_color = COLORS['SUCCESS']
            else:
                winner_text = f"🏆 {winner_name} WINS! 🏆"
                text_color = COLORS['WARNING']
            
            win_surface = self.font_large.render(winner_text, True, text_color)
            win_rect = win_surface.get_rect(center=banner_rect.center)
            surface.blit(win_surface, win_rect)
            
            # Reset instruction
            reset_text = self.font_medium.render("Press R to play again", True, COLORS['TEXT_SECONDARY'])
            reset_rect = reset_text.get_rect(center=(banner_rect.centerx, banner_rect.centery + 50))
            surface.blit(reset_text, reset_rect)

    def handle_reset(self):
        """Reset game with visual feedback"""
        result = self.client_interface.reset_game()
        if result['status'] == 'OK':
            self.winner = None
            self.update_game_state()

            #Syncs player initial position
            if self.current_player and self.maze_renderer:
                start_x = self.maze_renderer.start_pos[0] * self.maze_renderer.cell_size
                start_y = self.maze_renderer.start_pos[1] * self.maze_renderer.cell_size
                self.current_player.x = start_x
                self.current_player.y = start_y

                #syncs other players
                for player_id, player in self.other_players.items():
                    server_pos = self.client_interface.get_location(player_id)
                    if server_pos:
                        player.x, player.y = server_pos
                    else:
                        player.x, player.y = start_x, start_y

            # Add reset particles
            for _ in range(20):
                self.particle_system.add_particle(
                    random.randint(0, WIDTH-350), 
                    random.randint(0, HEIGHT),
                    COLORS['SUCCESS'], 
                    (random.uniform(-5, 5), random.uniform(-5, 5)), 
                    60
                )

    def run(self):
        """Enhanced main game loop"""
        if self.connection_error:
            print(f"❌ Cannot start game: {self.connection_error}")
            return
            
        running = True
        last_update = 0

        print("🎮 Enhanced game window opened!")
        print(f"🏃 Playing as: {self.player_name}")
        
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.handle_reset()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            keys = pygame.key.get_pressed()

            # Update game state
            if current_time - last_update > 1000:
                self.update_game_state()
                last_update = current_time

            # Update particles
            self.particle_system.update()

            # Move players
            if self.maze_renderer and self.current_player and not self.winner:
                self.current_player.move(keys, self.maze_renderer, self.particle_system)
                for player in self.other_players.values():
                    player.move(keys, self.maze_renderer, self.particle_system)

            # Draw everything
            screen.fill(COLORS['BACKGROUND'])
            
            if self.maze_renderer:
                self.maze_renderer.draw_maze(screen)
                
            if self.current_player:
                self.current_player.draw(screen)
            for player in self.other_players.values():
                player.draw(screen)

            # Draw particles
            self.particle_system.draw(screen)

            # Draw enhanced UI
            self.draw_enhanced_ui(screen)

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

def main():
    print("=" * 60)
    print("    🎮 ESCAPE THE MAZE - Enhanced Multiplayer Game")
    print("=" * 60)

    try:
        import os
        os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'

        game = Game()  # No arguments needed now
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