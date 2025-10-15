import pygame
import random
from enum import Enum

# Constants
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 256  # Increased to accommodate HUD bar (240 + 16)
HUD_HEIGHT = 16  # One grid size for HUD
GAME_OFFSET_Y = HUD_HEIGHT  # Game starts below HUD
GRID_SIZE = 16  # Doubled from 8 to 16 for better visibility
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - HUD_HEIGHT) // GRID_SIZE  # Grid height excludes HUD

# Colors - Neon Rave Theme
BLACK = (0, 0, 0)
DARK_BG = (10, 5, 20)  # Deep purple-black background
WHITE = (255, 255, 255)
NEON_GREEN = (57, 255, 20)  # Bright neon green
NEON_LIME = (191, 255, 0)  # Electric lime
NEON_PINK = (255, 16, 240)  # Hot pink
NEON_CYAN = (0, 255, 255)  # Electric cyan
NEON_ORANGE = (255, 95, 31)  # Neon orange
NEON_PURPLE = (191, 0, 255)  # Electric purple
NEON_YELLOW = (255, 255, 0)  # Bright yellow
NEON_BLUE = (0, 168, 255)  # Electric blue
GRID_COLOR = (40, 20, 60)  # Dark purple grid
HUD_BG = (20, 10, 40)  # Dark purple HUD background

# Legacy color names for compatibility
GREEN = NEON_GREEN
DARK_GREEN = NEON_LIME
RED = NEON_PINK
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
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    HIGH_SCORE_ENTRY = 5
    HIGH_SCORES = 6
    LEVEL_COMPLETE = 7

# Direction enum
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Particle:
    """Visual effect particle"""
    def __init__(self, x, y, color, velocity):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = 30
        self.size = random.randint(4, 8)  # Doubled from 2-4 to 4-8
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(1, self.size - 0.1)
    
    def draw(self, screen):
        if self.lifetime > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))
    
    def is_alive(self):
        return self.lifetime > 0

class MusicManager:
    """Manages random music playback without immediate repeats"""
    def __init__(self):
        self.tracks = ['sound/music1.mp3', 'sound/music2.mp3', 'sound/music3.mp3']
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
            pygame.mixer.music.play()
        except:
            print(f"Warning: Could not load {self.current_track}")
    
    def play_game_over_music(self):
        """Play the game over music"""
        self.game_over_mode = True
        try:
            pygame.mixer.music.load('sound/GameOver.mp3')
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
            'blip_select': 'sound/blipSelect.wav',
            'die': 'sound/die.wav',
            'eat_fruit': 'sound/EatFruit.wav',
            'level_up': 'sound/LevelUp.wav',
            'no_lives': 'sound/NoLives.wav',
            'powerup': 'sound/powerup.wav',
            'select_letter': 'sound/SelectLetter.wav',
            'start_game': 'sound/StartGame.wav'
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
    def __init__(self):
        self.reset()
    
    def reset(self):
        center_x = GRID_WIDTH // 2
        center_y = GRID_HEIGHT // 2
        self.body = [(center_x, center_y), (center_x - 1, center_y), (center_x - 2, center_y)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.grow_pending = 0
    
    def move(self):
        """Move snake one step"""
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
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
    
    def check_collision(self):
        """Check if snake hit walls or itself"""
        head_x, head_y = self.body[0]
        
        # Wall collision
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            return True
        
        # Self collision
        if self.body[0] in self.body[1:]:
            return True
        
        return False
    
    def grow(self, amount=1):
        """Grow snake by amount"""
        self.grow_pending += amount
