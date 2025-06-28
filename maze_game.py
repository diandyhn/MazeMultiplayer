import base64
import random
import time
from io import BytesIO
import logging
from PIL import Image, ImageDraw, ImageFont

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
        self.player_stats = {}  # New: track player statistics
        self.game_started = False
        self.winner = None
        self.game_start_time = time.time()
        self.round_number = 1
        
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
        
        # Power-ups and collectibles
        self.collectibles = self.generate_collectibles()

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

    def generate_collectibles(self):
        """Generate collectible items in the maze"""
        collectibles = []
        empty_cells = []
        
        # Find all empty cells except start and end
        for y in range(self.maze_height):
            for x in range(self.maze_width):
                if (self.maze[y][x] == 0 and 
                    (x, y) != self.start_pos and 
                    (x, y) != self.end_pos):
                    empty_cells.append((x, y))
        
        # Place 5-8 collectibles randomly
        num_collectibles = min(random.randint(5, 8), len(empty_cells))
        selected_cells = random.sample(empty_cells, num_collectibles)
        
        for x, y in selected_cells:
            collectible_type = random.choice(['coin', 'gem', 'star'])
            collectibles.append({
                'x': x,
                'y': y,
                'type': collectible_type,
                'collected': False,
                'value': {'coin': 10, 'gem': 25, 'star': 50}[collectible_type]
            })
        
        return collectibles

    def add_player(self, player_id, player_name="Unknown"):
        """Add a new player to the game"""
        if player_id not in self.players:
            color_index = len(self.players) % len(self.player_colors)
            self.players[player_id] = {
                'name': player_name,
                'color': self.player_colors[color_index],
                'avatar': self.generate_player_avatar(self.player_colors[color_index], player_name)
            }
            # Place player at start position
            self.player_positions[player_id] = {
                'x': self.start_pos[0] * self.cell_size,
                'y': self.start_pos[1] * self.cell_size
            }
            # Initialize player stats
            self.player_stats[player_id] = {
                'score': 0,
                'wins': 0,
                'games_played': 0,
                'collectibles_collected': 0,
                'total_moves': 0,
                'join_time': time.time()
            }
            logging.warning(f"Player {player_id} ({player_name}) added to game")

    def generate_player_avatar(self, color, name):
        """Generate a more attractive avatar for the player"""
        size = 28
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw outer glow
        for i in range(3):
            alpha = 50 - i * 15
            glow_color = (*color, alpha)
            draw.ellipse([1-i, 1-i, size-1+i, size-1+i], fill=glow_color)
        
        # Draw main circle with gradient effect
        draw.ellipse([3, 3, size-3, size-3], fill=color, outline=(255, 255, 255), width=2)
        
        # Add inner highlight
        highlight_color = tuple(min(255, c + 60) for c in color)
        draw.ellipse([6, 6, size//2, size//2], fill=highlight_color)
        
        # Try to add initial letter
        try:
            # Use default font
            font_size = 12
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Draw player initial
            initial = name[0].upper() if name and name != "Unknown" else "?"
            bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (size - text_width) // 2
            text_y = (size - text_height) // 2 - 2
            
            # Draw text shadow
            draw.text((text_x + 1, text_y + 1), initial, fill=(0, 0, 0), font=font)
            # Draw main text
            draw.text((text_x, text_y), initial, fill=(255, 255, 255), font=font)
        except:
            # Fallback: draw a simple dot
            draw.ellipse([size//2-2, size//2-2, size//2+2, size//2+2], fill=(255, 255, 255))
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str

    def is_valid_position(self, x, y):
        """Check if the player's full bounding circle is within valid maze paths"""
        # Radius player circle of 14 pixels (from player image size 28x28)
        radius = 14

        # 9 points: center + 4 sides + 4 corners
        edge_points = [
            (x + radius, y + radius),              # Center
            (x, y + radius),                       # Left
            (x + 2 * radius, y + radius),          # Right
            (x + radius, y),                       # Top
            (x + radius, y + 2 * radius),          # Bottom
            (x, y),                                # Top-left corner
            (x + 2 * radius, y),                   # Top-right corner
            (x, y + 2 * radius),                   # Bottom-left corner
            (x + 2 * radius, y + 2 * radius),      # Bottom-right corner
        ]

        for px, py in edge_points:
            maze_x = px // self.cell_size
            maze_y = py // self.cell_size

            # Check bounds
            if (maze_x < 0 or maze_x >= self.maze_width or 
                maze_y < 0 or maze_y >= self.maze_height):
                return False

            # Check wall
            if self.maze[maze_y][maze_x] != 0:
                return False

        return True

    def move_player(self, player_id, new_x, new_y):
        """Move player if the new position is valid"""
        if player_id not in self.player_positions:
            return False
            
        if self.is_valid_position(new_x, new_y):
            old_x = self.player_positions[player_id]['x']
            old_y = self.player_positions[player_id]['y']
            
            self.player_positions[player_id]['x'] = new_x
            self.player_positions[player_id]['y'] = new_y
            
            # Count moves
            if old_x != new_x or old_y != new_y:
                self.player_stats[player_id]['total_moves'] += 1
            
            # Check for collectibles
            self.check_collectibles(player_id, new_x, new_y)
            
            # Check win condition
            maze_x = new_x // self.cell_size
            maze_y = new_y // self.cell_size
            if (maze_x, maze_y) == self.end_pos and not self.winner:
                self.winner = player_id
                self.player_stats[player_id]['wins'] += 1
                self.player_stats[player_id]['score'] += 100  # Bonus for winning
                logging.warning(f"Player {player_id} won the game!")
            
            return True
        return False

    def check_collectibles(self, player_id, x, y):
        """Check if player collected any items"""
        maze_x = x // self.cell_size
        maze_y = y // self.cell_size
        
        for collectible in self.collectibles:
            if (not collectible['collected'] and 
                collectible['x'] == maze_x and 
                collectible['y'] == maze_y):
                collectible['collected'] = True
                collectible['collected_by'] = player_id
                self.player_stats[player_id]['score'] += collectible['value']
                self.player_stats[player_id]['collectibles_collected'] += 1

    def get_game_state(self):
        """Get current game state for clients"""
        return {
            'maze': self.maze,
            'maze_width': self.maze_width,
            'maze_height': self.maze_height,
            'cell_size': self.cell_size,
            'players': self.player_positions,
            'player_info': self.players,
            'player_stats': self.player_stats,
            'collectibles': self.collectibles,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'winner': self.winner,
            'round_number': self.round_number,
            'game_time': int(time.time() - self.game_start_time)
        }

    def reset_game(self):
        """Reset game for a new round"""
        self.winner = None
        self.maze = self.generate_maze()
        self.collectibles = self.generate_collectibles()
        self.game_start_time = time.time()
        self.round_number += 1
        
        # Reset player positions but keep stats
        for player_id in self.player_positions:
            self.player_positions[player_id] = {
                'x': self.start_pos[0] * self.cell_size,
                'y': self.start_pos[1] * self.cell_size
            }
            self.player_stats[player_id]['games_played'] += 1
