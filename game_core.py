import pygame
import random
import os
from enum import Enum
import colorsys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Constants
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 480  # Square screen for Raspberry Pi
HUD_HEIGHT = 32  # HUD overlay height (top portion of screen)
GAME_OFFSET_Y = 0  # Game uses full screen, HUD is overlaid
GRID_SIZE = 32  
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE  # Grid uses full height

# Debug: Print grid calculations
print("DEBUG: SCREEN_HEIGHT={}, HUD_HEIGHT={}, GRID_SIZE={}".format(SCREEN_HEIGHT, HUD_HEIGHT, GRID_SIZE))
print("DEBUG: GRID_WIDTH={}, GRID_HEIGHT={}".format(GRID_WIDTH, GRID_HEIGHT))
print("DEBUG: Game area pixels: {} to {}".format(GAME_OFFSET_Y, SCREEN_HEIGHT))

# Colors - Backyard Theme
BLACK = (0, 0, 0)
DARK_BG = (40, 30, 20)  # Dark brown background
WHITE = (255, 255, 255)
NEON_GREEN = (80, 140, 60)  # Natural grass green
NEON_LIME = (120, 180, 80)  # Light grass green
NEON_PINK = (220, 100, 140)  # Soft pink/rose
NEON_CYAN = (100, 180, 200)  # Sky blue
NEON_ORANGE = (230, 120, 60)  # Warm orange
NEON_PURPLE = (140, 100, 160)  # Soft purple
NEON_YELLOW = (240, 200, 80)  # Warm yellow/gold
NEON_BLUE = (80, 120, 180)  # Natural blue
GRID_COLOR = (60, 50, 40)  # Dark earth brown
HUD_BG = (50, 40, 30)  # Medium brown

# Legacy color names for compatibility
GREEN = NEON_GREEN
DARK_GREEN = NEON_LIME
RED = (200, 60, 60)  # Softer red
YELLOW = NEON_YELLOW
ORANGE = NEON_ORANGE
GRAY = (128, 128, 128)
DARK_GRAY = GRID_COLOR

# Button mappings
class GamepadButton:
    BTN_A = 0
    BTN_B = 1
    BTN_X = 2
    BTN_Y = 3
    BTN_L = 4
    BTN_R = 5
    BTN_SELECT = 6
    BTN_START = 7

# Game states
class GameState(Enum):
    SPLASH = 0
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    HIGH_SCORE_ENTRY = 5
    HIGH_SCORES = 6
    LEVEL_COMPLETE = 7
    DIFFICULTY_SELECT = 8
    EGG_HATCHING = 9
    MULTIPLAYER_MENU = 10
    MULTIPLAYER_LOBBY = 11
    SINGLE_PLAYER_MENU = 12
    ADVENTURE_LEVEL_SELECT = 13

# Difficulty modes
class Difficulty(Enum):
    EASY = 1    # Wrap-around walls, 0.5x score
    MEDIUM = 2  # Current gameplay, 1x score
    HARD = 3    # Moving enemies, 2x score

# Direction enum
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Utility function for hue shifting
def hue_shift_surface(surface, hue_shift):
    """Apply a hue shift to a pygame surface.
    hue_shift: 0-360 degrees to shift the hue
    """
    if surface is None:
        return None
    
    # Create a copy of the surface
    shifted = surface.copy()
    width, height = shifted.get_size()
    
    # Lock surface for pixel access
    shifted.lock()
    
    for x in range(width):
        for y in range(height):
            # Get the color at this pixel
            r, g, b, a = shifted.get_at((x, y))
            
            # Skip fully transparent pixels
            if a == 0:
                continue
            
            # Convert RGB to HSV
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            
            # Shift the hue
            h = (h + hue_shift / 360.0) % 1.0
            
            # Convert back to RGB
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            
            # Set the new color
            shifted.set_at((x, y), (int(r * 255), int(g * 255), int(b * 255), a))
    
    shifted.unlock()
    return shifted

def hue_shift_frames(frames, hue_shift):
    """Apply hue shift to a list of frames (for animations)"""
    return [hue_shift_surface(frame, hue_shift) for frame in frames]

def hue_shift_color(color, hue_shift):
    """Apply hue shift to a single RGB color tuple"""
    r, g, b = color[0], color[1], color[2]
    
    # Convert RGB to HSV
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    
    # Shift the hue
    h = (h + hue_shift / 360.0) % 1.0
    
    # Convert back to RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    return (int(r * 255), int(g * 255), int(b * 255))

