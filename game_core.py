import pygame
import random
import os
from enum import Enum
import colorsys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Constants
SCREEN_WIDTH = 240  # Base resolution (scaled 2x to 480x480 for display)
SCREEN_HEIGHT = 240  # Square screen for Raspberry Pi
HUD_HEIGHT = 16  # HUD overlay height (top portion of screen)
GAME_OFFSET_Y = 0  # Game uses full screen, HUD is overlaid
GRID_SIZE = 16  # Half of original 32 for 240x240 base resolution  
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
    MULTIPLAYER_LEVEL_SELECT = 12
    SINGLE_PLAYER_MENU = 13
    ADVENTURE_LEVEL_SELECT = 14
    CREDITS = 15
    EXTRAS_MENU = 16
    ACHIEVEMENTS = 17
    MUSIC_PLAYER = 18
    LEVEL_EDITOR_MENU = 19
    INTRO = 20
    OUTRO = 21

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
        self.animation_counter = 0
        self.animation_speed = 2  # Change frame every N game frames (slower = smoother)
        self.alive = True if frames else False
    
    def update(self):
        if self.alive:
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed:
                self.animation_counter = 0
                self.frame_index += 1
                # Keep last frame visible for animation_speed frames before dying
                if self.frame_index > len(self.frames):
                    self.alive = False
    
    def draw(self, screen):
        if self.alive and self.frames:
            # Clamp frame_index to valid range (show last frame if we've gone past)
            current_frame_index = min(self.frame_index, len(self.frames) - 1)
            frame = self.frames[current_frame_index]
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
        self.theme_track = os.path.join(SCRIPT_DIR, 'sound', 'music', 'Theme.mp3')
        self.last_track = None
        self.current_track = None
        self.music_enabled = True
        self.game_over_mode = False
        self.theme_mode = False  # True when playing theme music for menus
        self.victory_jingle_playing = False  # Track when victory jingle is playing
        self.silent_mode = False  # Suppress auto-play during special sequences
        
    def play_theme(self):
        """Play the theme music on loop for menu states"""
        if not self.music_enabled or self.game_over_mode:
            return
        
        # Only load and play if not already playing theme
        if not self.theme_mode or not pygame.mixer.music.get_busy():
            self.theme_mode = True
            self.current_track = self.theme_track
            try:
                pygame.mixer.music.load(self.theme_track)
                pygame.mixer.music.set_volume(0.9)
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except:
                print("Warning: Could not load Theme.mp3")
    
    def stop_theme(self):
        """Stop the theme music"""
        if self.theme_mode:
            pygame.mixer.music.stop()
            self.theme_mode = False
            self.current_track = None
    
    def play_next(self):
        """Play a random track that's different from the last one"""
        if not self.music_enabled or self.game_over_mode:
            return
        
        # Switch out of theme mode when playing random tracks
        self.theme_mode = False
            
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
    
    def play_victory_jingle(self):
        """Play the victory jingle once (after level completion)"""
        self.silent_mode = False  # Re-enable music system for jingle
        self.victory_jingle_playing = True
        try:
            victory_path = os.path.join(SCRIPT_DIR, 'sound', 'music', 'victoryJingle.mp3')
            pygame.mixer.music.load(victory_path)
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play()  # Play once (not looping)
            # Note: After this finishes, update() will automatically resume theme music
        except:
            print("Warning: Could not load victoryJingle.mp3")
            self.victory_jingle_playing = False
            # If jingle can't load, resume theme music for menus
            self.play_theme()
    
    def play_final_song(self):
        """Play the Final song on loop for credits screen"""
        self.victory_jingle_playing = False
        self.theme_mode = False
        self.game_over_mode = False
        try:
            final_path = os.path.join(SCRIPT_DIR, 'sound', 'music', 'Final.mp3')
            pygame.mixer.music.load(final_path)
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            print("Playing Final song for credits...")
        except:
            print("Warning: Could not load Final.mp3")
    
    def update(self, in_menu=False):
        """Check if music finished and play next track
        
        Args:
            in_menu: True if currently in a menu state, False if in gameplay
        """
        if not self.music_enabled or self.game_over_mode or self.silent_mode:
            return
        
        if not pygame.mixer.music.get_busy():
            # Music has stopped, determine what to play next
            if self.victory_jingle_playing:
                # Victory jingle finished, resume theme music
                self.victory_jingle_playing = False
                self.play_theme()
            elif in_menu:
                # In menu, play theme music
                self.play_theme()
            else:
                # In gameplay, play random tracks
                if self.theme_mode:
                    # Transitioning from menu to gameplay, stop theme and start random
                    self.theme_mode = False
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
            'pickupDiamond': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'pickupDiamond.wav'),
            'frogBossDeath': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'frogBossDeath.wav'),
            'bossWormDeath': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'bossWormDeath.wav'),
            'achievement': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'achievement.wav'),
            'laser_shoot': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'laserShoot.wav'),
            'power_down': os.path.join(SCRIPT_DIR, 'sound', 'sfx', 'powerDown.wav')
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