class Particle:
    """Visual effect particle"""
    def __init__(self, x, y, color, velocity):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = 15  # Reduced from 30 to 15 for better performance
        self.size = random.randint(2, 4)  # Reduced size for performance
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        # Size shrinking removed for performance (less calculations)
    
    def draw(self, screen):
        if self.lifetime > 0:
            # Use rect instead of circle - much faster on low-end hardware
            pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.size, self.size))
    
    def is_alive(self):
        return self.lifetime > 0

class GifParticle:
    """Animated GIF particle effect"""
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.frames = frames
        self.frame_index = 0
        self.alive = True if frames else False
    
    def update(self):
        if self.alive:
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.alive = False
    
    def draw(self, screen):
        if self.alive and self.frame_index < len(self.frames):
            frame = self.frames[self.frame_index]
            # Center the particle effect on the position
            offset_x = frame.get_width() // 2
            offset_y = frame.get_height() // 2
            # Normal blitting (transparency handled by the GIF itself)
            screen.blit(frame, (int(self.x - offset_x), int(self.y - offset_y)))
    
    def is_alive(self):
        return self.alive

class EggPiece:
    """Flying egg shell piece with rotation"""
    def __init__(self, x, y, image, velocity):
        self.x = x
        self.y = y
        self.image = image
        self.vx, self.vy = velocity
        self.rotation = 0
        self.rotation_speed = random.uniform(-15, 15)  # Random rotation speed
        self.lifetime = 60  # About 1 second at 60 FPS
        self.alpha = 255
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3  # Gravity
        self.rotation += self.rotation_speed
        self.lifetime -= 1
        # Fade out in the last 20 frames
        if self.lifetime < 20:
            self.alpha = int(255 * (self.lifetime / 20))
    
    def draw(self, screen):
        if self.lifetime > 0:
            # Rotate the image
            rotated = pygame.transform.rotate(self.image, self.rotation)
            # Apply alpha
            rotated.set_alpha(self.alpha)
            # Center the rotated image
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(rotated, rect)
    
    def is_alive(self):
        return self.lifetime > 0

class MusicManager:
    """Manages random music playback without immediate repeats"""
    def __init__(self):
        self.tracks = [
            os.path.join(SCRIPT_DIR, 'sound', 'music', 'music1.mp3'),
            os.path.join(SCRIPT_DIR, 'sound', 'music', 'music2.mp3'),
            os.path.join(SCRIPT_DIR, 'sound', 'music', 'music3.mp3')
        ]
        self.last_track = None
        self.current_track = None
        self.music_enabled = True
        self.game_over_mode = False
        
    def play_next(self):
        """Play a random track that's different from the last one"""
        if not self.music_enabled or self.game_over_mode:
            return
            
        available_tracks = [t for t in self.tracks if t != self.last_track]
        if not available_tracks:
            available_tracks = self.tracks
        
        self.current_track = random.choice(available_tracks)
        self.last_track = self.current_track
        
        try:
            pygame.mixer.music.load(self.current_track)
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play()
        except:
            print(f"Warning: Could not load {self.current_track}")
    
    def play_game_over_music(self):
        """Play the game over music"""
        self.game_over_mode = True
        try:
            game_over_path = os.path.join(SCRIPT_DIR, 'sound', 'music', 'GameOver.mp3')
            pygame.mixer.music.load(game_over_path)
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play(-1)  # Loop indefinitely
        except:
            print("Warning: Could not load GameOver.mp3")
    
    def stop_game_over_music(self):
        """Stop game over music and resume normal music"""
        if self.game_over_mode:
            self.game_over_mode = False
            pygame.mixer.music.stop()
            self.play_next()
    
    def update(self):
        """Check if music finished and play next track"""
        if self.music_enabled and not self.game_over_mode and not pygame.mixer.music.get_busy():
            self.play_next()


class SoundManager:
    """Manages sound effects for game events"""
    def __init__(self):
        self.sounds = {}
        self.sound_enabled = True
        
        # Load all sound effects
        sound_files = {
            'blip_select': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'blipSelect.wav'),
            'die': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'die.wav'),
            'eat_fruit': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'EatFruit.wav'),
            'level_up': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'LevelUp.wav'),
            'no_lives': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'NoLives.wav'),
            'powerup': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'powerup.wav'),
            'fullSnake': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'fullSnake.wav'),
            'select_letter': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'SelectLetter.wav'),
            'start_game': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'StartGame.wav'),
            'crack': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'crack.wav'),
            'pickupCoin': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'pickupCoin.wav'),
            'pickupDiamond': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'pickupDiamond.wav')
        }
        
        for name, path in sound_files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except:
                print(f"Warning: Could not load {path}")
                self.sounds[name] = None
    
    def play(self, sound_name):
        """Play a sound effect by name"""
        if self.sound_enabled and sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].play()

class Snake:
    """Snake game logic"""
    def __init__(self, player_id=0):
        self.player_id = player_id
        self.alive = True
        self.score = 0
        self.lives = 3  # Lives in multiplayer
        self.is_cpu = False  # Is this a CPU player?
        self.cpu_difficulty = 0  # 0=Easy, 1=Medium, 2=Hard, 3=Brutal
        self.speed_modifier = 0  # For multiplayer: apples increase, black apples decrease
        self.move_timer = 0  # Track movement progress for interpolation
        self.last_move_interval = 16  # Track the interval used for last move
        self.reset()
    
    def reset(self, spawn_pos=None, direction=None):
        if spawn_pos:
            center_x, center_y = spawn_pos
        else:
            center_x = GRID_WIDTH // 2
            center_y = GRID_HEIGHT // 2
        # Start with just the head - body will grow as player moves
        self.body = [(center_x, center_y)]
        self.previous_body = list(self.body)  # Track previous positions for interpolation
        
        # Set direction (default to RIGHT if not specified)
        if direction:
            self.direction = direction
            self.next_direction = direction
        else:
            self.direction = Direction.RIGHT
            self.next_direction = Direction.RIGHT
        
        self.grow_pending = 2  # Add 2 segments immediately so we start with 3 total
        self.alive = True
        self.move_timer = 0  # Reset move timer
        self.last_move_interval = 16
        # Don't reset speed_modifier - it persists across deaths in multiplayer
    
    def move(self):
        """Move snake one step"""
        # Save previous body positions for smooth interpolation
        self.previous_body = list(self.body)
        
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value
        new_head_x = head_x + dx
        new_head_y = head_y + dy
        
        # Wrap around if out of bounds (for adventure mode)
        if new_head_x < 0:
            new_head_x = GRID_WIDTH - 1
        elif new_head_x >= GRID_WIDTH:
            new_head_x = 0
        
        if new_head_y < 0:
            new_head_y = GRID_HEIGHT - 1
        elif new_head_y >= GRID_HEIGHT:
            new_head_y = 0
        
        new_head = (new_head_x, new_head_y)
        self.body.insert(0, new_head)
        
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()
    
    def change_direction(self, new_direction):
        """Change direction if not opposite to current"""
        dx, dy = self.direction.value
        new_dx, new_dy = new_direction.value
        
        # Prevent 180 degree turns
        if (dx + new_dx, dy + new_dy) != (0, 0):
            self.next_direction = new_direction
    
    def check_collision(self, wrap_around=False):
        """Check if snake hit walls or itself"""
        head_x, head_y = self.body[0]
        
        # Wall collision - 1 grid cell border (32 pixels) on left, right, and bottom
        # Top is handled by HUD area (y < 0 would be in HUD)
        # The border occupies: x=0, x=GRID_WIDTH-1, y=GRID_HEIGHT-1
        if not wrap_around:
            if head_x <= 0 or head_x >= GRID_WIDTH - 1 or head_y < 1 or head_y >= GRID_HEIGHT - 1:
                return True
        
        # Self collision
        if self.body[0] in self.body[1:]:
            return True
        
        return False
    
    def wrap_position(self):
        """Wrap the snake's head position around the grid edges."""
        head_x, head_y = self.body[0]
        original_y = head_y
        
        # Wrap horizontally
        if head_x < 0:
            head_x = GRID_WIDTH - 1
        elif head_x >= GRID_WIDTH:
            head_x = 0
        
        # Wrap vertically
        if head_y < 0:
            print("DEBUG: Wrapping from y={} to y={}".format(head_y, GRID_HEIGHT - 1))
            head_y = GRID_HEIGHT - 1
        elif head_y >= GRID_HEIGHT:
            print("DEBUG: Wrapping from y={} to y=0".format(head_y))
            head_y = 0
        
        self.body[0] = (head_x, head_y)
        
        # Debug: Print if we're in an invalid range
        if head_y < 0 or head_y >= GRID_HEIGHT:
            print("ERROR: Snake head at invalid y={} (valid range: 0-{})".format(head_y, GRID_HEIGHT-1))
    
    def grow(self, amount=1):
        """Grow snake by amount"""
        self.grow_pending += amount