class Bullet:
    """Bullet fired by player with isotope ability"""
    def __init__(self, x, y, direction):
        self.grid_x = x
        self.grid_y = y
        self.direction = direction  # Direction enum
        self.alive = True
        
        # Visual properties for smooth movement
        self.pixel_x = x * GRID_SIZE
        self.pixel_y = y * GRID_SIZE
        self.speed = 8  # Pixels per frame (faster than snake movement)
    
    def update(self):
        """Update bullet position"""
        if not self.alive:
            return
        
        # Move in pixel space
        dx, dy = self.direction.value
        self.pixel_x += dx * self.speed
        self.pixel_y += dy * self.speed
        
        # Update grid position
        self.grid_x = int(self.pixel_x / GRID_SIZE)
        self.grid_y = int(self.pixel_y / GRID_SIZE)
        
        # Check if out of bounds
        if (self.grid_x < 0 or self.grid_x >= GRID_WIDTH or 
            self.grid_y < 0 or self.grid_y >= GRID_HEIGHT):
            self.alive = False

class Spewtum:
    """Spewtum projectile fired by boss worm"""
    def __init__(self, pixel_x, pixel_y, frames, velocity_x, velocity_y, angle, scale=1.0):
        # Start position in pixels
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.alive = True
        self.scale = scale  # Size scaling factor (1.0 = normal, 2.0 = double size)
        
        # Movement with velocity vector
        self.velocity_x = velocity_x  # Pixels per frame
        self.velocity_y = velocity_y  # Pixels per frame
        self.angle = angle  # Rotation angle in degrees
        
        # Animation
        self.frames = frames
        self.frame_index = 0
        self.frame_counter = 0
        self.frame_speed = 3  # Frames per animation frame
        
        # Cached rotated and scaled frames for performance
        self.rotated_frames = []
        if frames:
            import pygame
            for frame in frames:
                # First scale, then rotate for better quality
                if scale != 1.0:
                    scaled_w = int(frame.get_width() * scale)
                    scaled_h = int(frame.get_height() * scale)
                    scaled_frame = pygame.transform.scale(frame, (scaled_w, scaled_h))
                    rotated = pygame.transform.rotate(scaled_frame, angle)
                else:
                    rotated = pygame.transform.rotate(frame, angle)
                self.rotated_frames.append(rotated)
        
        # Grid position for collision detection
        self.grid_x = int(self.pixel_x / GRID_SIZE)
        self.grid_y = int(self.pixel_y / GRID_SIZE)
    
    def update(self):
        """Update spewtum position and animation"""
        if not self.alive:
            return
        
        # Move based on velocity vector
        self.pixel_x += self.velocity_x
        self.pixel_y += self.velocity_y
        
        # Update grid position
        self.grid_x = int(self.pixel_x / GRID_SIZE)
        self.grid_y = int(self.pixel_y / GRID_SIZE)
        
        # Check if out of bounds (off any side of screen)
        if (self.pixel_x < -GRID_SIZE or self.pixel_x > SCREEN_WIDTH + GRID_SIZE or
            self.pixel_y < -GRID_SIZE or self.pixel_y > SCREEN_HEIGHT + GRID_SIZE):
            self.alive = False
        
        # Update animation
        if self.rotated_frames:
            self.frame_counter += 1
            if self.frame_counter >= self.frame_speed:
                self.frame_counter = 0
                self.frame_index = (self.frame_index + 1) % len(self.rotated_frames)
    
    def draw(self, screen, offset_y=0):
        """Draw the spewtum"""
        if self.alive and self.rotated_frames and self.frame_index < len(self.rotated_frames):
            frame = self.rotated_frames[self.frame_index]
            # Center the sprite on the position
            offset_x = frame.get_width() // 2
            offset_y_adjust = frame.get_height() // 2
            screen.blit(frame, (int(self.pixel_x - offset_x), int(self.pixel_y - offset_y_adjust + offset_y)))