class Enemy:
    """Base enemy class for adventure mode"""
    def __init__(self, x, y, enemy_type):
        self.grid_x = x
        self.grid_y = y
        self.enemy_type = enemy_type
        self.alive = True
        
        # Movement properties
        self.previous_x = x
        self.previous_y = y
        self.move_timer = 0  # For interpolation
        self.angle = 0  # Direction the enemy is facing (0=right, 90=down, 180=left, 270=up)
        
        # Animation properties
        self.animation_frame = 0  # Current frame of animation
        self.animation_counter = 0  # Counter for animation timing
        
        # Ant-specific properties
        if enemy_type.startswith('enemy_ant'):
            self.move_cooldown = 0  # Counts turns until next move (moves every 3 turns)
            self.rotation_delay = 0  # Delay before actual movement (1 second = 60 frames at 60 FPS)
            self.target_angle = 0  # The angle to rotate to before moving
            self.target_x = x
            self.target_y = y
            self.is_rotating = False
            self.is_moving = False
        
        # Spider-specific properties (similar to ant but faster)
        if enemy_type.startswith('enemy_spider'):
            self.move_cooldown = 0  # Counts turns until next move (moves every 1-2 turns, faster than ants)
            self.rotation_delay = 0  # Delay before actual movement
            self.target_angle = 0  # The angle to rotate to before moving
            self.target_x = x
            self.target_y = y
            self.is_rotating = False
            self.is_moving = False
    
    def update(self, snake_body, level_walls, collectibles):
        """Update enemy behavior based on type"""
        if not self.alive:
            return
        
        if self.enemy_type.startswith('enemy_ant'):
            self._update_ant(snake_body, level_walls, collectibles)
        elif self.enemy_type.startswith('enemy_spider'):
            self._update_spider(snake_body, level_walls, collectibles)
    
    def update_animation(self, total_frames, animation_speed=1):
        """Update animation frame - only animates when moving"""
        if self.is_moving and total_frames > 0:
            self.animation_counter += 1
            if self.animation_counter >= animation_speed:
                self.animation_counter = 0
                self.animation_frame = (self.animation_frame + 1) % total_frames
    
    def _update_ant(self, snake_body, level_walls, collectibles):
        """Ant AI: moves every 3 turns to a random adjacent square"""
        # Handle rotation delay
        if self.is_rotating:
            if self.rotation_delay > 0:
                self.rotation_delay -= 1
                # Smoothly rotate to target angle
                angle_diff = self.target_angle - self.angle
                if abs(angle_diff) > 180:
                    if angle_diff > 0:
                        angle_diff -= 360
                    else:
                        angle_diff += 360
                self.angle += angle_diff * 0.3  # Smooth rotation (faster)
                self.angle = self.angle % 360
            else:
                # Rotation complete, start moving
                self.angle = self.target_angle
                self.is_rotating = False
                self.is_moving = True
                self.move_timer = 0
                self.previous_x = self.grid_x
                self.previous_y = self.grid_y
            return
        
        # Handle movement interpolation
        if self.is_moving:
            self.move_timer += 1
            if self.move_timer >= 10:  # Full movement complete (faster than snake)
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                self.move_timer = 0
                self.is_moving = False
                self.move_cooldown = 3  # Reset cooldown
                # Stop animation and return to frame 0
                self.animation_frame = 0
                self.animation_counter = 0
            return
        
        # Count down movement cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Time to choose a new direction and move
        self._choose_ant_move(snake_body, level_walls, collectibles)
    
    def _choose_ant_move(self, snake_body, level_walls, collectibles):
        """Choose a random adjacent square for ant to move to"""
        # Get all adjacent positions
        adjacent = [
            (self.grid_x, self.grid_y - 1, 270),  # Up
            (self.grid_x, self.grid_y + 1, 90),   # Down
            (self.grid_x - 1, self.grid_y, 180),  # Left
            (self.grid_x + 1, self.grid_y, 0)     # Right
        ]
        
        # Filter out invalid moves (walls, collectibles, out of bounds)
        valid_moves = []
        for new_x, new_y, angle in adjacent:
            # Check bounds
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            
            # Check walls
            if (new_x, new_y) in level_walls:
                continue
            
            # Check collectibles
            if any(pos == (new_x, new_y) for pos, _ in collectibles):
                continue
            
            # This position is valid (even if snake is there)
            valid_moves.append((new_x, new_y, angle))
        
        # If no valid moves, stay in place
        if not valid_moves:
            self.move_cooldown = 3
            return
        
        # Choose a random valid move
        self.target_x, self.target_y, self.target_angle = random.choice(valid_moves)
        
        # Start rotation phase
        self.is_rotating = True
        self.rotation_delay = 2  # Fast rotation (2 frames)
    
    def _update_spider(self, snake_body, level_walls, collectibles):
        """Spider AI: moves every 1-2 turns to a random adjacent square, twice as fast as ants
        Special: if player head enters target space, spider instantly moves there killing the player"""
        snake_head = snake_body[0] if snake_body else None
        
        # Special spider behavior: If not currently moving/rotating and player head is in target space,
        # instantly initiate movement to that space
        if snake_head and not self.is_rotating and not self.is_moving:
            # Check if we have a target and if snake head is there
            if hasattr(self, 'target_x') and hasattr(self, 'target_y'):
                if snake_head == (self.target_x, self.target_y):
                    # Player entered our target space! Move there immediately
                    self.is_rotating = True
                    self.rotation_delay = 1  # Very fast rotation for instant attack
                    self.move_cooldown = 0  # Override any cooldown
        
        # Handle rotation delay
        if self.is_rotating:
            if self.rotation_delay > 0:
                self.rotation_delay -= 1
                # Smoothly rotate to target angle
                angle_diff = self.target_angle - self.angle
                if abs(angle_diff) > 180:
                    if angle_diff > 0:
                        angle_diff -= 360
                    else:
                        angle_diff += 360
                self.angle += angle_diff * 0.4  # Even faster rotation than ants
                self.angle = self.angle % 360
            else:
                # Rotation complete, start moving
                self.angle = self.target_angle
                self.is_rotating = False
                self.is_moving = True
                self.move_timer = 0
                self.previous_x = self.grid_x
                self.previous_y = self.grid_y
            return
        
        # Handle movement interpolation (twice as fast as ants)
        if self.is_moving:
            self.move_timer += 1
            if self.move_timer >= 5:  # Full movement complete in 5 frames (twice as fast as ants)
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                self.move_timer = 0
                self.is_moving = False
                self.move_cooldown = random.randint(1, 2)  # Reset cooldown (1-2 turns, faster than ants)
                # Stop animation and return to frame 0
                self.animation_frame = 0
                self.animation_counter = 0
            return
        
        # Count down movement cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Time to choose a new direction and move
        self._choose_spider_move(snake_body, level_walls, collectibles)
    
    def _choose_spider_move(self, snake_body, level_walls, collectibles):
        """Choose a random adjacent square for spider to move to (similar to ant)"""
        # Get all adjacent positions
        adjacent = [
            (self.grid_x, self.grid_y - 1, 270),  # Up
            (self.grid_x, self.grid_y + 1, 90),   # Down
            (self.grid_x - 1, self.grid_y, 180),  # Left
            (self.grid_x + 1, self.grid_y, 0)     # Right
        ]
        
        # Filter out invalid moves (walls, collectibles, out of bounds)
        valid_moves = []
        for new_x, new_y, angle in adjacent:
            # Check bounds
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            
            # Check walls
            if (new_x, new_y) in level_walls:
                continue
            
            # Check collectibles
            if any(pos == (new_x, new_y) for pos, _ in collectibles):
                continue
            
            # This position is valid (even if snake is there)
            valid_moves.append((new_x, new_y, angle))
        
        # If no valid moves, stay in place
        if not valid_moves:
            self.move_cooldown = random.randint(1, 2)
            return
        
        # Choose a random valid move
        self.target_x, self.target_y, self.target_angle = random.choice(valid_moves)
        
        # Start rotation phase
        self.is_rotating = True
        self.rotation_delay = 1  # Very fast rotation (1 frame, faster than ants)
    
    def get_render_position(self):
        """Get interpolated position for rendering"""
        if self.is_moving:
            # Spiders move in 5 frames, ants move in 10 frames
            if self.enemy_type.startswith('enemy_spider'):
                progress = self.move_timer / 5.0
            else:
                progress = self.move_timer / 10.0  # Ants and other enemies
            render_x = self.previous_x + (self.target_x - self.previous_x) * progress
            render_y = self.previous_y + (self.target_y - self.previous_y) * progress
            return render_x, render_y
        return self.grid_x, self.grid_y
    
    def check_collision_with_snake(self, snake_head, snake_body):
        """Check if enemy collides with snake
        Returns: 'head' if collided with head, 'body' if collided with body, None otherwise
        """
        if not self.alive:
            return None
        
        # When moving, check collision with target position (early detection)
        # This prevents the ant from completing its full movement animation before dying
        if self.is_moving:
            check_pos = (self.target_x, self.target_y)
        else:
            check_pos = (self.grid_x, self.grid_y)
        
        # Check collision with snake head
        if check_pos == snake_head:
            return 'head'
        
        # Check collision with snake body (excluding head)
        if check_pos in snake_body[1:]:
            return 'body'
        
        return None