class ScorpionStinger:
    """Stinger projectile fired by scorpion - travels in a straight line across the entire level"""
    def __init__(self, grid_x, grid_y, direction, frames):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.direction = direction  # Direction enum (UP, DOWN, LEFT, RIGHT)
        self.alive = True
        
        # Visual properties for smooth movement
        self.pixel_x = grid_x * GRID_SIZE
        self.pixel_y = grid_y * GRID_SIZE
        self.speed = 12  # Pixels per frame (very fast projectile)
        
        # Animation
        self.frames = frames if frames else []
        self.frame_index = 0
        self.frame_counter = 0
        self.frame_speed = 2  # Frames per animation frame
    
    def update(self):
        """Update stinger position"""
        if not self.alive:
            return
        
        # Move in pixel space
        dx, dy = self.direction.value
        self.pixel_x += dx * self.speed
        self.pixel_y += dy * self.speed
        
        # Update grid position
        self.grid_x = int(self.pixel_x / GRID_SIZE)
        self.grid_y = int(self.pixel_y / GRID_SIZE)
        
        # Check if out of bounds
        if (self.grid_x < 0 or self.grid_x >= GRID_WIDTH or 
            self.grid_y < 0 or self.grid_y >= GRID_HEIGHT):
            self.alive = False
        
        # Update animation
        if self.frames:
            self.frame_counter += 1
            if self.frame_counter >= self.frame_speed:
                self.frame_counter = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
    
    def draw(self, screen, offset_y=0):
        """Draw the stinger"""
        if self.alive and self.frames and self.frame_index < len(self.frames):
            frame = self.frames[self.frame_index]
            # Rotate frame based on direction
            if self.direction == Direction.UP:
                frame = pygame.transform.rotate(frame, 90)
            elif self.direction == Direction.DOWN:
                frame = pygame.transform.rotate(frame, -90)
            elif self.direction == Direction.LEFT:
                frame = pygame.transform.rotate(frame, 180)
            # Direction.RIGHT needs no rotation (default)
            
            # Center the sprite on the position
            offset_x = frame.get_width() // 2
            offset_y_adjust = frame.get_height() // 2
            screen.blit(frame, (int(self.pixel_x - offset_x), int(self.pixel_y - offset_y_adjust + offset_y)))

class BeetleLarvae:
    """Larvae projectile fired by beetle - travels in a straight line in one of four cardinal directions"""
    def __init__(self, grid_x, grid_y, direction, frames):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.direction = direction  # Direction enum (UP, DOWN, LEFT, RIGHT)
        self.alive = True
        
        # Visual properties for smooth movement
        self.pixel_x = grid_x * GRID_SIZE
        self.pixel_y = grid_y * GRID_SIZE
        self.speed = 8  # Pixels per frame (medium speed projectile)
        
        # Animation - larvae uses a static image
        self.frames = frames if frames else []
        self.frame_index = 0
    
    def update(self):
        """Update larvae position"""
        if not self.alive:
            return
        
        # Move in pixel space
        dx, dy = self.direction.value
        self.pixel_x += dx * self.speed
        self.pixel_y += dy * self.speed
        
        # Update grid position
        self.grid_x = int(self.pixel_x / GRID_SIZE)
        self.grid_y = int(self.pixel_y / GRID_SIZE)
        
        # Check if out of bounds
        if (self.grid_x < 0 or self.grid_x >= GRID_WIDTH or 
            self.grid_y < 0 or self.grid_y >= GRID_HEIGHT):
            self.alive = False
    
    def draw(self, screen, offset_y=0):
        """Draw the larvae"""
        if self.alive and self.frames and self.frame_index < len(self.frames):
            frame = self.frames[self.frame_index]
            # Rotate frame based on direction
            if self.direction == Direction.UP:
                frame = pygame.transform.rotate(frame, 90)
            elif self.direction == Direction.DOWN:
                frame = pygame.transform.rotate(frame, -90)
            elif self.direction == Direction.LEFT:
                frame = pygame.transform.rotate(frame, 180)
            # Direction.RIGHT needs no rotation (default)
            
            # Center the sprite on the position
            offset_x = frame.get_width() // 2
            offset_y_adjust = frame.get_height() // 2
            screen.blit(frame, (int(self.pixel_x - offset_x), int(self.pixel_y - offset_y_adjust + offset_y)))

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
        self.can_shoot = False  # Shooting ability from isotope pickup
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
        self.can_shoot = False  # Reset shooting ability on respawn
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
        
        # Movement properties (default for all enemies)
        self.previous_x = x
        self.previous_y = y
        self.move_timer = 0  # For interpolation
        self.angle = 0  # Direction the enemy is facing (0=right, 90=down, 180=left, 270=up)
        self.is_moving = False  # Default to stationary
        self.target_x = x
        self.target_y = y
        
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
        
        # Wasp-specific properties (continuous movement, no collision with snake body)
        if enemy_type.startswith('enemy_wasp'):
            self.target_x = x
            self.target_y = y
            self.is_moving = True  # Always moving
            self.previous_x = x
            self.previous_y = y
            # Start with a random direction
            directions = [0, 90, 180, 270]  # Right, Down, Left, Up
            self.angle = random.choice(directions)
            self.target_angle = self.angle
        
        # Enemy wall properties (stationary, destroyable by bullets)
        if enemy_type == 'enemy_wall':
            self.health = 3  # Takes 3 hits to destroy
            self.is_moving = False
            self.is_destroyable = True  # Can be destroyed by bullets
        
        # Scorpion-specific properties (large 64x64 enemy with ranged attack)
        if enemy_type.startswith('enemy_scorpion'):
            self.move_cooldown = 0  # Counts turns until next move (moves every 4-5 turns, slower than ants)
            self.rotation_delay = 0  # Delay before actual movement
            self.target_angle = 0  # The angle to rotate to before moving
            self.target_x = x
            self.target_y = y
            self.is_rotating = False
            self.is_moving = False
            self.size = 2  # 2x2 grid cells (64x64 pixels)
            # Attack properties
            self.attack_cooldown = 0  # Cooldown between attacks
            self.attack_charge_time = 0  # Time spent charging attack
            self.is_attacking = False  # Currently in attack animation
            self.attack_direction = Direction.RIGHT  # Direction to fire stinger
    
        # Beetle-specific properties (charges at player, launches larvae)
        if enemy_type.startswith('enemy_beetle'):
            self.attack_cooldown = 600  # Start with 10 second cooldown (first attack at 10s)
            self.attack_charge_time = 0  # Time spent in attack animation
            self.is_attacking = False  # Currently in attack animation
            self.is_moving = False  # Charging state
            self.target_x = x
            self.target_y = y
            self.previous_x = x  # For smooth rendering
            self.previous_y = y
            self.charge_cooldown = 0  # Cooldown after charging (prevents immediate re-charge)
            self.charge_dx = 0  # Direction of charge (per step)
            self.charge_dy = 0
            self.charge_steps_remaining = 0
            self.charge_target_x = x  # Final charge destination
            self.charge_target_y = y
            self.is_rotating = False  # Rotation state for scanning
            self.rotation_delay = 0  # Frames remaining in rotation
            self.target_angle = self.angle  # Target angle for rotation
            self.scan_timer = 120  # Timer for idle scanning behavior

        # Animation properties
        self.animation_frame = 0  # Current frame of animation
        self.animation_counter = 0  # Counter for animation timing
        
    def update(self, snake_body, level_walls, collectibles):
        """Update enemy behavior based on type"""
        if not self.alive:
            return
        
        if self.enemy_type.startswith('enemy_ant'):
            self._update_ant(snake_body, level_walls, collectibles)
        elif self.enemy_type.startswith('enemy_spider'):
            self._update_spider(snake_body, level_walls, collectibles)
        elif self.enemy_type.startswith('enemy_scorpion'):
            self._update_scorpion(snake_body, level_walls, collectibles)
        elif self.enemy_type.startswith('enemy_wasp'):
            self._update_wasp(snake_body, level_walls, collectibles)
        elif self.enemy_type.startswith('enemy_beetle'):
            self._update_beetle(snake_body, level_walls, collectibles)
        elif self.enemy_type == 'enemy_wall':
            # Enemy walls don't move, they're stationary obstacles
            pass
    
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
    
    def _update_scorpion(self, snake_body, level_walls, collectibles):
        """Scorpion AI: large 64x64 enemy that moves slowly and fires ranged stinger attacks
        The scorpion detects the player and fires a stinger in the direction it's facing"""
        snake_head = snake_body[0] if snake_body else None
        
        # Handle attack charging
        if self.is_attacking:
            self.attack_charge_time += 1
            # Attack animation lasts 30 frames (0.5 seconds at 60 FPS)
            if self.attack_charge_time >= 30:
                self.is_attacking = False
                self.attack_charge_time = 0
                self.attack_cooldown = random.randint(180, 300)  # 3-5 seconds between attacks
            return
        
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
                self.angle += angle_diff * 0.2  # Slow rotation
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
        
        # Handle movement interpolation (same speed as spiders - 5 frames)
        if self.is_moving:
            self.move_timer += 1
            if self.move_timer >= 5:  # Full movement complete in 5 frames (same as spiders)
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                self.move_timer = 0
                self.is_moving = False
                self.move_cooldown = random.randint(3, 4)  # Reset cooldown (3-4 turns)
                # Stop animation and return to frame 0
                self.animation_frame = 0
                self.animation_counter = 0
            return
        
        # Check if can attack (cooldown finished and player is visible)
        if self.attack_cooldown <= 0 and snake_head:
            # Check if player is in line of sight (same row or column)
            can_see_player = False
            attack_dir = None
            
            if self.grid_y == snake_head[1]:  # Same row
                if snake_head[0] > self.grid_x:
                    can_see_player = True
                    attack_dir = Direction.RIGHT
                elif snake_head[0] < self.grid_x:
                    can_see_player = True
                    attack_dir = Direction.LEFT
            elif self.grid_x == snake_head[0]:  # Same column
                if snake_head[1] > self.grid_y:
                    can_see_player = True
                    attack_dir = Direction.DOWN
                elif snake_head[1] < self.grid_y:
                    can_see_player = True
                    attack_dir = Direction.UP
            
            # Attack if player is visible
            if can_see_player and attack_dir:
                self.is_attacking = True
                self.attack_charge_time = 0
                self.attack_direction = attack_dir
                # Update angle to face attack direction
                angle_map = {Direction.RIGHT: 0, Direction.DOWN: 90, Direction.LEFT: 180, Direction.UP: 270}
                self.angle = angle_map[attack_dir]
                return  # Don't move while attacking
        
        # Count down cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
        
        # Time to choose a new direction and move
        self._choose_scorpion_move(snake_body, level_walls, collectibles)
    
    def _choose_scorpion_move(self, snake_body, level_walls, collectibles):
        """Choose a random adjacent square for scorpion to move to"""
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
            # Check bounds (scorpion is 2x2, so need extra space)
            if new_x < 0 or new_x >= GRID_WIDTH - 1 or new_y < 0 or new_y >= GRID_HEIGHT - 1:
                continue
            
            # Check walls (scorpion occupies 2x2 grid)
            blocked = False
            for dx in range(2):
                for dy in range(2):
                    check_pos = (new_x + dx, new_y + dy)
                    if check_pos in level_walls:
                        blocked = True
                        break
                    # Check collectibles
                    if any(pos == check_pos for pos, _ in collectibles):
                        blocked = True
                        break
                if blocked:
                    break
            
            if blocked:
                continue
            
            # This position is valid (even if snake is there)
            valid_moves.append((new_x, new_y, angle))
        
        # If no valid moves, stay in place
        if not valid_moves:
            self.move_cooldown = random.randint(4, 5)
            return
        
        # Choose a random valid move
        self.target_x, self.target_y, self.target_angle = random.choice(valid_moves)
        
        # Start rotation phase
        self.is_rotating = True
        self.rotation_delay = 5  # Slow rotation (5 frames)
    
    def _update_wasp(self, snake_body, level_walls, collectibles):
        """Wasp AI: continuously moves in a direction, only turns when hitting walls
        Faster than spiders, ignores player body, cannot be killed, always drawn on top"""
        
        # Wasps always animate - no speed limitation, update every frame
        # This is handled separately from the standard animation system
        # The animation frame counter will be updated externally at full speed
        
        # Handle movement interpolation (even faster than spiders - 3 frames)
        if self.is_moving:
            self.move_timer += 1
            if self.move_timer >= 3:  # Full movement complete in 3 frames (faster than spiders)
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                self.move_timer = 0
                self.previous_x = self.grid_x
                self.previous_y = self.grid_y
                
                # Immediately choose next move (continuous movement)
                self._choose_wasp_move(level_walls)
            return
    
    def _choose_wasp_move(self, level_walls):
        """Choose next move for wasp - continue in current direction or turn at wall"""
        # Calculate next position based on current angle
        next_x = self.grid_x
        next_y = self.grid_y
        
        if self.angle == 0:  # Right
            next_x += 1
        elif self.angle == 90:  # Down
            next_y += 1
        elif self.angle == 180:  # Left
            next_x -= 1
        elif self.angle == 270:  # Up
            next_y -= 1
        
        # Check if next position would be a wall or out of bounds
        hit_obstacle = False
        if next_x < 0 or next_x >= GRID_WIDTH or next_y < 0 or next_y >= GRID_HEIGHT:
            hit_obstacle = True
        elif (next_x, next_y) in level_walls:
            hit_obstacle = True
        
        if hit_obstacle:
            # Turn: try perpendicular directions first, then opposite
            possible_turns = []
            
            # Get perpendicular directions
            if self.angle == 0 or self.angle == 180:  # Moving horizontally
                perpendicular = [270, 90]  # Up, Down
            else:  # Moving vertically
                perpendicular = [0, 180]  # Right, Left
            
            # Try perpendicular directions
            for test_angle in perpendicular:
                test_x = self.grid_x
                test_y = self.grid_y
                if test_angle == 0:
                    test_x += 1
                elif test_angle == 90:
                    test_y += 1
                elif test_angle == 180:
                    test_x -= 1
                elif test_angle == 270:
                    test_y -= 1
                
                # Check if this direction is valid
                if 0 <= test_x < GRID_WIDTH and 0 <= test_y < GRID_HEIGHT:
                    if (test_x, test_y) not in level_walls:
                        possible_turns.append((test_angle, test_x, test_y))
            
            # If no perpendicular direction works, try opposite direction
            if not possible_turns:
                opposite_angle = (self.angle + 180) % 360
                test_x = self.grid_x
                test_y = self.grid_y
                if opposite_angle == 0:
                    test_x += 1
                elif opposite_angle == 90:
                    test_y += 1
                elif opposite_angle == 180:
                    test_x -= 1
                elif opposite_angle == 270:
                    test_y -= 1
                
                if 0 <= test_x < GRID_WIDTH and 0 <= test_y < GRID_HEIGHT:
                    if (test_x, test_y) not in level_walls:
                        possible_turns.append((opposite_angle, test_x, test_y))
            
            # Choose a turn direction
            if possible_turns:
                self.angle, next_x, next_y = random.choice(possible_turns)
                self.target_angle = self.angle
            else:
                # Stuck - stay in place (shouldn't happen in well-designed levels)
                return
        
        # Set target position and start moving
        self.target_x = next_x
        self.target_y = next_y
        self.is_moving = True
        self.move_timer = 0
        
        # Start rotation phase
        self.is_rotating = True
        self.rotation_delay = 5  # Slow rotation (5 frames)
    
    def _update_wasp(self, snake_body, level_walls, collectibles):
        """Wasp AI: continuously moves in a direction, only turns when hitting walls.
        Faster than spiders, ignores player body, cannot be killed."""
        
        if self.is_moving:
            self.move_timer += 1
            if self.move_timer >= 3:  # Wasps traverse a tile in 3 frames
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                self.move_timer = 0
                self.previous_x = self.grid_x
                self.previous_y = self.grid_y
                self._choose_wasp_move(level_walls)
            return
        
        # If not currently moving, pick the next move immediately
        self._choose_wasp_move(level_walls)
    
    def _choose_wasp_move(self, level_walls):
        """Choose next move for wasp - continue forward if possible, otherwise turn."""
        # Determine the preferred forward move based on current heading
        direction_vectors = {
            0: (1, 0),    # Right
            90: (0, 1),   # Down
            180: (-1, 0), # Left
            270: (0, -1), # Up
        }
        
        dx, dy = direction_vectors.get(self.angle, (1, 0))
        forward_x = self.grid_x + dx
        forward_y = self.grid_y + dy
        
        candidates = []
        
        def add_candidate(angle):
            vx, vy = direction_vectors[angle]
            cx = self.grid_x + vx
            cy = self.grid_y + vy
            if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT and (cx, cy) not in level_walls:
                candidates.append((angle, cx, cy))
        
        # Try forward direction first
        add_candidate(self.angle)
        
        # If forward is blocked, try perpendicular directions
        if not candidates:
            if self.angle in (0, 180):
                for angle in (270, 90):
                    add_candidate(angle)
            else:
                for angle in (0, 180):
                    add_candidate(angle)
        
        # If still no path, attempt to turn around
        if not candidates:
            add_candidate((self.angle + 180) % 360)
        
        if not candidates:
            return  # No valid moves available
        
        self.angle, self.target_x, self.target_y = random.choice(candidates)
        self.target_angle = self.angle
        self.is_moving = True
        self.move_timer = 0
        self.previous_x = self.grid_x
        self.previous_y = self.grid_y
    
    def _update_beetle(self, snake_body, level_walls, collectibles):
        """Beetle AI: charges at player if in same row/column, or launches larvae projectiles.
        Beetle attacks with larvae every 20 seconds."""
        snake_head = snake_body[0] if snake_body else None
        
        # Handle rotation (scanning for player)
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
                self.angle += angle_diff * 0.2  # Smooth rotation
                self.angle = self.angle % 360
            else:
                # Rotation complete
                self.angle = self.target_angle
                self.is_rotating = False
            return
        
        # Handle active charge movement first (continuous interpolation similar to wasps)
        if self.is_moving:
            self.move_timer += 1
            if self.move_timer >= 8:  # Advance one grid cell every 8 frames
                self.move_timer = 0
                
                # Complete movement to the current target cell
                self.grid_x = self.target_x
                self.grid_y = self.target_y
                
                if self.charge_steps_remaining > 0:
                    self.charge_steps_remaining -= 1
                    
                    if self.charge_steps_remaining > 0:
                        # Prepare interpolation for the next step in the charge
                        self.previous_x = self.grid_x
                        self.previous_y = self.grid_y
                        self.target_x = self.grid_x + self.charge_dx
                        self.target_y = self.grid_y + self.charge_dy
                    else:
                        # Charge complete - snap to final destination and set cooldown
                        self.grid_x = self.charge_target_x
                        self.grid_y = self.charge_target_y
                        self.target_x = self.grid_x
                        self.target_y = self.grid_y
                        self.previous_x = self.grid_x
                        self.previous_y = self.grid_y
                        self.is_moving = False
                        self.charge_cooldown = 180  # 3 second cooldown before next charge
                        print("Beetle finished charging at ({}, {})".format(self.grid_x, self.grid_y))
                else:
                    # Safety fallback - stop charging if no steps remain
                    self.is_moving = False
                    self.charge_cooldown = 180
            return
        
        # Handle larvae attack animation (beetle stays stationary during attack)
        if self.is_attacking:
            self.attack_charge_time += 1
            if self.attack_charge_time >= 60:
                self.is_attacking = False
                self.attack_charge_time = 0
                self.attack_cooldown = 1200
            return
        
        # Count down attack cooldown (but don't return - allow charging)
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            if self.attack_cooldown == 0:
                self.is_attacking = True
                self.attack_charge_time = 0
                print("Beetle starting larvae attack!")
                return
        
        # Count down charge cooldown
        if self.charge_cooldown > 0:
            self.charge_cooldown -= 1
            return
        
        # Check if beetle should initiate a charge
        if snake_head:
            head_x, head_y = snake_head
            same_row = self.grid_y == head_y
            same_col = self.grid_x == head_x
            
            if same_row or same_col:
                if same_row:
                    direction = 1 if head_x > self.grid_x else -1
                    charge_dx, charge_dy = direction, 0
                    steps = abs(head_x - self.grid_x)
                    target_x, target_y = head_x, self.grid_y
                    step_range = range(self.grid_x + direction, head_x, direction)
                    path_clear = all((x, self.grid_y) not in level_walls for x in step_range)
                else:
                    direction = 1 if head_y > self.grid_y else -1
                    charge_dx, charge_dy = 0, direction
                    steps = abs(head_y - self.grid_y)
                    target_x, target_y = self.grid_x, head_y
                    step_range = range(self.grid_y + direction, head_y, direction)
                    path_clear = all((self.grid_x, y) not in level_walls for y in step_range)
                
                if path_clear and steps > 0:
                    self.charge_dx = charge_dx
                    self.charge_dy = charge_dy
                    self.charge_steps_remaining = steps
                    self.charge_target_x = target_x
                    self.charge_target_y = target_y
                    self.previous_x = self.grid_x
                    self.previous_y = self.grid_y
                    self.target_x = self.grid_x + self.charge_dx
                    self.target_y = self.grid_y + self.charge_dy
                    self.move_timer = 0
                    self.is_moving = True
                    self.angle = 0 if charge_dx > 0 else (180 if charge_dx < 0 else (90 if charge_dy > 0 else 270))
                    print("Beetle charging at player from ({}, {}) to ({}, {})!".format(
                        self.grid_x, self.grid_y, self.charge_target_x, self.charge_target_y))
                    return
        
        # Idle behavior: rotate periodically to scan for player
        # Initialize scan timer if not set
        if not hasattr(self, 'scan_timer'):
            self.scan_timer = 120  # Start scanning after 2 seconds
        
        self.scan_timer -= 1
        if self.scan_timer <= 0:
            # Time to scan - rotate 90 degrees clockwise
            self.target_angle = (self.angle + 90) % 360
            self.is_rotating = True
            self.rotation_delay = 15  # Slower rotation for scanning (15 frames)
            self.scan_timer = 120  # Scan every 2 seconds
    
    def get_render_position(self):
        """Get interpolated position for rendering"""
        if self.is_moving:
            # Different enemies move at different speeds
            if self.enemy_type.startswith('enemy_wasp'):
                progress = self.move_timer / 3.0
            elif self.enemy_type.startswith('enemy_spider'):
                progress = self.move_timer / 5.0
            elif self.enemy_type.startswith('enemy_scorpion'):
                progress = self.move_timer / 5.0  # Same speed as spiders
            elif self.enemy_type.startswith('enemy_beetle'):
                progress = self.move_timer / 8.0
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
        # Exception: Beetles use current position since they charge across multiple cells
        if self.is_moving and not self.enemy_type.startswith('enemy_beetle'):
            base_x, base_y = self.target_x, self.target_y
        else:
            base_x, base_y = self.grid_x, self.grid_y
        
        # For scorpions (2x2), check all 4 grid cells
        if self.enemy_type.startswith('enemy_scorpion'):
            check_positions = [
                (base_x, base_y),
                (base_x + 1, base_y),
                (base_x, base_y + 1),
                (base_x + 1, base_y + 1)
            ]
        else:
            check_positions = [(base_x, base_y)]
        
        # Check collision with snake head
        for check_pos in check_positions:
            if check_pos == snake_head:
                return 'head'
        
        # Wasps ignore snake body (they fly over it) and cannot be killed
        if self.enemy_type.startswith('enemy_wasp'):
            return None  # Wasp only collides with head, never with body
        
        # Beetles only kill on head collision, but die when hitting snake body
        if self.enemy_type.startswith('enemy_beetle'):
            for check_pos in check_positions:
                if check_pos in snake_body[1:]:
                    return 'body'  # Beetle dies, player doesn't
            return None  # No collision
        
        # Check collision with snake body (excluding head) for non-wasp/non-beetle enemies
        for check_pos in check_positions:
            if check_pos in snake_body[1:]:
                return 'body'
        
        return None
