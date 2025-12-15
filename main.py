#!/usr/bin/env python3
import pygame
import json
import os
import random
import gc

# CRITICAL: Set SDL to grab input and prevent passthrough to EmulationStation
# This must be set BEFORE pygame.init()
os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '0'
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

from game_core import Snake, GameState, Difficulty, Direction, Particle, GifParticle, EggPiece, MusicManager, SoundManager, Enemy, Bullet, Spewtum, hue_shift_surface, hue_shift_frames, hue_shift_color, GamepadButton
from game_core import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, GAME_OFFSET_Y
from game_core import BLACK, WHITE, GREEN, DARK_GREEN, RED, YELLOW, ORANGE, GRAY, DARK_GRAY
from game_core import NEON_GREEN, NEON_LIME, NEON_PINK, NEON_CYAN, NEON_ORANGE, NEON_PURPLE, NEON_YELLOW, NEON_BLUE
from game_core import GRID_COLOR, HUD_BG, DARK_BG
from network_manager import NetworkManager, NetworkRole
from network_protocol import MessageType, create_input_message, create_game_state_message, create_game_start_message, create_game_end_message, create_player_assigned_message, create_lobby_state_message, create_return_to_lobby_message, create_host_shutdown_message, create_client_leave_message, create_player_disconnected_message, create_game_in_progress_message
from network_interpolation import NetworkInterpolator

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Save files directory (for Raspberry Pi deployment)
SAVE_DIR = '/home/pi/gamebird/saves/hungryHatchling'
# Ensure save directory exists
os.makedirs(SAVE_DIR, exist_ok=True)

pygame.init()
# Optimized audio settings for Raspberry Pi Zero 2W to prevent underruns/static
# - Lower frequency (22050) reduces CPU load for MP3 decoding
# - Larger buffer (8192) prevents stuttering on slow hardware
# - Mono output (1 channel) halves the audio processing load
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=8192)

FPS = 60

# MEMORY OPTIMIZATION STRATEGY
# Uses lazy loading approach - assets loaded only when needed:
# - Intro/outro sequences not preloaded (can be loaded on-demand if needed)
# - All animations load full frames for smooth playback
# - Game assets loaded at startup, can be extended to lazy load per-level
# Note: FPS stays at 60 because game logic is tied to frame rate

class SnakeGame:
    def __init__(self):
        # Scaling factor - 2x to scale 240x240 base to 480x480 display
        self.scale = 2
        
        # Create the actual display window (scaled up)
        self.display = pygame.display.set_mode((SCREEN_WIDTH * self.scale, SCREEN_HEIGHT * self.scale))
        
        # Create the render surface (native resolution)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Snake Game")
        pygame.mouse.set_visible(False)  # Hide mouse cursor
        
        # CRITICAL: Grab input to prevent passthrough to EmulationStation
        pygame.event.set_grab(True)
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 16)  # Scaled for 240x240 base resolution
        self.font_medium = pygame.font.Font(None, 24)  # Scaled for 240x240 base resolution
        self.font_large = pygame.font.Font(None, 33)  # Scaled for 240x240 base resolution
        
        # Load background image
        try:
            bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'bg.png')
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background = None
            print("Warning: bg.png not found, using default background")
        
        # Load title screen image
        try:
            title_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'title.png')
            self.title_screen = pygame.image.load(title_path).convert()
            self.title_screen = pygame.transform.scale(self.title_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.title_screen = None
            print("Warning: title.png not found, using default title screen")
        
        # Load bonus food image (speed boost apple)
        try:
            bonus_path = os.path.join(SCRIPT_DIR, 'img', 'bonus.png')
            self.bonus_img = pygame.image.load(bonus_path).convert_alpha()
            self.bonus_img = pygame.transform.scale(self.bonus_img, (GRID_SIZE, GRID_SIZE))
        except:
            self.bonus_img = None
            print("Warning: bonus.png not found, using default bonus graphic")
        
        # Load bad apple image (speed reduction)
        try:
            bad_apple_path = os.path.join(SCRIPT_DIR, 'img', 'badApple.png')
            self.bad_apple_img = pygame.image.load(bad_apple_path).convert_alpha()
            self.bad_apple_img = pygame.transform.scale(self.bad_apple_img, (GRID_SIZE, GRID_SIZE))
        except:
            self.bad_apple_img = None
            print("Warning: badApple.png not found, using default bad apple graphic")
        
        # Load wall image for adventure mode
        try:
            wall_path = os.path.join(SCRIPT_DIR, 'img', 'wall1.png')
            self.wall_img = pygame.image.load(wall_path).convert_alpha()
            self.wall_img = pygame.transform.scale(self.wall_img, (GRID_SIZE, GRID_SIZE))
        except:
            self.wall_img = None
            print("Warning: wall1.png not found, using default wall graphic")
        
        # Load isotope image (shooting ability power-up)
        try:
            isotope_path = os.path.join(SCRIPT_DIR, 'img', 'isotope.png')
            self.isotope_img = pygame.image.load(isotope_path).convert_alpha()
            self.isotope_img = pygame.transform.scale(self.isotope_img, (GRID_SIZE, GRID_SIZE))
        except:
            self.isotope_img = None
            print("Warning: isotope.png not found, using default isotope graphic")
        
        # Load game over screen image
        try:
            gameover_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'gameOver.png')
            self.gameover_screen = pygame.image.load(gameover_path).convert()
            self.gameover_screen = pygame.transform.scale(self.gameover_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.gameover_screen = None
            print("Warning: gameOver.png not found, using default game over screen")
        
        # Load high score screen image
        try:
            highscore_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'highScore.png')
            self.highscore_screen = pygame.image.load(highscore_path).convert()
            self.highscore_screen = pygame.transform.scale(self.highscore_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.highscore_screen = None
            print("Warning: highScore.png not found, using default high score screen")
        
        # Load difficulty selection screen image
        try:
            difficulty_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'notitle.png')
            self.difficulty_screen = pygame.image.load(difficulty_path).convert()
            self.difficulty_screen = pygame.transform.scale(self.difficulty_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.difficulty_screen = None
            print("Warning: notitle.png not found, using default difficulty screen")
        
        # Load splash screen image
        try:
            splash_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'splashAMS.png')
            self.splash_screen = pygame.image.load(splash_path).convert()
            self.splash_screen = pygame.transform.scale(self.splash_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.splash_screen = None
            print("Warning: splashAMS.png not found, skipping splash screen")
        
        # Load intro sequence images (7 images)
        self.intro_images = []
        try:
            intro_dir = os.path.join(SCRIPT_DIR, 'img', 'Intro')
            for i in range(1, 8):  # intro1.jpg through intro7.jpg
                intro_path = os.path.join(intro_dir, f'intro{i}.jpg')
                if os.path.exists(intro_path):
                    img = pygame.image.load(intro_path).convert()
                    img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    self.intro_images.append(img)
            print(f"Loaded {len(self.intro_images)} intro images (~320KB total)")
        except Exception as e:
            print(f"Warning: Could not load intro images: {e}")
            self.intro_images = []
        
        # Load outro sequence images (4 images)
        self.outro_images = []
        try:
            outro_dir = os.path.join(SCRIPT_DIR, 'img', 'outro')
            for i in range(1, 5):  # outro1.jpg through outro4.jpg
                outro_path = os.path.join(outro_dir, f'outro{i}.jpg')
                if os.path.exists(outro_path):
                    img = pygame.image.load(outro_path).convert()
                    # Image 4 is tall and pans - only scale width, preserve height
                    if i == 4:
                        # Load at original size (will be scaled to width during rendering)
                        # This preserves the tall aspect ratio for panning
                        pass  # Don't scale, keep original size
                    else:
                        # Images 1-3: Scale to screen size
                        img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    self.outro_images.append(img)
            print(f"Loaded {len(self.outro_images)} outro images (~100KB total)")
        except Exception as e:
            print(f"Warning: Could not load outro images: {e}")
            self.outro_images = []
        
        # Load Tweetrix logo
        try:
            tweetrix_path = os.path.join(SCRIPT_DIR, 'img', 'Tweetrix.png')
            self.tweetrix_logo = pygame.image.load(tweetrix_path).convert_alpha()
            # Scale logo to reasonable size (e.g., 50px wide for 240x240, maintain aspect ratio)
            logo_width = 50
            aspect_ratio = self.tweetrix_logo.get_height() / self.tweetrix_logo.get_width()
            logo_height = int(logo_width * aspect_ratio)
            self.tweetrix_logo = pygame.transform.scale(self.tweetrix_logo, (logo_width, logo_height))
        except:
            self.tweetrix_logo = None
            print("Warning: Tweetrix.png not found")
        
        # Load trophy icon for achievements
        try:
            trophy_path = os.path.join(SCRIPT_DIR, 'img', 'trophy.png')
            self.trophy_icon = pygame.image.load(trophy_path).convert_alpha()
            # Scale trophy to reasonable size
            trophy_size = 16
            self.trophy_icon = pygame.transform.scale(self.trophy_icon, (trophy_size, trophy_size))
        except:
            self.trophy_icon = None
            print("Warning: trophy.png not found")
        
        # Load lock icon for locked content
        try:
            lock_path = os.path.join(SCRIPT_DIR, 'img', 'lock.png')
            self.lock_icon = pygame.image.load(lock_path).convert_alpha()
            self.lock_icon = pygame.transform.scale(self.lock_icon, (10, 10))
        except:
            self.lock_icon = None
            print("Warning: lock.png not found")
        
        # Load hatchling head icon for selected music tracks
        try:
            hatchling_path = os.path.join(SCRIPT_DIR, 'img', 'HatchlingHead1.gif')
            self.hatchling_head_icon = pygame.image.load(hatchling_path).convert_alpha()
            self.hatchling_head_icon = pygame.transform.scale(self.hatchling_head_icon, (10, 10))
        except:
            self.hatchling_head_icon = None
            print("Warning: HatchlingHead1.gif not found")
        
        # Load multiplayer setup background
        try:
            multi_bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'multiBG.png')
            self.multi_bg = pygame.image.load(multi_bg_path).convert()
            self.multi_bg = pygame.transform.scale(self.multi_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.multi_bg = None
            print("Warning: multiBG.png not found, using default background")
        
        # Load egg images
        try:
            egg_path = os.path.join(SCRIPT_DIR, 'img', 'egg.png')
            self.egg_img = pygame.image.load(egg_path).convert_alpha()
            self.egg_img = pygame.transform.scale(self.egg_img, (GRID_SIZE * 2, GRID_SIZE * 2))
        except:
            self.egg_img = None
            print("Warning: egg.png not found")
        
        # Load player-colored egg icons for lives display (small 10x10 icons for 240x240)
        self.player_egg_icons = []
        for player_num in range(1, 5):
            try:
                egg_icon_path = os.path.join(SCRIPT_DIR, 'img', 'egg{}.png'.format(player_num))
                egg_icon = pygame.image.load(egg_icon_path).convert_alpha()
                egg_icon = pygame.transform.scale(egg_icon, (10, 10))
                self.player_egg_icons.append(egg_icon)
            except:
                self.player_egg_icons.append(None)
                print("Warning: egg{}.png not found".format(player_num))
        
        # Load egg piece images
        self.egg_piece_imgs = []
        for i in range(1, 5):
            try:
                piece_path = os.path.join(SCRIPT_DIR, 'img', 'eggPiece{}.png'.format(i))
                piece_img = pygame.image.load(piece_path).convert_alpha()
                piece_img = pygame.transform.scale(piece_img, (GRID_SIZE, GRID_SIZE))
                self.egg_piece_imgs.append(piece_img)
            except:
                print("Warning: eggPiece{}.png not found".format(i))
        
        # Load player-specific egg images for multiplayer respawns
        self.player_egg_imgs = []
        for player_num in range(1, 5):  # Players 1-4
            try:
                egg_path = os.path.join(SCRIPT_DIR, 'img', 'egg{}.png'.format(player_num))
                player_egg_img = pygame.image.load(egg_path).convert_alpha()
                player_egg_img = pygame.transform.scale(player_egg_img, (GRID_SIZE * 2, GRID_SIZE * 2))
                self.player_egg_imgs.append(player_egg_img)
            except Exception as e:
                self.player_egg_imgs.append(None)
                print("Warning: egg{}.png not found: {}".format(player_num, e))
        
        # Load snake graphics (scaled larger than grid for visual overlap)
        self.snake_scale_factor = 1.25  # Scale up by 25% for overlap effect
        self.snake_sprite_size = int(GRID_SIZE * self.snake_scale_factor)
        self.snake_offset = (GRID_SIZE - self.snake_sprite_size) // 2  # Center the sprite
        
        # Load snake body images for all 4 players
        self.snake_body_imgs = []  # List of body images for each player
        
        # Always load all 4 player graphics for multiplayer support
        player_range = range(1, 5)
        
        for player_num in player_range:  # Players 1-4
            try:
                if player_num == 1:
                    body_path = os.path.join(SCRIPT_DIR, 'img', 'HatchlingBody.png')
                else:
                    # Try standard name first, then .png.png (in case of naming issue)
                    body_path = os.path.join(SCRIPT_DIR, 'img', 'HatchlingBody{}.png'.format(player_num))
                    if not os.path.exists(body_path):
                        body_path = os.path.join(SCRIPT_DIR, 'img', 'HatchlingBody{}.png.png'.format(player_num))
                
                body_img = pygame.image.load(body_path).convert_alpha()
                body_img = pygame.transform.scale(body_img, (self.snake_sprite_size, self.snake_sprite_size))
                self.snake_body_imgs.append(body_img)
            except Exception as e:
                self.snake_body_imgs.append(None)
                print("Warning: HatchlingBody{}.png not found: {}".format(player_num if player_num > 1 else '', e))
        
        # Note: All 4 player graphics are always loaded for multiplayer support
        
        # Keep original for backwards compatibility
        self.snake_body_img = self.snake_body_imgs[0] if self.snake_body_imgs else None
        
        # Load glowing body image for isotope power-up
        try:
            glow_path = os.path.join(SCRIPT_DIR, 'img', 'HatchlingBodyGlow.png')
            glow_img = pygame.image.load(glow_path).convert_alpha()
            self.snake_body_glow_img = pygame.transform.scale(glow_img, (self.snake_sprite_size, self.snake_sprite_size))
        except Exception as e:
            self.snake_body_glow_img = None
            print("Warning: HatchlingBodyGlow.png not found: {}".format(e))
        
        # Load snake head animations (GIF) for all 4 players
        self.snake_head_frames_all = []  # List of frame lists for each player
        
        for player_num in player_range:  # Players 1-4
            try:
                from PIL import Image
                head_path = os.path.join(SCRIPT_DIR, 'img', 'HatchlingHead{}.gif'.format(player_num))
                frames = []
                
                # Load GIF frames using PIL
                gif = Image.open(head_path)
                frame_count = 0
                try:
                    while True:
                        # Convert PIL image to pygame surface
                        frame = gif.copy().convert('RGBA')
                        pygame_frame = pygame.image.frombytes(
                            frame.tobytes(), frame.size, frame.mode
                        ).convert_alpha()
                        pygame_frame = pygame.transform.scale(pygame_frame, (self.snake_sprite_size, self.snake_sprite_size))
                        frames.append(pygame_frame)
                        frame_count += 1
                        gif.seek(frame_count)
                except EOFError:
                    pass  # End of frames
                
                self.snake_head_frames_all.append(frames)
                print("Loaded {} frames for player {} head animation".format(len(frames), player_num))
            except Exception as e:
                self.snake_head_frames_all.append([])
                print("Warning: HatchlingHead{}.gif not found or could not be loaded: {}".format(player_num, e))
        
        # Keep original for backwards compatibility
        self.snake_head_frames = self.snake_head_frames_all[0] if self.snake_head_frames_all else []
        self.head_frame_index = 0
        self.head_animation_speed = 5  # Change frame every N game frames
        self.head_animation_counter = 0
        
        # Load particle effect animation (GIF)
        try:
            from PIL import Image
            particle_path = os.path.join(SCRIPT_DIR, 'img', 'particlesRed.gif')
            self.particle_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(particle_path)
            frame_count = 0
            try:
                while True:
                    
                    # Get the current frame and convert to RGBA
                    frame = gif.copy().convert('RGBA')
                    
                    # Convert PIL image to pygame surface
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to 50% of original size
                    scaled_width = frame.size[0] // 2
                    scaled_height = frame.size[1] // 2
                    pygame_frame = pygame.transform.scale(pygame_frame, (scaled_width, scaled_height))
                    self.particle_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            print("Loaded {} frames for particle animation".format(len(self.particle_frames)))
        except Exception as e:
            self.particle_frames = []
            print("Warning: particlesRed.gif not found or could not be loaded: {}".format(e))
        
        # Load white particle effect animation (GIF) - for snake death
        try:
            from PIL import Image
            particle_white_path = os.path.join(SCRIPT_DIR, 'img', 'particlesWhite.gif')
            self.particle_white_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(particle_white_path)
            frame_count = 0
            try:
                while True:
                    
                    # Get the current frame and convert to RGBA
                    frame = gif.copy().convert('RGBA')
                    
                    # Convert PIL image to pygame surface
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to 50% of original size
                    scaled_width = frame.size[0] // 2
                    scaled_height = frame.size[1] // 2
                    pygame_frame = pygame.transform.scale(pygame_frame, (scaled_width, scaled_height))
                    self.particle_white_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass
            
            print("Loaded {} frames for white particle animation".format(len(self.particle_white_frames)))
        except Exception as e:
            self.particle_white_frames = []
            print("Warning: particlesWhite.gif not found or could not be loaded: {}".format(e))
        
        # Load rainbow particle effect animation (GIF) - for bonus collection
        try:
            from PIL import Image
            particle_rainbow_path = os.path.join(SCRIPT_DIR, 'img', 'particlesRainbow.gif')
            self.particle_rainbow_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(particle_rainbow_path)
            frame_count = 0
            try:
                while True:
                    
                    # Get the current frame and convert to RGBA
                    frame = gif.copy().convert('RGBA')
                    
                    # Convert PIL image to pygame surface
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to 50% of original size
                    scaled_width = frame.size[0] // 2
                    scaled_height = frame.size[1] // 2
                    pygame_frame = pygame.transform.scale(pygame_frame, (scaled_width, scaled_height))
                    self.particle_rainbow_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass
            
            print("Loaded {} frames for rainbow particle animation".format(len(self.particle_rainbow_frames)))
        except Exception as e:
            self.particle_rainbow_frames = []
            print("Warning: particlesRainbow.gif not found or could not be loaded: {}".format(e))
        
        # Load yellow particle effect animation (GIF) - for coin/diamond collection
        try:
            from PIL import Image
            particle_yellow_path = os.path.join(SCRIPT_DIR, 'img', 'particlesYellow.gif')
            self.particle_yellow_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(particle_yellow_path)
            frame_count = 0
            try:
                while True:
                    
                    # Get the current frame and convert to RGBA
                    frame = gif.copy().convert('RGBA')
                    
                    # Convert PIL image to pygame surface
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to 50% of original size
                    scaled_width = frame.size[0] // 2
                    scaled_height = frame.size[1] // 2
                    pygame_frame = pygame.transform.scale(pygame_frame, (scaled_width, scaled_height))
                    self.particle_yellow_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass
            
            print("Loaded {} frames for yellow particle animation".format(len(self.particle_yellow_frames)))
        except Exception as e:
            self.particle_yellow_frames = []
            print("Warning: particlesYellow.gif not found or could not be loaded: {}".format(e))
        
        # Load worm (food) animation (GIF)
        try:
            from PIL import Image
            worm_path = os.path.join(SCRIPT_DIR, 'img', 'worm.png')
            self.worm_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(worm_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.worm_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            self.worm_frame_index = 0
            self.worm_animation_speed = 5  # Change frame every N game frames
            self.worm_animation_counter = 0
            print("Loaded {} frames for worm animation".format(len(self.worm_frames)))
        except Exception as e:
            self.worm_frames = []
            print("Warning: worm.png not found or could not be loaded: {}".format(e))
        
        # Load ant enemy animation (GIF)
        try:
            from PIL import Image
            ant_path = os.path.join(SCRIPT_DIR, 'img', 'ant.gif')
            self.ant_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(ant_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.ant_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            self.ant_frame_index = 0
            self.ant_animation_speed = 1  # Change frame every N game frames (fast animation)
            self.ant_animation_counter = 0
            print("Loaded {} frames for ant animation".format(len(self.ant_frames)))
        except Exception as e:
            self.ant_frames = []
            print("Warning: ant.gif not found or could not be loaded: {}".format(e))
        
        # Load spider enemy animation (GIF)
        try:
            from PIL import Image
            spider_path = os.path.join(SCRIPT_DIR, 'img', 'spider.gif')
            self.spider_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(spider_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.spider_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            self.spider_frame_index = 0
            self.spider_animation_speed = 1  # Change frame every N game frames (fast animation)
            self.spider_animation_counter = 0
            print("Loaded {} frames for spider animation".format(len(self.spider_frames)))
        except Exception as e:
            self.spider_frames = []
            print("Warning: spider.gif not found or could not be loaded: {}".format(e))
        
        # Load wasp enemy animation (GIF) - animates at 24 FPS
        try:
            from PIL import Image
            wasp_path = os.path.join(SCRIPT_DIR, 'img', 'wasp.gif')
            self.wasp_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(wasp_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.wasp_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            self.wasp_frame_index = 0
            # Fast animation for wasps - update every frame for rapid wing movement
            self.wasp_animation_speed = 1  # Change frame every game frame (~60 FPS)
            self.wasp_animation_counter = 0
            print("Loaded {} frames for wasp animation".format(len(self.wasp_frames)))
        except Exception as e:
            self.wasp_frames = []
            print("Warning: wasp.gif not found or could not be loaded: {}".format(e))
        
        # Load scorpion enemy animation (GIF) - 64x64 size for large enemy
        try:
            from PIL import Image
            scorpion_path = os.path.join(SCRIPT_DIR, 'img', 'scorpion.gif')
            self.scorpion_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(scorpion_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to 64x64 (2x grid size for large enemy)
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE * 2, GRID_SIZE * 2))
                    self.scorpion_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            self.scorpion_frame_index = 0
            self.scorpion_animation_speed = 1  # Change frame every N game frames
            self.scorpion_animation_counter = 0
            print("Loaded {} frames for scorpion animation".format(len(self.scorpion_frames)))
        except Exception as e:
            self.scorpion_frames = []
            print("Warning: scorpion.gif not found or could not be loaded: {}".format(e))
        
        # Load scorpion attack animation (GIF) - projectile stinger
        try:
            from PIL import Image
            scorpion_attack_path = os.path.join(SCRIPT_DIR, 'img', 'scorpionAttack.gif')
            self.scorpion_attack_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(scorpion_attack_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size (projectile is normal sized)
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.scorpion_attack_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            print("Loaded {} frames for scorpion attack animation".format(len(self.scorpion_attack_frames)))
        except Exception as e:
            self.scorpion_attack_frames = []
            print("Warning: scorpionAttack.gif not found or could not be loaded: {}".format(e))
        
        # Load beetle animations
        try:
            from PIL import Image
            beetle_path = os.path.join(SCRIPT_DIR, 'img', 'beetle.gif')
            self.beetle_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(beetle_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.beetle_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            print("Loaded {} frames for beetle animation".format(len(self.beetle_frames)))
        except Exception as e:
            self.beetle_frames = []
            print("Warning: beetle.gif not found or could not be loaded: {}".format(e))
        
        # Load beetle attack animation
        try:
            from PIL import Image
            beetle_attack_path = os.path.join(SCRIPT_DIR, 'img', 'beetleAttack.gif')
            self.beetle_attack_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(beetle_attack_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.beetle_attack_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            print("Loaded {} frames for beetle attack animation".format(len(self.beetle_attack_frames)))
        except Exception as e:
            self.beetle_attack_frames = []
            print("Warning: beetleAttack.gif not found or could not be loaded: {}".format(e))
        
        # Load beetle vulnerable/open animation
        try:
            from PIL import Image
            beetle_open_path = os.path.join(SCRIPT_DIR, 'img', 'beetleOpen.gif')
            self.beetle_open_frames = []
            
            # Load GIF frames using PIL
            gif = Image.open(beetle_open_path)
            frame_count = 0
            try:
                while True:
                    
                    # Convert PIL image to pygame surface
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    # Scale to fit grid size
                    pygame_frame = pygame.transform.scale(pygame_frame, (GRID_SIZE, GRID_SIZE))
                    self.beetle_open_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            print("Loaded {} frames for beetle open animation".format(len(self.beetle_open_frames)))
        except Exception as e:
            self.beetle_open_frames = []
            print("Warning: beetleOpen.gif not found or could not be loaded: {}".format(e))
        
        # Load larvae projectile image
        try:
            larvae_path = os.path.join(SCRIPT_DIR, 'img', 'larvae.png')
            larvae_img = pygame.image.load(larvae_path).convert_alpha()
            # Scale to fit grid size
            larvae_img = pygame.transform.scale(larvae_img, (GRID_SIZE, GRID_SIZE))
            self.beetle_larvae_frames = [larvae_img]  # Single frame, stored as list for consistency
            print("Loaded larvae projectile image")
        except Exception as e:
            self.beetle_larvae_frames = []
            print("Warning: larvae.png not found or could not be loaded: {}".format(e))
        
        # Load boss animations
        self.boss_animations = {}
        boss_anim_names = ['wormBossEmerges', 'wormBossIdle', 'wormBossAttack', 'wormBossDeath1', 'wormBossDeath3']
        for anim_name in boss_anim_names:
            try:
                from PIL import Image
                boss_path = os.path.join(SCRIPT_DIR, 'img', 'boss', '{}.gif'.format(anim_name))
                frames = []
                gif = Image.open(boss_path)
                frame_count = 0
                try:
                    while True:
                        
                        frame = gif.copy().convert('RGBA')
                        pygame_frame = pygame.image.frombytes(
                            frame.tobytes(), frame.size, frame.mode
                        ).convert_alpha()
                        # Scale boss from 256x256 to 128x128 for 240x240 base resolution
                        pygame_frame = pygame.transform.scale(pygame_frame, (128, 128))
                        frames.append(pygame_frame)
                        frame_count += 1
                        gif.seek(frame_count)
                except EOFError:
                    pass
                self.boss_animations[anim_name] = frames
                print("Loaded {} frames for {} animation".format(len(frames), anim_name))
            except Exception as e:
                self.boss_animations[anim_name] = []
                print("Warning: {}.gif not found or could not be loaded: {}".format(anim_name, e))
        
        # Load static boss death images (PNG)
        boss_static_names = ['bossWormDeath2', 'bossWormDeath4']
        for img_name in boss_static_names:
            try:
                img_path = os.path.join(SCRIPT_DIR, 'img', 'boss', '{}.png'.format(img_name))
                img = pygame.image.load(img_path).convert_alpha()
                # Scale boss from 256x256 to 128x128 for 240x240 base resolution
                img = pygame.transform.scale(img, (128, 128))
                # Store as single-frame "animation" for consistency
                self.boss_animations[img_name] = [img]
                print("Loaded static image: {}".format(img_name))
            except Exception as e:
                self.boss_animations[img_name] = []
                print("Warning: {}.png not found or could not be loaded: {}".format(img_name, e))
        
        # Load spewtum projectile animation
        self.spewtum_frames = []
        try:
            from PIL import Image
            spewtum_path = os.path.join(SCRIPT_DIR, 'img', 'boss', 'bossSpewtum.gif')
            gif = Image.open(spewtum_path)
            frame_count = 0
            try:
                while True:
                    
                    frame = gif.copy().convert('RGBA')
                    pygame_frame = pygame.image.frombytes(
                        frame.tobytes(), frame.size, frame.mode
                    ).convert_alpha()
                    self.spewtum_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass
            print("Loaded {} frames for bossSpewtum animation".format(len(self.spewtum_frames)))
        except Exception as e:
            print("Warning: bossSpewtum.gif not found or could not be loaded: {}".format(e))
        
        # Load Frog Boss assets
        try:
            frog_boss_path = os.path.join(SCRIPT_DIR, 'img', 'boss', 'frogBoss.png')
            self.frog_boss_img = pygame.image.load(frog_boss_path).convert_alpha()
            # Scale to 200% size (4x4 grid cells instead of 2x2)
            self.frog_boss_img = pygame.transform.scale(self.frog_boss_img, (GRID_SIZE * 4, GRID_SIZE * 4))
            print("Loaded frogBoss.png")
        except Exception as e:
            print("Warning: frogBoss.png not found: {}".format(e))
            self.frog_boss_img = None
        
        try:
            frog_boss_top_path = os.path.join(SCRIPT_DIR, 'img', 'boss', 'frogBossTop.png')
            self.frog_boss_top_img = pygame.image.load(frog_boss_top_path).convert_alpha()
            # Scale to same size as frog boss (4x4 grid cells)
            self.frog_boss_top_img = pygame.transform.scale(self.frog_boss_top_img, (GRID_SIZE * 4, GRID_SIZE * 4))
            print("Loaded frogBossTop.png")
        except Exception as e:
            print("Warning: frogBossTop.png not found: {}".format(e))
            self.frog_boss_top_img = None
        
        try:
            frog_tongue_path = os.path.join(SCRIPT_DIR, 'img', 'boss', 'frogTongue.png')
            self.frog_tongue_img = pygame.image.load(frog_tongue_path).convert_alpha()
            # Tongue segment is 1 grid cell
            self.frog_tongue_img = pygame.transform.scale(self.frog_tongue_img, (GRID_SIZE, GRID_SIZE))
            print("Loaded frogTongue.png")
        except Exception as e:
            self.frog_tongue_img = None
            print("Warning: frogTongue.png not found: {}".format(e))
        
        # Load bad snake graphics for boss minions
        try:
            bad_head_path = os.path.join(SCRIPT_DIR, 'img', 'badSnakeHead.png')
            self.bad_snake_head_img = pygame.image.load(bad_head_path).convert_alpha()
            self.bad_snake_head_img = pygame.transform.scale(self.bad_snake_head_img, (self.snake_sprite_size, self.snake_sprite_size))
        except Exception as e:
            self.bad_snake_head_img = None
            print("Warning: badSnakeHead.png not found: {}".format(e))
        
        try:
            bad_body_path = os.path.join(SCRIPT_DIR, 'img', 'badSnakeBody.png')
            self.bad_snake_body_img = pygame.image.load(bad_body_path).convert_alpha()
            self.bad_snake_body_img = pygame.transform.scale(self.bad_snake_body_img, (self.snake_sprite_size, self.snake_sprite_size))
        except Exception as e:
            self.bad_snake_body_img = None
            print("Warning: badSnakeBody.png not found: {}".format(e))
        
        # Load enemy snake graphics
        try:
            enemy_head_path = os.path.join(SCRIPT_DIR, 'img', 'snakeHead.png')
            self.enemy_snake_head_img = pygame.image.load(enemy_head_path).convert_alpha()
            self.enemy_snake_head_img = pygame.transform.scale(self.enemy_snake_head_img, (self.snake_sprite_size, self.snake_sprite_size))
        except Exception as e:
            self.enemy_snake_head_img = None
            print("Warning: snakeHead.png not found: {}".format(e))
        
        try:
            enemy_body_path = os.path.join(SCRIPT_DIR, 'img', 'snakeBody.png')
            self.enemy_snake_body_img = pygame.image.load(enemy_body_path).convert_alpha()
            self.enemy_snake_body_img = pygame.transform.scale(self.enemy_snake_body_img, (self.snake_sprite_size, self.snake_sprite_size))
        except Exception as e:
            self.enemy_snake_body_img = None
            print("Warning: snakeBody.png not found: {}".format(e))
        
        # Boss battle state
        self.boss_active = False
        self.boss_data = None
        self.boss_spawn_timer = 0  # Timer in seconds for boss events
        self.boss_spawned = False
        self.boss_current_animation = None
        self.boss_animation_frame = 0
        self.boss_animation_counter = 0
        self.boss_animation_speed = 5  # Frames per game frame (higher = slower)
        self.boss_position = (0, 0)  # Boss position in pixels
        self.boss_animation_loop = True  # Whether current animation loops
        self.screen_shake_intensity = 0
        self.screen_shake_offset = (0, 0)
        self.boss_minions = []  # List of boss minion snakes
        self.enemy_snakes = []  # List of enemy snakes (non-boss)
        self.boss_minion_respawn_timers = {}  # Dict of minion_id -> respawn_timer
        self.boss_attack_timer = 0  # Timer for periodic boss attacks
        self.boss_attack_interval = 1200  # Start at 20 seconds (1200 frames at 60 FPS)
        self.boss_attack_interval_min = 180  # Fastest attack speed: 3 seconds
        self.boss_attack_interval_max = 1200  # Slowest attack speed: 20 seconds
        self.boss_is_attacking = False  # Whether boss is currently in attack animation
        self.spewtums = []  # List of active spewtum projectiles
        self.boss_health = 50  # Boss health
        self.boss_max_health = 50  # Boss maximum health
        self.boss_damage_flash = 0  # Timer for red flash when boss is hit
        self.boss_damage_sound_cooldown = 0  # Cooldown to prevent damage sounds from overlapping
        self.boss_super_attack_thresholds = [0.75, 0.5, 0.25]  # Health % thresholds for super attacks
        self.boss_super_attacks_used = set()  # Track which thresholds have been used
        self.boss_defeated = False  # Whether boss has been defeated
        self.boss_death_delay = 0  # Delay before level completion after death animation
        self.boss_death_phase = 0  # Current death animation phase (0=not started, 1-5=phases)
        self.player_frozen = False  # Whether player is frozen (during boss death sequence)
        self.boss_death_timer = 0  # Timer for death phase 2 (static image hold)
        self.boss_death_particle_timer = 0  # Timer for spawning particles during phase 3
        self.boss_slide_offset_y = 0  # Vertical offset for boss sliding during death
        self.boss_slide_timer = 0  # Timer for boss slide (4 seconds = 240 frames)
        
        # Frog Boss state variables
        self.frog_state = 'waiting'  # States: 'waiting', 'falling', 'landed', 'jumping', 'airborne'
        self.frog_position = [GRID_WIDTH // 2, 2]  # Grid position (can be fractional during animation)
        self.frog_shadow_position = [GRID_WIDTH // 2, 2]  # Shadow grid position
        self.frog_fall_timer = 0  # Animation timer for falling
        self.frog_initial_spawn_timer = 0  # Timer for 2-second delay before initial spawn
        self.frog_jump_timer = 0  # Timer between jumps
        self.frog_airborne_timer = 0  # How long frog has been in the air
        self.frog_tongue_segments = []  # List of tongue segment positions [(x, y), ...]
        self.frog_tongue_extending = False  # Whether tongue is extending
        self.frog_tongue_retracting = False  # Whether tongue is retracting
        self.frog_tongue_timer = 0  # Timer for tongue animation
        self.frog_tongue_direction = (0, -1)  # Direction of tongue extension (dx, dy)
        self.frog_jump_count = 0  # Number of jumps performed
        self.frog_tracking_player = False  # Whether frog is tracking player for targeted attack
        self.frog_is_invulnerable = False  # Whether frog is invulnerable (during jump)
        self.frog_rotation_angle = 0  # Current angle frog is facing (interpolated)
        self.frog_target_rotation = 0  # Target angle for smooth rotation
        self.frog_tongue_stuck_timer = 0  # Timer for tongue staying extended
        self.frog_tongue_sticking = False  # Whether tongue is stuck at full extension
        
        # Load UI icons for multiplayer lobby
        # Star rating icons for difficulty
        self.icon_size = 24  # Halved from 48 for 240x240 resolution
        self.star_icons = {}
        star_names = ['starEmpty', 'easy', 'medium', 'hard', 'brutal']
        for star_name in star_names:
            try:
                star_path = os.path.join(SCRIPT_DIR, 'img', '{}.png'.format(star_name))
                star_img = pygame.image.load(star_path).convert_alpha()
                self.star_icons[star_name] = pygame.transform.scale(star_img, (self.icon_size, self.icon_size))
            except Exception as e:
                self.star_icons[star_name] = None
                print("Warning: {}.png not found: {}".format(star_name, e))
        
        # Input device icons
        try:
            keyboard_path = os.path.join(SCRIPT_DIR, 'img', 'keyboard.png')
            self.keyboard_icon = pygame.image.load(keyboard_path).convert_alpha()
            self.keyboard_icon = pygame.transform.scale(self.keyboard_icon, (self.icon_size, self.icon_size))
        except Exception as e:
            self.keyboard_icon = None
            print("Warning: keyboard.png not found: {}".format(e))
        
        try:
            gamepad_path = os.path.join(SCRIPT_DIR, 'img', 'gamepad.png')
            self.gamepad_icon = pygame.image.load(gamepad_path).convert_alpha()
            self.gamepad_icon = pygame.transform.scale(self.gamepad_icon, (self.icon_size, self.icon_size))
        except Exception as e:
            self.gamepad_icon = None
            print("Warning: gamepad.png not found: {}".format(e))
        
        try:
            robot_path = os.path.join(SCRIPT_DIR, 'img', 'robot.png')
            self.robot_icon = pygame.image.load(robot_path).convert_alpha()
            self.robot_icon = pygame.transform.scale(self.robot_icon, (self.icon_size, self.icon_size))
        except Exception as e:
            self.robot_icon = None
            print("Warning: robot.png not found: {}".format(e))
        
        # Set initial state to splash screen if available
        if self.splash_screen:
            self.state = GameState.SPLASH
            self.splash_start_time = pygame.time.get_ticks()
            self.splash_duration = 3000  # 3 seconds in milliseconds
        else:
            self.state = GameState.MENU
        
        # Achievement notification system
        self.achievement_notification_active = False
        self.achievement_notification_name = ""
        self.achievement_notification_timer = 0
        self.achievement_selection = 0  # For achievements menu
        
        # Multiplayer support
        self.is_multiplayer = False
        self.is_spectator = False  # For clients who join mid-game
        self.num_players = 1
        self.snakes = [Snake(player_id=0)]  # List of snakes for multiplayer
        self.snake = self.snakes[0]  # For backwards compatibility
        
        # Player colors (hue shifts in degrees): Blue (default), Red, Green, Yellow
        self.player_hue_shifts = [0, 120, 240, 60]  # Player 1, 2, 3, 4
        self.player_names = ["Player 1", "Player 2", "Player 3", "Player 4"]
        self.player_colors = [NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_YELLOW]
        
        # Controller mapping
        self.player_controllers = []  # List of (controller_type, controller_index) tuples
        self.detect_controllers()
        
        # Multiplayer menu
        self.multiplayer_menu_selection = 0
        self.multiplayer_menu_options = ["Same Screen", "Network Game", "Back"]
        
        # Network multiplayer
        self.network_manager = NetworkManager()
        self.network_interpolator = NetworkInterpolator(buffer_time_ms=80)  # Lag compensation
        self.is_network_game = False  # True when playing over network
        self.network_menu_selection = 0
        self.network_menu_options = ["Host Game", "Join Game", "Back"]
        self.network_host_ip = ""  # For displaying host IP
        self.network_join_ip = list("192.168.1.1")  # IP as list of chars for digit-by-digit editing
        self.network_join_ip_cursor = len(self.network_join_ip) - 1  # Current digit position (0-indexed)
        self.network_status_message = ""  # Status messages for connection
        self.discovered_servers = []  # List of (name, ip, port) from LAN discovery
        self.server_selection = 0  # Currently selected server in list
        
        # Multiplayer level selection
        self.multiplayer_level_selection = 0
        self.multiplayer_levels = []  # Will be loaded from multi_*.json files
        self.multiplayer_level_previews = {}  # Cache for level wall previews
        self.load_multiplayer_levels()
        
        # Multiplayer lobby settings
        self.lobby_selection = 0  # Which setting is selected
        self.lobby_settings = {
            'rounds': 3,
            'lives': 3,
            'item_frequency': 1,  # 0=Low, 1=Normal, 2=High
            'cpu_difficulty': 1,  # 0=Easy, 1=Medium, 2=Hard, 3=Brutal
            'level': 0,  # Index into multiplayer_levels list
        }
        self.level_select_return_state = None  # Where to return after level select
        # Player slot types: 'player', 'cpu', 'off'
        self.player_slots = ['player', 'player', 'cpu', 'cpu']  # Default setup
        # Egg respawn state for dead players
        self.respawning_players = {}  # {player_id: {'pos': (x,y), 'timer': int, 'direction': Direction or None}}
        
        # Food system - list of (position, type) tuples
        # Types: 'worm' (regular), 'apple' (speed up), 'black_apple' (slow down)
        self.food_items = []  # List of (pos, type)
        self.food_pos = None  # Legacy for single player
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.score = 0
        self.level = 1
        self.lives = 3
        self.fruits_eaten_this_level = 0  # Track fruits eaten for leveling up
        self.move_timer = 0
        self.particles = []
        self.egg_pieces = []  # Track flying egg shell pieces
        self.bullets = []  # Track player bullets from isotope ability
        self.scorpion_stingers = []  # Track scorpion projectiles
        self.beetle_larvae = []  # Track beetle larvae projectiles
        self.game_over_timer = 0
        self.game_over_delay = 180  # 3 seconds at 60 FPS
        self.multiplayer_end_timer = 0  # Timer for delay after last player dies in multiplayer
        self.respawn_timer = 0  # Timer for delay before respawning in adventure mode
        self.respawn_delay = 60  # 1 second at 60 FPS
        
        self.joystick = None
        self.joystick_has_hat = False
        self.axis_was_neutral = True  # Track if axis was in neutral position
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            # No need to call init() - it's deprecated and joystick is auto-initialized
            print("Gamepad connected: {}".format(self.joystick.get_name()))
            # Check if joystick has a hat (D-pad)
            if self.joystick.get_numhats() > 0:
                self.joystick_has_hat = True
                print("Joystick has {} hat(s)".format(self.joystick.get_numhats()))
            else:
                print("Joystick has no hats, will use axes/buttons only")
                print("Axes: {}, Buttons: {}".format(self.joystick.get_numaxes(), self.joystick.get_numbuttons()))
        
        self.music_manager = MusicManager()
        self.music_manager.play_theme()  # Start with theme music for menus
        
        self.sound_manager = SoundManager()
        
        self.high_scores = self.load_high_scores()
        self.level_scores = self.load_level_scores()  # Dictionary: level_number -> best_score
        self.unlocked_levels = self.load_unlocked_levels()  # Set of unlocked level numbers
        self.player_name = ['A', 'A', 'A']
        self.name_index = 0
        self.current_hint = ""  # Will be set when entering high score entry
        self.keyboard_selection = [0, 0]
        self.keyboard_layout = [
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'],
            ['U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3'],
            ['4', '5', '6', '7', '8', '9', '<', ' ', ' ', '>']
        ]
        
        self.menu_selection = 0
        self.menu_options = ["Single Player", "Multiplayer", "Extras", "Quit"]
        
        # Single player submenu
        self.single_player_selection = 0
        self.single_player_options = ["Adventure", "Endless", "Back"]
        
        # Extras menu
        self.extras_menu_selection = 0
        self.extras_menu_options = ["Achievements", "Music Player", "Level Editor", "Credits", "Back"]
        
        # Music Player
        self.music_player_tracks = []
        self.music_player_selection = 0
        self.music_player_playing = False
        self.music_player_current_track = None
        self.load_music_tracks()
        
        # Game Unlocks (for music, achievements, etc.)
        self.game_unlocks = {}
        self.load_game_unlocks()
        
        # Adventure mode
        self.game_mode = "endless"  # "endless" or "adventure"
        self.current_level_data = None
        self.level_walls = []  # List of (x, y) wall positions
        self.worms_collected = 0
        self.worms_required = 0
        self.adventure_level_selection = 0  # Which level is selected in level select
        self.total_levels = 32  # 30 regular + 2 bonus
        
        self.difficulty = Difficulty.MEDIUM  # Default difficulty
        self.difficulty_selection = 1  # Start on Medium
        self.difficulty_options = ["Easy", "Medium", "Hard"]
        
        # Create hue-shifted graphics for all players
        self.create_player_graphics()
        
        self.spawn_food()
        
        # Force garbage collection after loading all assets to free temporary memory
        gc.collect()
        print("Asset loading complete - garbage collection done")
    
    def load_high_scores(self):
        try:
            highscores_path = os.path.join(SAVE_DIR, 'highscores.json')
            if os.path.exists(highscores_path):
                with open(highscores_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_high_scores(self):
        try:
            highscores_path = os.path.join(SAVE_DIR, 'highscores.json')
            with open(highscores_path, 'w') as f:
                json.dump(self.high_scores, f)
        except:
            pass
    
    def load_music_tracks(self):
        """Load all music tracks from the sound/music directory."""
        music_dir = os.path.join(SCRIPT_DIR, 'sound', 'music')
        if os.path.exists(music_dir):
            # Get all mp3 files
            files = [f for f in os.listdir(music_dir) if f.endswith('.ogg')]
            # Sort them alphabetically
            files.sort()
            # Store as tuples of (display_name, full_path, filename)
            for filename in files:
                # Remove .ogg extension for display
                display_name = filename[:-4]
                full_path = os.path.join(music_dir, filename)
                self.music_player_tracks.append((display_name, full_path, filename))
    
    def load_game_unlocks(self):
        """Load game unlocks from JSON file."""
        try:
            unlocks_path = os.path.join(SAVE_DIR, 'game_unlocks.json')
            if os.path.exists(unlocks_path):
                with open(unlocks_path, 'r') as f:
                    self.game_unlocks = json.load(f)
            else:
                # Create default unlocks if file doesn't exist
                self.game_unlocks = {"music": {}}
                self.save_game_unlocks()
        except Exception as e:
            print(f"Warning: Could not load game_unlocks.json: {e}")
            self.game_unlocks = {"music": {}}
    
    def save_game_unlocks(self):
        """Save game unlocks to JSON file."""
        try:
            unlocks_path = os.path.join(SAVE_DIR, 'game_unlocks.json')
            with open(unlocks_path, 'w') as f:
                json.dump(self.game_unlocks, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save game_unlocks.json: {e}")
    
    def is_music_unlocked(self, filename):
        """Check if a music track is unlocked."""
        if 'music' not in self.game_unlocks:
            return True
        if filename not in self.game_unlocks['music']:
            return True
        return self.game_unlocks['music'][filename].get('unlocked', True)
    
    def get_music_cost(self, filename):
        """Get the coin cost of a music track."""
        if 'music' not in self.game_unlocks:
            return 0
        if filename not in self.game_unlocks['music']:
            return 0
        return self.game_unlocks['music'][filename].get('cost', 0)
    
    def unlock_music(self, filename):
        """Unlock a music track by spending coins."""
        cost = self.get_music_cost(filename)
        if self.total_coins >= cost:
            self.total_coins -= cost
            if 'music' in self.game_unlocks and filename in self.game_unlocks['music']:
                self.game_unlocks['music'][filename]['unlocked'] = True
                self.save_game_unlocks()
                self.save_unlocked_levels()  # Save updated coin count
                return True
        return False
    
    def is_achievement_unlocked(self, achievement_id):
        """Check if an achievement is unlocked."""
        if 'achievements' not in self.game_unlocks:
            return False
        if str(achievement_id) not in self.game_unlocks['achievements']:
            return False
        return self.game_unlocks['achievements'][str(achievement_id)].get('unlocked', False)
    
    def unlock_achievement(self, achievement_id):
        """Unlock an achievement and show notification."""
        # Check if already unlocked
        if self.is_achievement_unlocked(achievement_id):
            return False
        
        # Unlock the achievement
        if 'achievements' not in self.game_unlocks:
            return False
        
        achievement_id_str = str(achievement_id)
        if achievement_id_str not in self.game_unlocks['achievements']:
            return False
        
        # Mark as unlocked
        self.game_unlocks['achievements'][achievement_id_str]['unlocked'] = True
        self.save_game_unlocks()
        
        # Show notification
        achievement_name = self.game_unlocks['achievements'][achievement_id_str].get('name', 'Achievement')
        self.show_achievement_notification(achievement_name)
        
        # Play sound
        self.sound_manager.play('achievement')
        
        return True
    
    def show_achievement_notification(self, achievement_name):
        """Display achievement unlocked notification."""
        self.achievement_notification_active = True
        self.achievement_notification_name = achievement_name
        self.achievement_notification_timer = 300  # 5 seconds at 60 FPS
    
    def get_achievement_list(self):
        """Get a list of all achievements with their status."""
        achievements = []
        if 'achievements' in self.game_unlocks:
            for achievement_id, achievement_data in self.game_unlocks['achievements'].items():
                achievements.append({
                    'id': achievement_id,
                    'name': achievement_data.get('name', 'Unknown'),
                    'description': achievement_data.get('description', ''),
                    'unlocked': achievement_data.get('unlocked', False)
                })
        # Sort by ID
        achievements.sort(key=lambda x: int(x['id']))
        return achievements
    
    def add_high_score(self, name, score):
        self.high_scores.append({'name': name, 'score': score})
        self.high_scores.sort(key=lambda x: x['score'], reverse=True)
        self.high_scores = self.high_scores[:10]  # Keep top 10
        self.save_high_scores()
    
    def is_high_score(self, score):
        return len(self.high_scores) < 10 or score > self.high_scores[-1]['score']
    
    def load_level_scores(self):
        """Load level-specific high scores for adventure mode"""
        try:
            level_scores_path = os.path.join(SAVE_DIR, 'level_scores.json')
            if os.path.exists(level_scores_path):
                with open(level_scores_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}  # Dictionary: level_number -> best_score
    
    def save_level_scores(self):
        """Save level-specific high scores"""
        try:
            level_scores_path = os.path.join(SAVE_DIR, 'level_scores.json')
            with open(level_scores_path, 'w') as f:
                json.dump(self.level_scores, f, indent=2)
        except:
            pass
    
    def update_level_score(self, level_number, score):
        """Update the high score for a specific level, returns True if new high score"""
        level_key = str(level_number)
        if level_key not in self.level_scores or score > self.level_scores[level_key]:
            self.level_scores[level_key] = score
            self.save_level_scores()
            return True
        return False
    
    def get_level_high_score(self, level_number):
        """Get the high score for a specific level"""
        level_key = str(level_number)
        return self.level_scores.get(level_key, 0)
    
    def load_unlocked_levels(self):
        """Load which levels are unlocked, total coins, and intro status"""
        try:
            unlock_path = os.path.join(SAVE_DIR, 'level_unlocks.json')
            if os.path.exists(unlock_path):
                with open(unlock_path, 'r') as f:
                    data = json.load(f)
                    self.total_coins = data.get('total_coins', 0)
                    self.intro_seen = data.get('intro', False) or False  # null or missing becomes False
                    return set(data.get('unlocked', [1]))  # Default to level 1 unlocked
        except:
            pass
        self.total_coins = 0
        self.intro_seen = False
        return {1}  # Only level 1 unlocked by default
    
    def save_unlocked_levels(self):
        """Save which levels are unlocked, total coins, and intro status"""
        try:
            unlock_path = os.path.join(SAVE_DIR, 'level_unlocks.json')
            with open(unlock_path, 'w') as f:
                data = {
                    'intro': getattr(self, 'intro_seen', False),
                    'unlocked': sorted(list(self.unlocked_levels)),
                    'total_coins': getattr(self, 'total_coins', 0)
                }
                json.dump(data, f, indent=2)
        except:
            pass
    
    def load_multiplayer_levels(self):
        """Load all multiplayer level files (multi_01.json to multi_12.json)"""
        self.multiplayer_levels = []
        levels_dir = os.path.join(SCRIPT_DIR, 'levels')
        
        # Try to load multi_01 through multi_12
        for i in range(1, 13):
            level_file = 'multi_{:02d}.json'.format(i)
            level_path = os.path.join(levels_dir, level_file)
            
            if os.path.exists(level_path):
                try:
                    with open(level_path, 'r') as f:
                        level_data = json.load(f)
                        self.multiplayer_levels.append({
                            'number': i,
                            'name': level_data.get('name', 'Level {}'.format(i)),
                            'background': level_data.get('background_image', 'bg.png'),
                            'walls': level_data.get('walls', []),
                            'filename': level_file
                        })
                except Exception as e:
                    print("Warning: Could not load {}: {}".format(level_file, e))
        
        print("Loaded {} multiplayer levels".format(len(self.multiplayer_levels)))
    
    def load_selected_multiplayer_level(self):
        """Load the currently selected multiplayer level data"""
        level_idx = self.lobby_settings.get('level', 0)
        if level_idx < 0 or level_idx >= len(self.multiplayer_levels):
            self.current_level_data = None
            return
        
        selected_level = self.multiplayer_levels[level_idx]
        level_path = os.path.join(SCRIPT_DIR, 'levels', selected_level['filename'])
        try:
            with open(level_path, 'r') as f:
                self.current_level_data = json.load(f)
            print(f"Loaded multiplayer level: {selected_level['name']}")
        except Exception as e:
            print(f"Error loading multiplayer level: {e}")
            self.current_level_data = None
    
    def generate_level_preview(self, level_index):
        """Generate a small preview surface of level walls for display"""
        if level_index < 0 or level_index >= len(self.multiplayer_levels):
            return None
        
        # Check cache first
        if level_index in self.multiplayer_level_previews:
            return self.multiplayer_level_previews[level_index]
        
        level = self.multiplayer_levels[level_index]
        walls = level['walls']
        
        # Create small preview surface (scale down 15x15 grid to fit in preview area)
        preview_size = 90  # Preview area size in pixels (halved from 180)
        cell_size = preview_size // 15  # Each grid cell size
        
        preview_surface = pygame.Surface((preview_size, preview_size))
        preview_surface.fill(BLACK)  # Dark background
        
        # Draw grid lines (subtle)
        grid_color = (30, 30, 30)
        for x in range(0, preview_size, cell_size):
            pygame.draw.line(preview_surface, grid_color, (x, 0), (x, preview_size), 1)
        for y in range(0, preview_size, cell_size):
            pygame.draw.line(preview_surface, grid_color, (0, y), (preview_size, y), 1)
        
        # Draw walls
        wall_color = NEON_CYAN
        for wall in walls:
            x = wall['x']
            y = wall['y']
            wall_rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
            pygame.draw.rect(preview_surface, wall_color, wall_rect)
            # Add subtle border
            pygame.draw.rect(preview_surface, NEON_BLUE, wall_rect, 1)
        
        # Cache the preview
        self.multiplayer_level_previews[level_index] = preview_surface
        return preview_surface
    
    def unlock_level(self, level_number):
        """Unlock a specific level"""
        self.unlocked_levels.add(level_number)
        self.save_unlocked_levels()
    
    def is_level_unlocked(self, level_number):
        """Check if a level is unlocked"""
        return level_number in self.unlocked_levels
    
    def detect_controllers(self):
        """Detect available input devices and assign them to players."""
        self.player_controllers = []
        self.joysticks = []
        
        # Detect all connected gamepads
        num_joysticks = pygame.joystick.get_count()
        for i in range(num_joysticks):
            joystick = pygame.joystick.Joystick(i)
            self.joysticks.append(joystick)
            print("Gamepad {} connected: {}".format(i, joystick.get_name()))
        
        # Assignment logic:
        # If keyboard detected (always true on PC), player 1 = keyboard
        # If no keyboard expected (gamebird), player 1 = first gamepad
        # Subsequent players get remaining gamepads
        
        # We assume keyboard is available unless we detect we're running on a handheld
        has_keyboard = True
        
        if has_keyboard and num_joysticks > 0:
            # PC mode: Keyboard + gamepads
            self.player_controllers.append(('keyboard', 0))
            for i in range(min(3, num_joysticks)):  # Up to 3 more players with gamepads
                self.player_controllers.append(('gamepad', i))
        elif num_joysticks > 0:
            # Handheld mode: Only gamepads
            for i in range(min(4, num_joysticks)):
                self.player_controllers.append(('gamepad', i))
        else:
            # Fallback: Only keyboard
            self.player_controllers.append(('keyboard', 0))
        
        print("Controller mapping: {}".format(self.player_controllers))
    
    def create_player_graphics(self):
        """Load graphics for each player (up to 4 players)."""
        # Store graphics for each player: [body_img, head_frames]
        self.player_graphics = []
        
        for player_id in range(4):
            # Use pre-loaded player-specific graphics
            if player_id < len(self.snake_body_imgs):
                body_img = self.snake_body_imgs[player_id]
            else:
                body_img = None
            
            if player_id < len(self.snake_head_frames_all):
                head_frames = self.snake_head_frames_all[player_id]
            else:
                head_frames = []
            
            self.player_graphics.append((body_img, head_frames))
        
        print("Created graphics for {} players".format(len(self.player_graphics)))
    
    def spawn_food(self):
        if self.is_multiplayer:
            # In multiplayer, spawn worms
            self.spawn_food_item('worm')
        else:
            # Single player - use legacy system
            while True:
                # Spawn food within playable area (avoid 1-grid-cell border)
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                if (x, y) not in self.snake.body:
                    self.food_pos = (x, y)
                    break
    
    def spawn_adventure_food(self):
        """Spawn a worm in adventure mode, avoiding occupied positions"""
        # Don't spawn worms during boss battles
        if hasattr(self, 'boss_active') and self.boss_active:
            return
        
        occupied_positions = set()
        occupied_positions.update(self.snake.body)
        occupied_positions.update(self.level_walls)
        
        # Add existing food items to avoid spawning on top of them
        occupied_positions.update([pos for pos, _ in self.food_items])
        
        # Add boss minion positions
        if hasattr(self, 'boss_minions'):
            for minion in self.boss_minions:
                if minion.alive:
                    occupied_positions.update(minion.body)
        
        # Add enemy snake positions
        if hasattr(self, 'enemy_snakes'):
            for enemy_snake in self.enemy_snakes:
                if enemy_snake.alive:
                    occupied_positions.update(enemy_snake.body)
        
        # Add enemy positions (including enemy walls from super attacks)
        if hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.alive:
                    occupied_positions.add((enemy.grid_x, enemy.grid_y))
        
        # Try to find a valid spawn position
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            
            # Avoid lower right quadrant during boss battles (boss zone)
            if hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned:
                # Lower right quadrant: x >= 8 and y >= 8 (roughly half of 15x15 grid)
                if x >= 8 and y >= 8:
                    continue  # Skip this position, try again
            
            if (x, y) not in occupied_positions:
                self.food_items.append(((x, y), 'worm'))
                print("Spawned new worm at ({}, {})".format(x, y))
                return
        
        # Debug: Show why spawning failed
        available_spaces = (GRID_WIDTH - 2) * (GRID_HEIGHT - 2)
        if hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned:
            # Subtract boss zone (roughly 7x7 = 49 spaces)
            available_spaces -= 49
        occupied_count = len(occupied_positions)
        print("Warning: Could not find valid position to spawn worm after 100 attempts")
        print("  Occupied positions: {}, Available spaces (approx): {}".format(occupied_count, available_spaces))
    
    def find_random_unoccupied_position(self):
        """Find a random unoccupied position for boss egg respawning."""
        occupied_positions = set()
        occupied_positions.update(self.snake.body)
        occupied_positions.update(self.level_walls)
        
        # Add existing food items
        occupied_positions.update([pos for pos, _ in self.food_items])
        
        # Add boss minion positions
        if hasattr(self, 'boss_minions'):
            for minion in self.boss_minions:
                if minion.alive:
                    occupied_positions.update(minion.body)
        
        # Add enemy positions
        if hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.alive:
                    occupied_positions.add((enemy.grid_x, enemy.grid_y))
        
        # Add frog boss position if present
        if hasattr(self, 'boss_type') and self.boss_type == 'frog' and hasattr(self, 'frog_position'):
            frog_x = int(self.frog_position[0])
            frog_y = int(self.frog_position[1])
            # Frog occupies 4x4 grid cells
            for dx in range(4):
                for dy in range(4):
                    occupied_positions.add((frog_x + dx, frog_y + dy))
        
        # Try to find a valid spawn position
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(2, GRID_WIDTH - 3)  # Leave extra margin for 2x2 egg
            y = random.randint(2, GRID_HEIGHT - 3)
            
            # Check if position and surrounding 2x2 area are clear (for egg size)
            position_clear = True
            for dx in range(2):
                for dy in range(2):
                    if (x + dx, y + dy) in occupied_positions:
                        position_clear = False
                        break
                if not position_clear:
                    break
            
            if position_clear:
                return (x, y)
        
        # Fallback to center if no position found
        print("Warning: Could not find random unoccupied position, using center")
        return (GRID_WIDTH // 2, GRID_HEIGHT // 2)
    
    def spawn_boss_minions(self):
        """Spawn 2 hard-AI boss minion snakes for the boss battle"""
        # Clear any existing minions
        self.boss_minions = []
        self.boss_minion_respawn_timers = {}
        
        # Spawn positions: top-right and bottom-right (near the boss)
        minion_positions = [
            (GRID_WIDTH - 3, 3),  # Top right
            (GRID_WIDTH - 3, GRID_HEIGHT - 4)  # Bottom right
        ]
        
        minion_directions = [
            Direction.LEFT,  # Face left (toward player)
            Direction.LEFT
        ]
        
        for i in range(2):
            minion = Snake(player_id=100 + i)  # Use high IDs to distinguish from regular players
            minion.is_cpu = True
            minion.cpu_difficulty = 2  # Hard difficulty (0=Easy, 1=Medium, 2=Hard, 3=Brutal)
            minion.reset(spawn_pos=minion_positions[i], direction=minion_directions[i])
            minion.alive = True
            minion.is_boss_minion = True  # Mark as boss minion
            # Initialize movement tracking for smooth interpolation
            minion.move_timer = 0
            minion.last_move_interval = 16
            minion.previous_body = minion.body.copy()
            self.boss_minions.append(minion)
            print("Spawned boss minion {} at {}".format(i+1, minion_positions[i]))
    
    def respawn_boss_minion(self, minion_index):
        """Respawn a dead boss minion"""
        if minion_index >= len(self.boss_minions):
            return
        
        minion = self.boss_minions[minion_index]
        
        # Respawn positions
        minion_positions = [
            (GRID_WIDTH - 3, 3),  # Top right
            (GRID_WIDTH - 3, GRID_HEIGHT - 4)  # Bottom right
        ]
        
        # Reset the minion
        minion.reset(spawn_pos=minion_positions[minion_index], direction=Direction.LEFT)
        minion.alive = True
        minion.is_cpu = True
        minion.cpu_difficulty = 2  # Hard difficulty
        # Initialize movement tracking for smooth interpolation
        minion.move_timer = 0
        minion.last_move_interval = 16
        minion.previous_body = minion.body.copy()
        
        # Remove from respawn timer
        if minion_index in self.boss_minion_respawn_timers:
            del self.boss_minion_respawn_timers[minion_index]
        
        print("Boss minion {} respawned at {}".format(minion_index + 1, minion_positions[minion_index]))
    
    def spawn_boss_spewtums(self):
        """Spawn spewtum projectiles from the boss position.
        Normally fires 1 large (2x) spewtum, but occasionally (20% chance) fires 3 smaller spewtums.
        """
        if not self.spewtum_frames:
            print("Warning: No spewtum frames loaded, cannot spawn spewtums")
            return
        
        import math
        import random
        
        # Safety check: Don't spawn if player has no body (died)
        if not self.snake.body or len(self.snake.body) == 0:
            print("Boss attack skipped: player has no body")
            return
        
        # Boss position is in bottom right (128x128 sprite for 240x240 resolution)
        boss_center_x = self.boss_position[0] + 64  # Center of 128px boss
        boss_center_y = self.boss_position[1] + 64  # Center of 128px boss
        
        # Player head position (convert to pixel coordinates)
        player_head = self.snake.body[0]
        player_x = player_head[0] * GRID_SIZE + GRID_SIZE // 2
        player_y = player_head[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
        
        # Calculate direction from boss to player
        dx = player_x - boss_center_x
        dy = player_y - boss_center_y
        
        # Calculate base angle to player (in radians)
        base_angle_rad = math.atan2(dy, dx)
        
        # 20% chance for rare attack (3 small spewtums), 80% chance for normal attack (1 large spewtum)
        is_rare_attack = random.random() < 0.2
        
        if is_rare_attack:
            # Rare attack: 3 smaller spewtums in a spread pattern
            spread_angles = [-15, 0, 15]  # Degrees of spread
            speed = 2.5
            scale = 1.0  # Normal size
            print("Boss rare attack: 3 small spewtums")
        else:
            # Normal attack: 1 large spewtum aimed directly at player
            spread_angles = [0]  # No spread, just center
            speed = 2.0  # Slightly slower for the larger projectile
            scale = 2.0  # Double size
            print("Boss normal attack: 1 large spewtum")
        
        for i, spread_deg in enumerate(spread_angles):
            # Convert spread to radians and add to base angle
            spread_rad = math.radians(spread_deg)
            angle_rad = base_angle_rad + spread_rad
            
            # Calculate velocity components
            velocity_x = math.cos(angle_rad) * speed
            velocity_y = math.sin(angle_rad) * speed
            
            # Calculate rotation angle for sprite (pygame rotates counter-clockwise)
            # Convert to degrees and adjust for sprite orientation
            rotation_angle = -math.degrees(angle_rad)  # Negative for pygame rotation
            
            # Spawn position offset a bit from boss center towards firing direction
            spawn_offset = 40
            spewtum_x = boss_center_x + math.cos(angle_rad) * spawn_offset
            spewtum_y = boss_center_y + math.sin(angle_rad) * spawn_offset
            
            spewtum = Spewtum(spewtum_x, spewtum_y, self.spewtum_frames, velocity_x, velocity_y, rotation_angle, scale)
            self.spewtums.append(spewtum)
            print("Spawned spewtum {} at ({:.1f}, {:.1f}) with angle {:.1f}°, velocity ({:.2f}, {:.2f}), scale {:.1f}x".format(
                i + 1, spewtum_x, spewtum_y, math.degrees(angle_rad), velocity_x, velocity_y, scale))
        
        # Play attack sound
        self.sound_manager.play('shoot')
    
    def spawn_boss_super_attack(self):
        """Boss super attack: spawns 3 destroyable enemy walls around the arena"""
        import random
        
        print("BOSS SUPER ATTACK: Spawning enemy walls!")
        
        # Create a small pattern of enemy walls (just 3 walls)
        wall_positions = []
        
        # Spawn 3 random walls in strategic positions
        attempts = 0
        max_attempts = 50
        
        while len(wall_positions) < 3 and attempts < max_attempts:
            attempts += 1
            
            # Pick a random position, avoiding edges and center
            x = random.randint(2, GRID_WIDTH - 3)
            y = random.randint(2, GRID_HEIGHT - 3)
            pos = (x, y)
            
            # Make sure not spawning on player, existing walls, or too close to boss
            # Boss is in bottom right corner, so avoid that area
            if (pos not in self.snake.body and 
                pos not in self.level_walls and
                pos not in wall_positions and
                x < GRID_WIDTH - 4 and  # Keep away from boss area
                y < GRID_HEIGHT - 4):
                wall_positions.append(pos)
        
        # Create enemy wall objects
        for pos in wall_positions:
            # Check if position is clear (no snake, no existing enemies, no food items)
            existing_enemy_positions = [(e.grid_x, e.grid_y) for e in self.enemies if e.alive]
            food_positions = [food_pos for food_pos, _ in self.food_items]
            
            if (pos not in self.snake.body and 
                pos not in existing_enemy_positions and
                pos not in food_positions):
                
                enemy_wall = Enemy(pos[0], pos[1], 'enemy_wall')
                self.enemies.append(enemy_wall)
        
        # Play sound effect (will fallback if specific sound not available)
        self.sound_manager.play('shoot')  # Using shoot as placeholder
        
        # Create screen shake effect (will last for 30 frames = 0.5 seconds)
        self.screen_shake_intensity = 5
        self.screen_shake_timer = 30  # Frames to shake
        
        print("Spawned {} enemy walls in super attack pattern".format(len([e for e in self.enemies if e.enemy_type == 'enemy_wall' and e.alive])))
    
    def update_frog_boss(self):
        """Update Frog Boss behavior: falling entrance, jumping, shadow movement, tongue attacks"""
        
        # Waiting state: Initial 2-second delay before first spawn
        if self.frog_state == 'waiting':
            self.frog_initial_spawn_timer += 1
            if self.frog_initial_spawn_timer >= 120:  # 2 seconds at 60 FPS
                # Start falling sequence from top of level
                self.frog_state = 'falling'
                self.frog_shadow_position = [GRID_WIDTH // 2, 2]  # Top of level
                self.frog_position = [GRID_WIDTH // 2, -5]  # Start above screen
                self.frog_fall_timer = 0
                print("Frog Boss: Initial spawn - Shadow appears at top ({}, {})".format(self.frog_shadow_position[0], self.frog_shadow_position[1]))
            return  # Don't process other states while waiting
        
        # Entrance sequence: Frog falls from sky
        if self.frog_state == 'falling':
            self.frog_fall_timer += 1
            
            # For initial entrance (jump count == 0), position already set by waiting state
            # For subsequent falls, position already set by airborne state
            if self.frog_fall_timer == 1:
                print("Frog Boss: Falling to position ({}, {})".format(self.frog_shadow_position[0], self.frog_shadow_position[1]))
            
            # Frog falls down over 60 frames (1 second)
            if self.frog_fall_timer <= 60:
                # Interpolate from above screen to shadow position
                progress = self.frog_fall_timer / 60.0
                self.frog_position[1] = -5 + (self.frog_shadow_position[1] + 5) * progress
            else:
                # Landing complete
                self.frog_position = self.frog_shadow_position[:]
                self.frog_state = 'landed'
                self.frog_fall_timer = 0
                self.frog_is_invulnerable = False
                self.frog_landed_timer = 0  # Start delay timer
                
                # Calculate target rotation angle immediately so frog can start rotating
                if len(self.snake.body) > 0:
                    player_head = self.snake.body[0]
                    frog_center_x = self.frog_position[0] + 2
                    frog_center_y = self.frog_position[1] + 2
                    dx = player_head[0] - frog_center_x
                    dy = player_head[1] - frog_center_y
                    import math
                    angle_rad = math.atan2(dy, dx)
                    angle_deg = math.degrees(angle_rad)
                    if angle_deg < 0:
                        angle_deg += 360
                    self.frog_target_rotation = angle_deg
                else:
                    self.frog_target_rotation = 0
                
                print("Frog Boss: Landed at position", self.frog_position)
        
        # Landed state: Tongue attack or preparing to jump
        elif self.frog_state == 'landed':
            # Smoothly interpolate rotation angle towards target
            self.interpolate_frog_rotation()
            
            # Wait 1 second after landing before starting tongue attack
            if not self.frog_tongue_extending and not self.frog_tongue_retracting and not self.frog_tongue_sticking:
                if self.frog_landed_timer < 60:  # 1 second delay (60 frames)
                    self.frog_landed_timer += 1
                elif self.frog_landed_timer == 60:
                    # Start tongue attack after 1 second
                    self.start_frog_tongue_attack()
                    self.frog_landed_timer += 1  # Move past 60 to avoid repeated calls
                else:
                    # Wait for tongue to finish, then prepare to jump
                    self.frog_jump_timer += 1
                    if self.frog_jump_timer >= 180:  # 3 seconds after tongue retracts
                        self.start_frog_jump()
            else:
                # Handle tongue attack animation (extending, sticking, or retracting)
                self.update_frog_tongue()
        
        # Jumping state: Frog leaves the ground
        elif self.frog_state == 'jumping':
            self.frog_jump_timer += 1
            # Quick jump animation (30 frames)
            if self.frog_jump_timer <= 30:
                # Frog moves up off screen
                progress = self.frog_jump_timer / 30.0
                start_y = self.frog_shadow_position[1]
                self.frog_position[1] = start_y - progress * (start_y + 5)
            else:
                # Jump complete, now airborne
                self.frog_state = 'airborne'
                self.frog_jump_timer = 0
                self.frog_is_invulnerable = True
                print("Frog Boss: Airborne")
        
        # Airborne state: Wait 3-4 seconds, then fall
        elif self.frog_state == 'airborne':
            self.frog_airborne_timer += 1
            
            # Pick new landing position at the start of airborne (shadow moves once)
            if self.frog_airborne_timer == 1:
                self.pick_new_frog_landing()
                print("Frog Boss: Shadow moving to", self.frog_shadow_position)
            
            # Wait 210 frames (3.5 seconds)
            if self.frog_airborne_timer >= 210:
                # Start falling
                self.frog_state = 'falling'
                self.frog_airborne_timer = 0
                self.frog_fall_timer = 0
                self.frog_position = [self.frog_shadow_position[0], -5]
                print("Frog Boss: Falling to", self.frog_shadow_position)
        
        # Update damage flash
        if self.boss_damage_flash > 0:
            self.boss_damage_flash -= 1
        if self.boss_damage_sound_cooldown > 0:
            self.boss_damage_sound_cooldown -= 1
        
        # Handle boss defeated (Phase 1 trigger)
        if self.boss_health <= 0 and not self.boss_defeated:
            print("Frog Boss defeated! Starting death animation phase 1...")
            self.boss_defeated = True
            self.player_frozen = True
            self.boss_death_phase = 1
            
            # Unlock Toad Crusher achievement
            self.unlock_achievement(1)
            # Phase 1: Brief pause (1 second)
            self.boss_death_phase1_timer = 60  # 1 second
            pygame.mixer.music.fadeout(2000)
            self.music_manager.silent_mode = True
            # Clear tongue and reset all tongue/jump timers
            self.frog_tongue_segments = []
            self.frog_tongue_extending = False
            self.frog_tongue_retracting = False
            self.frog_tongue_sticking = False
            self.frog_tongue_timer = 0
            self.frog_tongue_stuck_timer = 0
            self.frog_jump_timer = 0  # Reset jump timer to prevent jumping during death
            self.frog_landed_timer = 0  # Reset landed timer
            # Destroy all enemy walls immediately
            if hasattr(self, 'enemies') and self.enemies:
                for enemy in self.enemies:
                    if enemy.alive and enemy.enemy_type == 'enemy_wall':
                        enemy.alive = False
                        self.create_particles(enemy.grid_x * GRID_SIZE + GRID_SIZE // 2,
                                            enemy.grid_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                            GRAY, 12)
                print("All enemy walls destroyed!")
        
        # Death sequence phases
        if self.boss_defeated:
            # Phase 1: Brief pause (1 second)
            if self.boss_death_phase == 1:
                # Initialize timer if it doesn't exist (safety check)
                if not hasattr(self, 'boss_death_phase1_timer'):
                    self.boss_death_phase1_timer = 60  # 1 second
                
                if self.boss_death_phase1_timer > 0:
                    self.boss_death_phase1_timer -= 1
                else:
                    # Move to phase 2
                    print("Phase 1 complete, moving to phase 2 (shake with explosions)")
                    self.boss_death_phase = 2
                    self.boss_slide_timer = 240  # 4 seconds of shaking/explosions
                    self.screen_shake_intensity = 2  # Match worm boss shake intensity
                    # Play death sound now that music has faded
                    self.sound_manager.play('frogBossDeath')
                    # Clear any existing shake timer
                    if hasattr(self, 'screen_shake_timer'):
                        self.screen_shake_timer = 0
            
            # Phase 2: Shake with continuous explosions (4 seconds)
            elif self.boss_death_phase == 2 and self.boss_slide_timer > 0:
                self.boss_slide_timer -= 1
                self.screen_shake_intensity = 2  # Keep shaking
                
                # Spawn white explosion particles continuously (every 2 frames like worm boss)
                if self.boss_slide_timer % 2 == 0:
                    # Calculate frog center position in pixels
                    frog_center_x = int((self.frog_position[0] + 2) * GRID_SIZE)
                    frog_center_y = int((self.frog_position[1] + 2) * GRID_SIZE + GAME_OFFSET_Y)
                    # Spawn particles randomly within frog sprite (4x4 grid cells = 128x128 pixels)
                    import random
                    rand_x = frog_center_x + random.randint(-GRID_SIZE * 2, GRID_SIZE * 2)
                    rand_y = frog_center_y + random.randint(-GRID_SIZE * 2, GRID_SIZE * 2)
                    self.create_particles(rand_x, rand_y, None, None, particle_type='white')
                
                # When timer expires, move to phase 3
                if self.boss_slide_timer <= 0:
                    print("Phase 2 complete, waiting before victory jingle")
                    self.boss_death_phase = 3
                    self.screen_shake_intensity = 0
                    self.boss_spawned = False
                    # DON'T set boss_active = False yet - Phase 3 still needs to run!
                    self.boss_death_delay = 120  # 2 seconds wait before victory jingle
            
            # Phase 3: Wait, then play victory jingle
            elif self.boss_death_phase == 3:
                if self.boss_death_delay > 0:
                    self.boss_death_delay -= 1
                else:
                    # Calculate completion percentage for BOSS LEVELS
                    print("Playing victory jingle...")
                    starting_length = 3
                    current_segments = len(self.snake.body) + self.snake.grow_pending
                    segments_gained = current_segments - starting_length
                    self.final_segments = current_segments
                    
                    # NEW BOSS SCORING SYSTEM:
                    # 1. Base 60% for defeating the boss (main objective)
                    boss_defeat_score = 60
                    
                    # 2. Up to 20% for survival/growth (based on snake length)
                    # Award 1% per segment gained, capped at 20%
                    growth_score = min(segments_gained, 20)
                    
                    # 3. Up to 20% for bonus items collected (if any bonus fruits in level)
                    bonus_score = 0
                    if self.total_bonus_fruits > 0:
                        # Award proportional points: (collected / total) * 20
                        bonus_score = int((self.bonus_fruits_collected / self.total_bonus_fruits) * 20)
                    
                    # Total completion percentage (capped at 100%)
                    self.completion_percentage = min(boss_defeat_score + growth_score + bonus_score, 100)
                    
                    print("Boss level score breakdown: Defeat={}, Growth={}, Bonus={}, Total={}%".format(
                        boss_defeat_score, growth_score, bonus_score, self.completion_percentage))
                    
                    # Save level score and unlock next level
                    self.is_new_level_high_score = self.update_level_score(self.current_adventure_level, self.completion_percentage)
                    self.unlock_level(self.current_adventure_level + 1)
                    
                    # Play victory jingle and transition to level complete
                    self.music_manager.play_victory_jingle()
                    self.state = GameState.LEVEL_COMPLETE
                    self.level_complete_timer = 180
                    self.sound_manager.play('win')
                    
                    # NOW we can set boss_active = False since victory screen is triggered
                    self.boss_active = False
        
        # Periodic isotope spawning - maintain 2 isotopes on the field
        if self.boss_spawned and hasattr(self, 'isotope_spawn_timer'):
            self.isotope_spawn_timer += 1
            if self.isotope_spawn_timer >= self.isotope_spawn_interval:
                isotope_count = sum(1 for _, food_type in self.food_items if food_type == 'isotope')
                while isotope_count < 2:
                    if self.spawn_isotope():
                        isotope_count += 1
                    else:
                        break  # Stop if we can't find a valid spawn location
                self.isotope_spawn_timer = 0
    
    def start_frog_tongue_attack(self):
        """Start the frog's tongue attack"""
        self.frog_tongue_extending = True
        self.frog_tongue_retracting = False
        self.frog_tongue_sticking = False
        self.frog_tongue_timer = 0
        self.frog_tongue_segments = []
        self.frog_tongue_stuck_timer = 0
        
        # Always aim at player's head (after jump 3, use current position, otherwise use last known)
        if len(self.snake.body) > 0:
            player_head = self.snake.body[0]
            # Frog center is at position + 2 grid cells (since frog is 4x4)
            frog_center_x = self.frog_position[0] + 2
            frog_center_y = self.frog_position[1] + 2
            
            # Calculate angle to player head
            dx = player_head[0] - frog_center_x
            dy = player_head[1] - frog_center_y
            
            # Calculate angle in degrees (0 = right, 90 = down, 180 = left, 270 = up)
            import math
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            # Normalize to 0-360 range
            if angle_deg < 0:
                angle_deg += 360
            
            self.frog_target_rotation = angle_deg
            
            # Store direction as normalized vector for tongue extension
            distance = math.sqrt(dx * dx + dy * dy)
            if distance > 0:
                self.frog_tongue_direction = (dx / distance, dy / distance)
            else:
                self.frog_tongue_direction = (1, 0)  # Default right
        else:
            # Default direction if no player
            self.frog_tongue_direction = (1, 0)  # Right
            self.frog_target_rotation = 0
        
        print("Frog Boss: Starting tongue attack at angle {:.1f} degrees".format(self.frog_target_rotation))
    
    def update_frog_tongue(self):
        """Update tongue extension/retraction animation"""
        self.frog_tongue_timer += 1
        
        if self.frog_tongue_extending:
            # Extend tongue - add new segment every 5 frames (slower)
            if self.frog_tongue_timer % 5 == 0:
                # Calculate next segment position
                segment_spacing = 0.5  # Reduced spacing between segments
                if len(self.frog_tongue_segments) == 0:
                    # First segment starts at frog center (frog is 4x4)
                    frog_center_x = self.frog_position[0] + 2
                    frog_center_y = self.frog_position[1] + 2
                    # Move in the direction vector with reduced spacing
                    next_x = frog_center_x + self.frog_tongue_direction[0] * segment_spacing
                    next_y = frog_center_y + self.frog_tongue_direction[1] * segment_spacing
                    next_pos = (next_x, next_y)
                else:
                    # Extend from last segment using the direction vector with reduced spacing
                    last_seg = self.frog_tongue_segments[-1]
                    next_x = last_seg[0] + self.frog_tongue_direction[0] * segment_spacing
                    next_y = last_seg[1] + self.frog_tongue_direction[1] * segment_spacing
                    next_pos = (next_x, next_y)
                
                # Check if next position is valid and not hitting obstacles
                hit_obstacle = False
                
                # Convert to grid position for wall/bounds checking
                grid_pos = (int(round(next_pos[0])), int(round(next_pos[1])))
                
                # Check screen bounds
                if not (0 <= next_pos[0] < GRID_WIDTH and 0 <= next_pos[1] < GRID_HEIGHT):
                    hit_obstacle = True
                # Check for duplicate position (within threshold)
                elif len(self.frog_tongue_segments) > 0:
                    last_pos = self.frog_tongue_segments[-1]
                    dist = abs(next_pos[0] - last_pos[0]) + abs(next_pos[1] - last_pos[1])
                    if dist < 0.1:  # Very close to last segment
                        hit_obstacle = True
                # Check for wall collision (use rounded grid position)
                if not hit_obstacle and hasattr(self, 'level_walls') and grid_pos in self.level_walls:
                    hit_obstacle = True
                
                if not hit_obstacle:
                    # Valid position, add segment
                    self.frog_tongue_segments.append(next_pos)
                    # Check collision with player body
                    self.check_tongue_collision(next_pos)
                elif len(self.frog_tongue_segments) > 0:
                    # Hit obstacle (wall, edge, or duplicate), start sticking phase
                    self.frog_tongue_extending = False
                    self.frog_tongue_sticking = True
                    self.frog_tongue_timer = 0
                    self.frog_tongue_stuck_timer = 90  # Stick for 1.5 seconds (90 frames)
                    print("Frog tongue hit obstacle, sticking at {} segments".format(len(self.frog_tongue_segments)))
            
            # Tongue fully extended (15 segments) - start sticking
            if len(self.frog_tongue_segments) >= 15:
                self.frog_tongue_extending = False
                self.frog_tongue_sticking = True
                self.frog_tongue_timer = 0
                self.frog_tongue_stuck_timer = 90  # Stick for 1.5 seconds
        
        elif self.frog_tongue_sticking:
            # Tongue is stuck at full extension
            if self.frog_tongue_stuck_timer > 0:
                self.frog_tongue_stuck_timer -= 1
            else:
                # Done sticking, start retracting
                self.frog_tongue_sticking = False
                self.frog_tongue_retracting = True
                self.frog_tongue_timer = 0
        
        elif self.frog_tongue_retracting:
            # Retract tongue - remove segment every 8 frames (much slower)
            if self.frog_tongue_timer % 8 == 0 and len(self.frog_tongue_segments) > 0:
                self.frog_tongue_segments.pop()  # Remove last segment
            
            # Tongue fully retracted
            if len(self.frog_tongue_segments) == 0:
                self.frog_tongue_retracting = False
                self.frog_tongue_timer = 0
                self.frog_jump_timer = 0  # Reset jump timer
    
    def check_tongue_collision(self, tongue_pos):
        """Check if tongue segment hit player"""
        if len(self.snake.body) == 0:
            return
        
        # Check collision with player body (not head) - check if within same grid cell
        tongue_grid_pos = (int(round(tongue_pos[0])), int(round(tongue_pos[1])))
        if tongue_grid_pos in self.snake.body[1:]:
            # Find which body segment was hit
            body_segment_index = self.snake.body.index(tongue_grid_pos)
            
            # Destroy tongue segments from this point onwards
            tongue_segment_index = self.frog_tongue_segments.index(tongue_pos)
            destroyed_tongue_segments = self.frog_tongue_segments[tongue_segment_index:]
            self.frog_tongue_segments = self.frog_tongue_segments[:tongue_segment_index]
            
            # Remove player body segments from hit point to tail
            removed_body_count = len(self.snake.body) - body_segment_index
            self.snake.body = self.snake.body[:body_segment_index]
            
            # Start retracting immediately
            self.frog_tongue_extending = False
            self.frog_tongue_retracting = True
            self.frog_tongue_timer = 0
            
            # Create particles at hit location
            hit_x = int(tongue_pos[0] * GRID_SIZE + GRID_SIZE // 2)
            hit_y = int(tongue_pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y)
            self.create_particles(hit_x, hit_y, RED, 10)
            self.sound_manager.play('eat_fruit')
            
            print("Frog tongue hit player body! {} tongue segments destroyed, {} body segments lost".format(
                len(destroyed_tongue_segments), removed_body_count))
    
    def start_frog_jump(self):
        """Start frog jump sequence"""
        self.frog_state = 'jumping'
        self.frog_jump_timer = 0
        self.frog_jump_count += 1
        
        # Clear tongue segments and reset tongue state (prevent leaving tongue behind)
        self.frog_tongue_segments = []
        self.frog_tongue_extending = False
        self.frog_tongue_retracting = False
        self.frog_tongue_sticking = False
        self.frog_tongue_timer = 0
        self.frog_tongue_stuck_timer = 0
        
        # After 3 jumps, start tracking player
        if self.frog_jump_count >= 3:
            self.frog_tracking_player = True
            print("Frog Boss: Now tracking player for next attack")
    
    def pick_new_frog_landing(self):
        """Pick a new random landing position for the frog"""
        # Pick random position, avoiding edges (need 2x2 space for frog)
        attempts = 0
        while attempts < 20:
            x = random.randint(2, GRID_WIDTH - 4)
            y = random.randint(2, GRID_HEIGHT - 4)
            
            # Make sure not too close to player (at least 3 cells away)
            if len(self.snake.body) > 0:
                player_head = self.snake.body[0]
                dist = abs(x - player_head[0]) + abs(y - player_head[1])
                if dist >= 3:
                    self.frog_shadow_position = [x, y]
                    return
            else:
                self.frog_shadow_position = [x, y]
                return
            attempts += 1
        
        # Fallback: use center
        self.frog_shadow_position = [GRID_WIDTH // 2, GRID_HEIGHT // 2]
    
    def interpolate_frog_rotation(self):
        """Smoothly interpolate frog rotation angle towards target"""
        # Calculate the shortest angular distance
        diff = self.frog_target_rotation - self.frog_rotation_angle
        
        # Normalize diff to -180 to 180 range (shortest path)
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        
        # Interpolate with speed (adjust speed for smoothness)
        rotation_speed = 8.0  # Degrees per frame
        if abs(diff) <= rotation_speed:
            # Close enough, snap to target
            self.frog_rotation_angle = self.frog_target_rotation
        else:
            # Rotate towards target
            if diff > 0:
                self.frog_rotation_angle += rotation_speed
            else:
                self.frog_rotation_angle -= rotation_speed
            
            # Normalize to 0-360 range
            if self.frog_rotation_angle < 0:
                self.frog_rotation_angle += 360
            elif self.frog_rotation_angle >= 360:
                self.frog_rotation_angle -= 360
    
    def respawn_boss_minion(self, minion_index):
        if minion_index >= len(self.boss_minions):
            return
        
        minion = self.boss_minions[minion_index]
        
        # Respawn positions
        minion_positions = [
            (GRID_WIDTH - 3, 3),  # Top right
            (GRID_WIDTH - 3, GRID_HEIGHT - 4)  # Bottom right
        ]
        
        # Reset the minion
        minion.reset(spawn_pos=minion_positions[minion_index], direction=Direction.LEFT)
        minion.alive = True
        minion.is_cpu = True
        minion.cpu_difficulty = 2  # Hard difficulty
        # Initialize movement tracking for smooth interpolation
        minion.move_timer = 0
        minion.last_move_interval = 16
        minion.previous_body = minion.body.copy()
        
        # Remove from respawn timer
        if minion_index in self.boss_minion_respawn_timers:
            del self.boss_minion_respawn_timers[minion_index]
        
        print("Boss minion {} respawned at {}".format(minion_index + 1, minion_positions[minion_index]))
    
    def spawn_food_item(self, food_type):
        """Spawn a specific food item for multiplayer."""
        occupied_positions = set()
        for snake in self.snakes:
            occupied_positions.update(snake.body)
        occupied_positions.update([pos for pos, _ in self.food_items])
        
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            
            # Check if position is valid (not occupied, not a wall)
            if (x, y) in occupied_positions:
                continue
            
            # Check multiplayer walls
            if hasattr(self, 'walls') and self.walls and (x, y) in self.walls:
                continue
            
            # Check adventure mode walls
            if hasattr(self, 'level_walls') and (x, y) in self.level_walls:
                continue
            
            # Valid spawn position found!
            self.food_items.append(((x, y), food_type))
            print("Spawned {} at {}".format(food_type, (x, y)))
            return
        print("Warning: Could not spawn {}".format(food_type))
    
    def spawn_bonus_food(self):
        while True:
            # Spawn bonus food within playable area (avoid 1-grid-cell border)
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if (x, y) not in self.snake.body and (x, y) != self.food_pos:
                self.bonus_food_pos = (x, y)
                self.bonus_food_timer = 600
                break
    
    def spawn_isotope(self):
        """Spawn an isotope collectible in a safe location (for boss battles)"""
        # Collect all occupied positions
        occupied_positions = set()
        occupied_positions.update(self.snake.body)
        
        # Add boss minion positions if they exist
        if hasattr(self, 'boss_minions'):
            for minion in self.boss_minions:
                if minion and minion.alive:
                    occupied_positions.update(minion.body)
        
        # Add existing food items
        occupied_positions.update([pos for pos, _ in self.food_items])
        
        # Add level walls if they exist
        if hasattr(self, 'level_walls'):
            occupied_positions.update(self.level_walls)
        
        # Add enemy positions (including enemy walls from super attacks)
        if hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.alive:
                    occupied_positions.add((enemy.grid_x, enemy.grid_y))
        
        # Try to spawn isotope in a safe location
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(2, GRID_WIDTH - 3)
            y = random.randint(2, GRID_HEIGHT - 3)
            
            # Avoid lower right quadrant during boss battles (boss zone)
            if hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned:
                # Lower right quadrant: x >= 8 and y >= 8
                if x >= 8 and y >= 8:
                    continue  # Skip this position, try again
            
            if (x, y) not in occupied_positions:
                self.food_items.append(((x, y), 'isotope'))
                print("Spawned isotope at ({}, {})".format(x, y))
                return True
        
        # Debug: Show why spawning failed
        available_spaces = (GRID_WIDTH - 4) * (GRID_HEIGHT - 4)
        if hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned:
            # Subtract boss zone (roughly 7x7 = 49 spaces)
            available_spaces -= 49
        occupied_count = len(occupied_positions)
        print("Warning: Could not find safe location to spawn isotope after 100 attempts")
        print("  Occupied positions: {}, Available spaces (approx): {}".format(occupied_count, available_spaces))
        return False
    
    def get_next_level_score(self):
        """Calculate the score needed to reach the next level.
        Level 2: 200, Level 3: 400, Level 4: 600, Level 5: 800, etc.
        Formula: 200 * level - lower threshold for faster progression
        """
        return 200 * self.level
    
    def get_score_multiplier(self):
        """Get the score multiplier based on difficulty."""
        if self.difficulty == Difficulty.EASY:
            return 0.5
        elif self.difficulty == Difficulty.MEDIUM:
            return 1.0
        elif self.difficulty == Difficulty.HARD:
            return 2.0
        return 1.0
    def get_difficulty_length_modifier(self):
        # In endless mode, growth varies by difficulty
        if self.game_mode == "endless":
            if self.difficulty == Difficulty.HARD:
                return 4
            elif self.difficulty == Difficulty.MEDIUM:
                return 2
            else:  # EASY
                return 1
        
        # In other modes (adventure/multiplayer), keep original behavior
        # Hard mode: grow by 2 instead of 1 (fills faster)
        if self.difficulty == Difficulty.HARD:
            return 2
        # Medium mode: normal growth
        return 1
    
    def handle_player_death(self, snake):
        """Handle a player's death in multiplayer mode."""
        if not snake.alive:
            return
        
        snake.alive = False
        snake.lives -= 1
        self.sound_manager.play('die')
        
        # Spawn white particles on all body segments
        for segment_x, segment_y in snake.body:
            self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                None, None, particle_type='white')
        
        print("Player {} died! Lives remaining: {}".format(snake.player_id + 1, snake.lives))
        
        # Check if this player has lives left for respawn
        if snake.lives > 0:
            # Spawn an egg for respawn
            self.spawn_respawn_egg(snake.player_id)
        
        # Check if only one player with lives remains
        players_with_lives = [s for s in self.snakes if s.lives > 0]
        if len(players_with_lives) == 1:
            # Game over - we have a winner!
            winner = players_with_lives[0]
            print("Player {} wins the match!".format(winner.player_id + 1))
            self.sound_manager.play('level_up')
            # Broadcast game end to network clients
            if self.is_network_game and self.network_manager.is_host():
                final_scores = [0] * len(self.snakes)  # TODO: Track actual scores
                end_msg = create_game_end_message(winner.player_id, final_scores)
                self.network_manager.broadcast_to_clients(end_msg)
            # Set a delay before transitioning to game over screen
            self.multiplayer_end_timer = 120  # 2 seconds at 60 FPS
        elif len(players_with_lives) == 0:
            # Everyone ran out of lives - draw
            print("Draw - all players eliminated!")
            self.sound_manager.play('no_lives')
            # Broadcast game end to network clients (no winner)
            if self.is_network_game and self.network_manager.is_host():
                final_scores = [0] * len(self.snakes)
                end_msg = create_game_end_message(-1, final_scores)  # -1 = draw
                self.network_manager.broadcast_to_clients(end_msg)
            # Set a delay before transitioning to game over screen
            self.multiplayer_end_timer = 120  # 2 seconds at 60 FPS
    
    def respawn_player(self, player_id, pos, direction):
        """Respawn a player at the egg position."""
        # Find the snake
        snake = next((s for s in self.snakes if s.player_id == player_id), None)
        if snake is None:
            print("Warning: Could not find snake for player {}".format(player_id + 1))
            return
        
        # Reset snake at the egg position
        snake.reset(spawn_pos=pos, direction=direction)
        snake.alive = True
        snake.speed_modifier = 0  # Reset speed on respawn
        
        # Remove from respawning players
        del self.respawning_players[player_id]
        
        # Spawn egg crack particles and egg pieces
        self.sound_manager.play('crack')
        center_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
        center_y = pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
        
        # Spawn particle effect
        self.create_particles(center_x, center_y, None, None, particle_type='white')
        
        # Spawn flying egg pieces (same as single player egg hatching)
        if len(self.egg_piece_imgs) == 4:
            velocities = [
                (-4, -6),  # Top-left
                (4, -6),   # Top-right
                (-5, -3),  # Left
                (5, -3)    # Right
            ]
            
            for i, (vx, vy) in enumerate(velocities):
                piece = EggPiece(center_x, center_y, self.egg_piece_imgs[i], (vx, vy))
                self.egg_pieces.append(piece)
        
        print("Player {} respawned at {}".format(player_id + 1, pos))
    
    def get_safe_cpu_direction(self, pos):
        """Find a safe direction for CPU to hatch from egg."""
        x, y = pos
        directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        
        # Check which directions are safe
        safe_dirs = []
        for direction in directions:
            dx, dy = direction.value
            new_x, new_y = x + dx, y + dy
            
            # Check if in bounds and not occupied
            if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                is_safe = True
                # Check against all snake bodies
                for snake in self.snakes:
                    if snake.alive and (new_x, new_y) in snake.body:
                        is_safe = False
                        break
                if is_safe:
                    safe_dirs.append(direction)
        
        return random.choice(safe_dirs) if safe_dirs else random.choice(directions)
    
    def update_cpu_decision(self, snake):
        """AI logic for CPU players."""
        if not snake.alive:
            return
        
        head_x, head_y = snake.body[0]
        difficulty = snake.cpu_difficulty
        
        # Get all possible directions (excluding opposite of current direction)
        possible_directions = []
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            # Can't go opposite direction
            if direction.value == (-snake.direction.value[0], -snake.direction.value[1]):
                continue
            possible_directions.append(direction)
        
        # Evaluate each direction and choose based on difficulty
        best_direction = None
        best_score = -999999
        safe_moves = []  # Track moves that don't immediately kill
        
        for direction in possible_directions:
            dx, dy = direction.value
            new_x = head_x + dx
            new_y = head_y + dy
            
            # Calculate score for this direction
            score = 0
            is_immediately_fatal = False
            
            # Check if move is valid (not wall, not self)
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                score -= 10000  # Grid boundary
                is_immediately_fatal = True
            elif (new_x, new_y) in self.level_walls:
                score -= 10000  # Adventure mode level wall collision
                is_immediately_fatal = True
            elif hasattr(self, 'walls') and self.walls and (new_x, new_y) in self.walls:
                score -= 10000  # Multiplayer level wall collision
                is_immediately_fatal = True
            elif (new_x, new_y) in snake.body:
                score -= 10000  # Self collision
                is_immediately_fatal = True
            else:
                # Valid move, evaluate based on difficulty
                
                # Check collision with other snakes
                for other_snake in self.snakes:
                    if other_snake.player_id != snake.player_id and other_snake.alive:
                        if (new_x, new_y) in other_snake.body:
                            score -= 10000
                            is_immediately_fatal = True
                            break
                
                # Only evaluate further if not immediately fatal
                if not is_immediately_fatal:
                    # Check if this is an enemy snake (can't eat food)
                    is_enemy_snake = hasattr(snake, 'is_enemy_snake') and snake.is_enemy_snake
                    
                    # Only seek food if this is a player/CPU (not enemy snake)
                    if not is_enemy_snake:
                        # Look for food (all difficulties)
                        closest_food_dist = 999999
                        best_food_type = None
                        
                        for food_pos, food_type in self.food_items:
                            fx, fy = food_pos
                            dist = abs(new_x - fx) + abs(new_y - fy)
                            
                            # Weight food by type based on difficulty
                            if difficulty >= 2:  # Hard+
                                if food_type == 'apple':
                                    dist *= 0.7  # Prefer apples
                                elif food_type == 'black_apple':
                                    dist *= 2.0  # Avoid black apples
                            
                            if dist < closest_food_dist:
                                closest_food_dist = dist
                                best_food_type = food_type
                        
                        # Score based on proximity to food
                        if closest_food_dist < 999999:
                            score += (100 - closest_food_dist * 5)
                            
                            # Brutal difficulty: strategic food choices
                            if difficulty >= 3:
                                if best_food_type == 'apple' and snake.speed_modifier < 0:
                                    score += 50  # Already fast, less priority
                                elif best_food_type == 'apple':
                                    score += 100  # Prioritize speed boost
                                elif best_food_type == 'black_apple':
                                    score -= 200  # Strongly avoid black apples
                    else:
                        # Enemy snakes: just wander randomly, favor open space
                        score += random.randint(-30, 30)
                    
                    # Avoid danger zones (look ahead)
                    if difficulty >= 2:
                        danger_count = 0
                        for check_dir in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                            cdx, cdy = check_dir.value
                            check_x = new_x + cdx
                            check_y = new_y + cdy
                            
                            # Check if dangerous
                            if check_x < 0 or check_x >= GRID_WIDTH or check_y < 0 or check_y >= GRID_HEIGHT:
                                danger_count += 1
                            else:
                                for other_snake in self.snakes:
                                    if other_snake.alive and (check_x, check_y) in other_snake.body:
                                        danger_count += 1
                                        break
                        
                        score -= danger_count * 10
                    
                    # Brutal: avoid corners and tight spaces
                    if difficulty >= 3:
                        open_spaces = 0
                        for check_dir in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                            cdx, cdy = check_dir.value
                            check_x = new_x + cdx
                            check_y = new_y + cdy
                            
                            if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                                is_open = True
                                for check_snake in self.snakes:
                                    if check_snake.alive and (check_x, check_y) in check_snake.body:
                                        is_open = False
                                        break
                                if is_open:
                                    open_spaces += 1
                        
                        score += open_spaces * 15
                    
                    # Add small random factor (less random for higher difficulty)
                    if difficulty == 0:  # Easy
                        score += random.randint(-50, 50)
                    elif difficulty == 1:  # Medium
                        score += random.randint(-20, 20)
                    elif difficulty == 2:  # Hard
                        score += random.randint(-10, 10)
                    # Brutal has minimal randomness
                    
                    # This is a safe move - add to list
                    safe_moves.append((direction, score))
            
            # Track all moves with their scores (even fatal ones, as fallback)
            if score > best_score:
                best_score = score
                best_direction = direction
        
        # Priority 1: Use safe moves if any exist
        if safe_moves:
            # Pick the best safe move
            safe_moves.sort(key=lambda x: x[1], reverse=True)
            best_direction = safe_moves[0][0]
        
        # Priority 2: If no safe moves, pick least bad option (happens when cornered)
        elif best_direction is None and possible_directions:
            # Just pick any direction to avoid getting stuck
            best_direction = possible_directions[0]
        
        # Final validation: Make sure the chosen direction won't immediately kill us
        if best_direction:
            dx, dy = best_direction.value
            next_x = head_x + dx
            next_y = head_y + dy
            
            # Double check this move is safe
            is_safe = True
            if next_x < 0 or next_x >= GRID_WIDTH or next_y < 0 or next_y >= GRID_HEIGHT:
                is_safe = False
            elif (next_x, next_y) in self.level_walls:
                is_safe = False  # Check level walls
            elif (next_x, next_y) in snake.body:
                is_safe = False
            else:
                for other_snake in self.snakes:
                    if other_snake.player_id != snake.player_id and other_snake.alive:
                        if (next_x, next_y) in other_snake.body:
                            is_safe = False
                            break
            
            # Only change direction if safe, or if we have no choice
            if is_safe or not safe_moves:
                if best_direction != snake.direction:
                    snake.change_direction(best_direction)
    
    def spawn_respawn_egg(self, player_id):
        """Spawn a respawn egg for a dead player."""
        # Find an unoccupied position
        occupied_positions = set()
        for snake in self.snakes:
            if snake.alive:
                occupied_positions.update(snake.body)
        occupied_positions.update([pos for pos, _ in self.food_items])
        occupied_positions.update([data['pos'] for data in self.respawning_players.values()])
        
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(2, GRID_WIDTH - 3)
            y = random.randint(2, GRID_HEIGHT - 3)
            
            # Check if position is valid (not occupied, not a wall)
            if (x, y) in occupied_positions:
                continue
            
            # Check multiplayer walls
            if hasattr(self, 'walls') and self.walls and (x, y) in self.walls:
                continue
            
            # Check adventure mode walls
            if hasattr(self, 'level_walls') and (x, y) in self.level_walls:
                continue
            
            # Valid spawn position found!
            # Spawn egg with 5 second timer (5 * 60 = 300 frames at 60fps)
            self.respawning_players[player_id] = {
                'pos': (x, y),
                'timer': 300,  # 5 seconds
                'direction': None
            }
            print("Spawned respawn egg for Player {} at ({}, {})".format(player_id + 1, x, y))
            return
        
        print("Warning: Could not find spawn position for Player {}".format(player_id + 1))
    
    
    def create_particles(self, x, y, color=None, count=None, particle_type='red'):
        # Spawn a single GIF particle effect based on type
        # particle_type can be 'red', 'white', 'rainbow', or 'yellow'
        if particle_type == 'white' and self.particle_white_frames:
            self.particles.append(GifParticle(x, y, self.particle_white_frames))
        elif particle_type == 'rainbow' and self.particle_rainbow_frames:
            self.particles.append(GifParticle(x, y, self.particle_rainbow_frames))
        elif particle_type == 'yellow' and self.particle_yellow_frames:
            self.particles.append(GifParticle(x, y, self.particle_yellow_frames))
        elif self.particle_frames:  # Default to red particles
            self.particles.append(GifParticle(x, y, self.particle_frames))
        # If particle frames not loaded, do nothing (silent fail for better performance)
    
    def get_interpolated_snake_positions(self):
        """Calculate smooth interpolated positions for snake segments"""
        move_interval = max(1, 16 - self.level // 2)
        progress = self.move_timer / move_interval  # 0.0 to 1.0
        
        interpolated_positions = []
        for i in range(len(self.snake.body)):
            current_pos = self.snake.body[i]
            
            # Get previous position, handling edge cases
            if i < len(self.snake.previous_body):
                previous_pos = self.snake.previous_body[i]
            else:
                previous_pos = current_pos  # Newly grown segment
            
            # Handle wrapping - detect if snake wrapped around screen edges
            dx = current_pos[0] - previous_pos[0]
            dy = current_pos[1] - previous_pos[1]
            
            # Adjust for wrapping (if difference is too large, it wrapped)
            if abs(dx) > GRID_WIDTH // 2:
                if dx > 0:
                    previous_pos = (previous_pos[0] + GRID_WIDTH, previous_pos[1])
                else:
                    previous_pos = (previous_pos[0] - GRID_WIDTH, previous_pos[1])
            
            if abs(dy) > GRID_HEIGHT // 2:
                if dy > 0:
                    previous_pos = (previous_pos[0], previous_pos[1] + GRID_HEIGHT)
                else:
                    previous_pos = (previous_pos[0], previous_pos[1] - GRID_HEIGHT)
            
            # Linear interpolation
            interp_x = previous_pos[0] + (current_pos[0] - previous_pos[0]) * progress
            interp_y = previous_pos[1] + (current_pos[1] - previous_pos[1]) * progress
            
            interpolated_positions.append((interp_x, interp_y))
        
        return interpolated_positions
    
    def update_game(self):
        # Update music - we're in gameplay (not menu)
        self.music_manager.update(in_menu=False)
        
        # Network clients: only render state from host, don't run game logic
        if self.is_network_game and self.network_manager.is_client():
            # Clients only update timers for smooth interpolation
            for snake in self.snakes:
                if snake.alive:
                    snake.move_timer += 1
                    # Reset timer when it gets too high
                    if snake.move_timer > 100:
                        snake.move_timer = 0
            
            # Update local effects (particles, animations) on client
            self.particles = [p for p in self.particles if p.is_alive()]
            for particle in self.particles:
                particle.update()
            
            self.egg_pieces = [p for p in self.egg_pieces if p.is_alive()]
            for piece in self.egg_pieces:
                piece.update()
            
            # Handle multiplayer end timer for client (game over transition)
            if hasattr(self, 'multiplayer_end_timer') and self.multiplayer_end_timer > 0:
                self.multiplayer_end_timer -= 1
                if self.multiplayer_end_timer == 0:
                    phase = getattr(self, 'multiplayer_end_timer_phase', 0)
                    if phase == 1:
                        # Phase 1 (client): Show game over screen after delay
                        self.music_manager.play_game_over_music()
                        self.state = GameState.GAME_OVER
                        self.game_over_timer = 0
                        self.multiplayer_end_timer_phase = 0
            
            # Handle network game over auto-progress timer for client
            if self.state == GameState.GAME_OVER:
                if hasattr(self, 'network_game_over_auto_timer') and self.network_game_over_auto_timer > 0:
                    self.network_game_over_auto_timer -= 1
            
            # Skip all other game logic updates for clients
            return
        
        # Broadcast game state to clients (host only, every frame for 60 updates/sec)
        if self.is_network_game and self.network_manager.is_host():
            # Broadcast every frame for smoother sync
            self.broadcast_game_state()
        
        # Update achievement notification timer
        if self.achievement_notification_active:
            self.achievement_notification_timer -= 1
            if self.achievement_notification_timer <= 0:
                self.achievement_notification_active = False
        
        # Update boss battle if active
        if self.boss_active and self.boss_data == 'wormBoss':
            # Increment boss timer (60 frames per second)
            self.boss_spawn_timer += 1 / 60.0
            
            # At 16 seconds, start screen shake (only if boss hasn't spawned yet)
            if self.boss_spawn_timer >= 14.0 and self.boss_spawn_timer < 28.0 and not self.boss_spawned:
                
                self.screen_shake_intensity = 2  # Shake intensity in pixels
                        # At 16 seconds, start screen shake (only if boss hasn't spawned yet)
            if self.boss_spawn_timer >= 17.0 and self.boss_spawn_timer < 28.0 and not self.boss_spawned:
                
                self.screen_shake_intensity = 4  # Shake intensity in pixels
            if self.boss_spawn_timer >= 21.0 and self.boss_spawn_timer < 28.0 and not self.boss_spawned:
                
                self.screen_shake_intensity = 8  # Shake intensity in pixels
            
            # At 28 seconds, spawn the boss
            if self.boss_spawn_timer >= 28.0 and not self.boss_spawned:
                self.boss_spawned = True
                self.screen_shake_intensity = 0  # Stop shaking when boss appears
                self.boss_current_animation = 'wormBossEmerges'
                self.boss_animation_frame = 0
                self.boss_animation_counter = 0
                self.boss_animation_loop = False  # Emergence plays once
                
                # Position boss: bottom right of screen
                # Boss is 128x128, screen is 240 wide, 240 tall
                # Place it so it's in the bottom right corner
                boss_x = SCREEN_WIDTH - 128  # Right edge at screen edge
                boss_y = SCREEN_HEIGHT - 128  # Bottom edge at screen edge
                self.boss_position = (boss_x, boss_y)
                
                # Spawn 2 boss minions (hard AI CPU snakes)
                self.spawn_boss_minions()
                
                print("Boss spawning at {} seconds at position {}".format(self.boss_spawn_timer, self.boss_position))
            
            # Update boss animation (but not during slide phase)
            if self.boss_spawned and self.boss_current_animation:
                # Don't update animation during phase 2 (slide) - it's frozen on last frame
                should_update_animation = not (self.boss_defeated and self.boss_death_phase == 2)
                
                if should_update_animation:
                    self.boss_animation_counter += 1
                    if self.boss_animation_counter >= self.boss_animation_speed:
                        self.boss_animation_counter = 0
                        self.boss_animation_frame += 1
                        
                        # Check if animation finished
                        anim_frames = self.boss_animations.get(self.boss_current_animation, [])
                        if anim_frames and self.boss_animation_frame >= len(anim_frames):
                            if self.boss_animation_loop:
                                # Loop the animation
                                self.boss_animation_frame = 0
                            else:
                                # Animation finished, transition to next
                                if self.boss_current_animation == 'wormBossEmerges':
                                    # After emergence, play idle
                                    self.boss_current_animation = 'wormBossIdle'
                                    self.boss_animation_frame = 0
                                    self.boss_animation_loop = True
                                    print("Boss emergence complete, transitioning to idle")
                                elif self.boss_current_animation == 'wormBossAttack':
                                    # Attack animation finished, spawn spewtums and return to idle
                                    self.spawn_boss_spewtums()
                                    self.boss_current_animation = 'wormBossIdle'
                                    self.boss_animation_frame = 0
                                    self.boss_animation_loop = True
                                    self.boss_is_attacking = False
                                    print("Boss attack complete, returning to idle")
                                elif self.boss_current_animation == 'wormBossDeath1':
                                    # Phase 1 finished - move to phase 2 (slide down with explosions)
                                    # Only transition if we're actually in phase 1 (prevent reset loop)
                                    if self.boss_death_phase == 1:
                                        print("Death phase 1 complete, moving to phase 2 (slide with explosions)")
                                        self.boss_death_phase = 2
                                        # Freeze on last frame of death animation
                                        self.boss_animation_frame = len(anim_frames) - 1
                                        self.boss_animation_loop = False
                                        # Initialize slide timer (320 frames = ~5.3 seconds at 60 FPS, 25% slower than before)
                                        self.boss_slide_timer = 320  # Halved from 640 for scaled resolution
                                        self.boss_slide_offset_y = 0
                                        # Play boss worm death sound now that music has faded
                                        self.sound_manager.play('bossWormDeath')
            
            # Update screen shake
            if self.screen_shake_intensity > 0:
                # Random shake offset
                shake_x = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
                shake_y = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
                self.screen_shake_offset = (shake_x, shake_y)
                
                # Count down shake timer if it exists (for timed shakes like super attack)
                if hasattr(self, 'screen_shake_timer') and self.screen_shake_timer > 0:
                    self.screen_shake_timer -= 1
                    if self.screen_shake_timer <= 0:
                        self.screen_shake_intensity = 0
            else:
                self.screen_shake_offset = (0, 0)
            
            # Update boss minions
            if self.boss_minions:
                for minion_idx, minion in enumerate(self.boss_minions):
                    if minion.alive:
                        # Update minion AI and movement
                        minion.move_timer += 1
                        move_interval = 16  # Same speed as normal snakes
                        
                        if minion.move_timer >= move_interval:
                            # AI decision making
                            self.update_cpu_decision(minion)
                            minion.move_timer = 0
                            minion.last_move_interval = move_interval  # Track for interpolation
                            minion.move()
                            
                            # Check collision with player snake (only if snake has a body)
                            if len(self.snake.body) > 0:
                                if minion.body[0] == self.snake.body[0]:
                                    # Minion head hit player head - player dies
                                    self.sound_manager.play('die')
                                    self.lives -= 1
                                    if self.lives <= 0:
                                        self.music_manager.play_game_over_music()
                                        self.state = GameState.GAME_OVER
                                        self.game_over_timer = self.game_over_delay
                                    else:
                                        # In adventure mode, wait before going to egg hatching to clear visuals
                                        if self.game_mode == "adventure":
                                            self.respawn_timer = self.respawn_delay
                                            # Clear the snake body immediately
                                            self.snake.body = []
                                        else:
                                            self.state = GameState.EGG_HATCHING
                                            # Mark this as a respawn for boss battles
                                            if hasattr(self, 'boss_active') and self.boss_active:
                                                self.boss_egg_is_respawn = True
                                                self.egg_timer = 0
                                elif minion.body[0] in self.snake.body[1:]:
                                    # Minion head hit player's body - minion dies
                                    minion.alive = False
                                    self.boss_minion_respawn_timers[minion_idx] = 900  # 15 seconds at 60 FPS
                                    self.sound_manager.play('eat')
                                    print("Boss minion {} killed, will respawn in 15 seconds".format(minion_idx + 1))
                            
                            # Boss minions don't eat food - they just wander as obstacles
                    else:
                        # Minion is dead, check respawn timer
                        if minion_idx in self.boss_minion_respawn_timers:
                            self.boss_minion_respawn_timers[minion_idx] -= 1
                            if self.boss_minion_respawn_timers[minion_idx] <= 0:
                                self.respawn_boss_minion(minion_idx)
            
            # Update boss damage flash and sound cooldown
            if self.boss_damage_flash > 0:
                self.boss_damage_flash -= 1
            if self.boss_damage_sound_cooldown > 0:
                self.boss_damage_sound_cooldown -= 1
            
            # Boss periodic attacks (only if not defeated)
            if self.boss_spawned and not self.boss_is_attacking and self.boss_health > 0 and not self.boss_defeated:
                self.boss_attack_timer += 1
                if self.boss_attack_timer >= self.boss_attack_interval:
                    # Time to attack! Start attack animation
                    self.boss_attack_timer = 0
                    self.boss_is_attacking = True
                    self.boss_current_animation = 'wormBossAttack'
                    self.boss_animation_frame = 0
                    self.boss_animation_loop = False
                    print("Boss starting attack animation!")
            
            # Handle boss death phase timers
            if self.boss_defeated:
                # Phase 1: If death animation 1 doesn't exist or failed to load, auto-advance after short delay
                if self.boss_death_phase == 1:
                    # Check if animation exists and has frames
                    has_death_anim = 'wormBossDeath1' in self.boss_animations and len(self.boss_animations['wormBossDeath1']) > 0
                    if not has_death_anim:
                        # No phase 1 animation, use a timer instead
                        if not hasattr(self, 'boss_death_phase1_timer'):
                            self.boss_death_phase1_timer = 60  # 1 second
                        if self.boss_death_phase1_timer > 0:
                            self.boss_death_phase1_timer -= 1
                        else:
                            # Auto-advance to phase 2
                            print("Phase 1 fallback timer complete, moving to phase 2 (slide with explosions)")
                            self.boss_death_phase = 2
                            self.boss_slide_timer = 240  # 4 seconds
                            self.boss_slide_offset_y = 0
                            # Play boss worm death sound now that music has faded
                            self.sound_manager.play('bossWormDeath')
                
                # Phase 2: Slide down off-screen with continuous white explosions
                if self.boss_death_phase == 2 and self.boss_slide_timer > 0:
                    self.boss_slide_timer -= 1
                    self.screen_shake_intensity = 2
                    # Calculate slide speed: need to move boss fully off screen (128px height + screen height)
                    # Over 320 frames (~5.3 seconds), slide down
                    # Total distance: SCREEN_HEIGHT (240) + boss height (128) = 368 pixels
                    slide_speed = (SCREEN_HEIGHT + 128) / 320.0  # ~1.15 pixels per frame
                    self.boss_slide_offset_y += slide_speed
                    
                    # Spawn white explosion particles continuously
                    # Spawn particles every 2 frames for lots of explosions
                    if self.boss_slide_timer % 2 == 0:
                        # Spawn white particles randomly on boss sprite
                        boss_x = self.boss_position[0]
                        boss_y = self.boss_position[1] + self.boss_slide_offset_y
                        # Random position within boss sprite (128x128)
                        rand_x = boss_x + random.randint(15, 113)
                        rand_y = boss_y + random.randint(15, 113)
                        # Create white explosion particles
                        self.create_particles(rand_x, rand_y, None, None, particle_type='white')
                    
                    # When slide timer reaches 0, transition to victory delay
                    if self.boss_slide_timer == 0:
                        print("Boss slide complete, waiting a few seconds before victory jingle")
                        self.boss_death_phase = 3
                        self.screen_shake_intensity = 0
                        # Stop rendering the boss and deactivate boss logic
                        self.boss_spawned = False
                        self.boss_current_animation = None
                        self.boss_active = False  # Prevent boss from respawning
                        self.boss_death_delay = 120  # 2 seconds wait before victory jingle
            
            # Update spewtum projectiles
            self.spewtums = [s for s in self.spewtums if s.alive]
            for spewtum in self.spewtums:
                spewtum.update()
                
                # Check collision with player snake (only if snake has a body)
                if len(self.snake.body) == 0:
                    continue
                
                spewtum_pos = (spewtum.grid_x, spewtum.grid_y)
                
                # Check if hit player head
                if spewtum_pos == self.snake.body[0]:
                    # Player dies
                    spewtum.alive = False
                    self.sound_manager.play('die')
                    self.lives -= 1
                    if self.lives <= 0:
                        self.music_manager.play_game_over_music()
                        self.state = GameState.GAME_OVER
                        self.game_over_timer = self.game_over_delay
                    else:
                        self.state = GameState.EGG_HATCHING
                        # Mark this as a respawn for boss battles
                        if hasattr(self, 'boss_active') and self.boss_active:
                            self.boss_egg_is_respawn = True
                            self.egg_timer = 0
                    print("Player hit by spewtum in the head!")
                # Check if hit player body
                elif spewtum_pos in self.snake.body[1:]:
                    # Player loses segments from hit point to tail
                    segment_index = self.snake.body.index(spewtum_pos)
                    spewtum.alive = False
                    self.sound_manager.play('eat_fruit')
                    # Remove all segments from hit point to tail
                    removed_count = len(self.snake.body) - segment_index
                    self.snake.body = self.snake.body[:segment_index]
                    # Create particles at hit location
                    hit_x = spewtum_pos[0] * GRID_SIZE + GRID_SIZE // 2
                    hit_y = spewtum_pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                    self.create_particles(hit_x, hit_y, RED, 10)
                    print("Player hit by spewtum in body! Lost {} segments".format(removed_count))
            
            # Periodic isotope spawning for boss battles - maintain 2 isotopes
            if self.boss_spawned and hasattr(self, 'isotope_spawn_timer'):
                self.isotope_spawn_timer += 1
                if self.isotope_spawn_timer >= self.isotope_spawn_interval:
                    # Spawn isotopes until we have 2 on the field
                    isotope_count = sum(1 for _, food_type in self.food_items if food_type == 'isotope')
                    while isotope_count < 2:
                        if self.spawn_isotope():
                            isotope_count += 1
                        else:
                            break  # Stop if we can't find a valid spawn location
                    # Reset timer
                    self.isotope_spawn_timer = 0
        
        # Update Frog Boss if active
        if self.boss_active and self.boss_data == 'frog':
            self.update_frog_boss()
        
        # Update enemy snakes (non-boss) - works in all adventure mode levels
        if self.game_mode == "adventure" and self.enemy_snakes:
            for enemy_snake in self.enemy_snakes:
                if enemy_snake.alive:
                    # Only update movement during PLAYING state
                    if self.state == GameState.PLAYING:
                        # Update enemy snake AI and movement
                        enemy_snake.move_timer += 1
                        move_interval = 24  # Same speed as normal snakes
                        
                        if enemy_snake.move_timer >= move_interval:
                            # AI decision making
                            self.update_cpu_decision(enemy_snake)
                            enemy_snake.move_timer = 0
                            enemy_snake.last_move_interval = move_interval
                            enemy_snake.previous_body = enemy_snake.body.copy()
                            enemy_snake.move()
                            
                            # Enemy snakes with can_eat=False should not eat food (to preserve scoring)
                            # They roam around but never consume food items
                            # This is already handled by not adding food eating logic here
                        
                        # Check collision with player snake every frame (not just when enemy moves)
                        if len(self.snake.body) > 0:
                            player_head = self.snake.body[0]
                            enemy_head = enemy_snake.body[0]
                            
                            # Check if player head hits enemy snake (any part) - player dies
                            if player_head in enemy_snake.body:
                                self.sound_manager.play('die')
                                self.lives -= 1
                                
                                # Spawn white particles on all body segments including head
                                for segment_x, segment_y in self.snake.body:
                                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                        None, None, particle_type='white')
                                
                                if self.lives <= 0:
                                    self.music_manager.play_game_over_music()
                                    self.state = GameState.GAME_OVER
                                    self.game_over_timer = self.game_over_delay
                                else:
                                    # In adventure mode, wait before going to egg hatching
                                    if self.game_mode == "adventure":
                                        self.respawn_timer = self.respawn_delay
                                        self.snake.body = []
                                    else:
                                        # Classic mode: respawn immediately
                                        self.respawn_snake()
                                print("Player head hit enemy snake!")
                            # Check if enemy snake head hits player body - enemy snake dies
                            elif enemy_head in self.snake.body[1:]:
                                enemy_snake.alive = False
                                self.sound_manager.play('die')
                                
                                # Spawn white particles on all enemy snake body segments
                                for segment_x, segment_y in enemy_snake.body:
                                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                        None, None, particle_type='white')
                                
                                print("Enemy snake head hit player body - enemy snake dies!")
                    else:
                        # Not in PLAYING state - sync previous_body to prevent flickering
                        enemy_snake.previous_body = enemy_snake.body.copy()
                        enemy_snake.move_timer = 0
        
        # Update screen shake (works for all boss types)
        if self.screen_shake_intensity > 0:
            # Random shake offset
            shake_x = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_y = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
            self.screen_shake_offset = (shake_x, shake_y)
            
            # Count down shake timer if it exists (for timed shakes like super attack)
            if hasattr(self, 'screen_shake_timer') and self.screen_shake_timer > 0:
                self.screen_shake_timer -= 1
                if self.screen_shake_timer <= 0:
                    self.screen_shake_intensity = 0
        else:
            self.screen_shake_offset = (0, 0)
        
        # Handle multiplayer end timer (delay after last player dies)
        if hasattr(self, 'multiplayer_end_timer') and self.multiplayer_end_timer > 0:
            self.multiplayer_end_timer -= 1
            if self.multiplayer_end_timer == 0:
                phase = getattr(self, 'multiplayer_end_timer_phase', 0)
                
                if phase == 1:
                    # Phase 1 (client only): Show game over screen after delay
                    self.music_manager.play_game_over_music()
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = 0  # Skip timer so winner is shown immediately
                    self.multiplayer_end_timer_phase = 0  # Done with phases, wait for host
                elif self.is_network_game and self.network_manager.is_host():
                    # Host phase 1: show game over, then set up auto-return timer
                    self.music_manager.play_game_over_music()
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = 0  # Skip timer so winner is shown immediately
                    self.multiplayer_end_timer_phase = 2  # Mark that we're in phase 2 (showing game over)
                    self.network_game_over_auto_timer = 600  # 10 seconds auto-progress to lobby
                else:
                    # Local multiplayer or single player
                    self.music_manager.play_game_over_music()
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = self.game_over_delay
        
        # Handle network multiplayer auto-progress to lobby (10 second timer)
        if self.state == GameState.GAME_OVER and self.is_network_game:
            if hasattr(self, 'network_game_over_auto_timer') and self.network_game_over_auto_timer > 0:
                self.network_game_over_auto_timer -= 1
                if self.network_game_over_auto_timer == 0:
                    # Auto-progress to lobby after 10 seconds
                    if self.network_manager.is_host():
                        return_msg = create_return_to_lobby_message()
                        self.network_manager.broadcast_to_clients(return_msg)
                        self.state = GameState.MULTIPLAYER_LOBBY
                        self.is_multiplayer = True
                        self.multiplayer_end_timer_phase = 0
                        self.broadcast_lobby_state()
        
        # Handle boss death phases 3-4 (outside boss_active block)
        # These need to continue after boss_active is set to False
        if self.boss_defeated and self.boss_death_phase >= 3:
            # Phase 3: Wait a few seconds, then play victory jingle
            if self.boss_death_phase == 3 and self.boss_death_delay > 0:
                self.boss_death_delay -= 1
                # Play victory jingle after waiting
                if self.boss_death_delay == 60:
                    print("Playing victory jingle...")
                    self.music_manager.play_victory_jingle()
                if self.boss_death_delay == 0:
                    # Move to phase 4: wait for jingle to finish
                    print("Victory jingle playing, waiting for it to finish...")
                    self.boss_death_phase = 4
                    self.boss_death_delay = 360  # 4 seconds for victory jingle to finish
            
            # Phase 4: Wait before transitioning to outro (ONLY for worm boss - final boss)
            if self.boss_death_phase == 4 and self.boss_death_delay > 0 and self.boss_data == 'wormBoss':
                self.boss_death_delay -= 1
                if self.boss_death_delay == 0:
                    # Trigger outro sequence (final boss only)
                    print("Boss battle complete! Transitioning to outro sequence")
                    
                    # Unlock Worm Smasher achievement (after all death animations complete)
                    self.unlock_achievement(2)
                    
                    self.music_manager.play_final_song()
                    self.start_outro()
        
        # Update snake head animation
        if self.snake_head_frames:
            self.head_animation_counter += 1
            if self.head_animation_counter >= self.head_animation_speed:
                self.head_animation_counter = 0
                self.head_frame_index = (self.head_frame_index + 1) % len(self.snake_head_frames)
        
        # Update worm (food) animation
        if self.worm_frames:
            self.worm_animation_counter += 1
            if self.worm_animation_counter >= self.worm_animation_speed:
                self.worm_animation_counter = 0
                self.worm_frame_index = (self.worm_frame_index + 1) % len(self.worm_frames)
        
        # Handle respawn timer countdown in adventure mode
        if self.state == GameState.PLAYING and self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer == 0:
                # Timer expired, transition to egg hatching
                self.state = GameState.EGG_HATCHING
                # Mark this as a respawn for boss battles
                if hasattr(self, 'boss_active') and self.boss_active:
                    self.boss_egg_is_respawn = True
                    self.egg_timer = 0
        
        # Handle game over timer countdown
        if self.state == GameState.GAME_OVER and self.game_over_timer > 0:
            self.game_over_timer -= 1
            if self.game_over_timer == 0:
                # Timer expired, transition to appropriate screen
                # Only check for high score in endless mode (not adventure or multiplayer)
                if self.game_mode == "endless" and self.is_high_score(self.score):
                    self.state = GameState.HIGH_SCORE_ENTRY
                    self.player_name = ['A', 'A', 'A']
                    self.name_index = 0
                    # Pick a random hint for this high score entry session
                    hints = [
                        "Length increases score multiplier!", 
                        "Fill entire screen for massive bonus!", 
                        "Your level increases score multiplier!", 
                        "Your level increases snakebird speed!", 
                        "Snakebird grows faster on hard!"]
                    self.current_hint = random.choice(hints)
                # Otherwise stay in GAME_OVER state for player to press button
        
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update()
        
        # Update egg pieces
        self.egg_pieces = [p for p in self.egg_pieces if p.is_alive()]
        for piece in self.egg_pieces:
            piece.update()
        
        # Update bullets
        self.bullets = [b for b in self.bullets if b.alive]
        for bullet in self.bullets:
            bullet.update()
        
        # Update scorpion stingers
        self.scorpion_stingers = [s for s in self.scorpion_stingers if s.alive]
        for stinger in self.scorpion_stingers:
            stinger.update()
        
        # Check scorpion stinger collisions with player
        for stinger in self.scorpion_stingers:
            if not stinger.alive:
                continue
            
            stinger_pos = (stinger.grid_x, stinger.grid_y)
            
            # Check if stinger hit player snake head (not body segments)
            if len(self.snake.body) > 0 and stinger_pos == self.snake.body[0]:
                # Player head hit by stinger - dies
                stinger.alive = False
                self.sound_manager.play('die')
                self.lives -= 1
                
                # Spawn white particles on all snake body segments
                for segment_x, segment_y in self.snake.body:
                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                        None, None, particle_type='white')
                
                if self.lives < 0:
                    self.sound_manager.play('no_lives')
                    self.music_manager.play_game_over_music()
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = self.game_over_delay
                else:
                    # In adventure mode, wait before going to egg hatching to clear visuals
                    if self.game_mode == "adventure":
                        self.respawn_timer = self.respawn_delay
                        # Clear the snake body immediately
                        self.snake.body = []
                    else:
                        # Go to egg hatching state for respawn
                        self.state = GameState.EGG_HATCHING
                break  # Don't check more stingers this frame
        
        # Update beetle larvae
        self.beetle_larvae = [l for l in self.beetle_larvae if l.alive]
        for larvae in self.beetle_larvae:
            larvae.update()
        
        # Check beetle larvae collisions with player
        for larvae in self.beetle_larvae:
            if not larvae.alive:
                continue
            
            larvae_pos = (larvae.grid_x, larvae.grid_y)
            
            # Check if larvae hit player snake (only if snake has a body)
            if len(self.snake.body) > 0 and larvae_pos in self.snake.body:
                # Player hit by larvae - dies
                larvae.alive = False
                self.sound_manager.play('die')
                self.lives -= 1
                
                # Spawn white particles on all snake body segments
                for segment_x, segment_y in self.snake.body:
                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                        None, None, particle_type='white')
                
                if self.lives < 0:
                    self.sound_manager.play('no_lives')
                    self.music_manager.play_game_over_music()
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = self.game_over_delay
                else:
                    # In adventure mode, wait before going to egg hatching to clear visuals
                    if self.game_mode == "adventure":
                        self.respawn_timer = self.respawn_delay
                        # Clear the snake body immediately
                        self.snake.body = []
                    else:
                        # Go to egg hatching state for respawn
                        self.state = GameState.EGG_HATCHING
                break  # Don't check more larvae this frame
        
        # Check bullet collisions with boss minions
        if self.boss_active and hasattr(self, 'boss_minions') and self.boss_minions:
            for bullet in self.bullets:
                if not bullet.alive:
                    continue
                
                bullet_pos = (bullet.grid_x, bullet.grid_y)
                
                for minion_idx, minion in enumerate(self.boss_minions):
                    if not minion.alive:
                        continue
                    
                    # Check if bullet hit minion head (instant kill)
                    if bullet_pos == minion.body[0]:
                        # Headshot - kill the minion
                        minion.alive = False
                        bullet.alive = False
                        self.boss_minion_respawn_timers[minion_idx] = 900  # 15 seconds respawn
                        self.sound_manager.play('die')
                        # Create particles at hit location
                        hit_x = bullet_pos[0] * GRID_SIZE + GRID_SIZE // 2
                        hit_y = bullet_pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                        self.create_particles(hit_x, hit_y, RED, 15)
                        print("Boss minion {} headshot! Respawning in 15 seconds.".format(minion_idx + 1))
                        break
                    
                    # Check if bullet hit minion body (remove segment)
                    elif bullet_pos in minion.body[1:]:
                        # Body shot - remove the segment that was hit
                        segment_index = minion.body.index(bullet_pos)
                        # Remove all segments from hit point to tail
                        minion.body = minion.body[:segment_index]
                        bullet.alive = False
                        self.sound_manager.play('eat_fruit')
                        # Create particles at hit location
                        hit_x = bullet_pos[0] * GRID_SIZE + GRID_SIZE // 2
                        hit_y = bullet_pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                        self.create_particles(hit_x, hit_y, NEON_ORANGE, 8)
                        print("Boss minion {} hit! Reduced to {} segments.".format(minion_idx + 1, len(minion.body)))
                        
                        # If minion is too small, kill it
                        if len(minion.body) < 2:
                            minion.alive = False
                            self.boss_minion_respawn_timers[minion_idx] = 900
                            self.sound_manager.play('die')
                            print("Boss minion {} destroyed! Respawning in 15 seconds.".format(minion_idx + 1))
                        break
        
        # Check bullet collisions with enemy snakes
        if hasattr(self, 'enemy_snakes') and self.enemy_snakes:
            for bullet in self.bullets:
                if not bullet.alive:
                    continue
                
                bullet_pos = (bullet.grid_x, bullet.grid_y)
                
                for enemy_snake in self.enemy_snakes:
                    if not enemy_snake.alive:
                        continue
                    
                    # Check if bullet hit anywhere - kill instantly (per user request)
                    if bullet_pos in enemy_snake.body:
                        enemy_snake.alive = False
                        bullet.alive = False
                        self.sound_manager.play('die')
                        # Spawn particles on all segments
                        for segment_x, segment_y in enemy_snake.body:
                            self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                None, None, particle_type='white')
                        print("Enemy snake destroyed by bullet!")
                        break
        
        # Check bullet collisions with regular enemies (ants, spiders, wasps, scorpions, beetles)
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            
            bullet_pos = (bullet.grid_x, bullet.grid_y)
            
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                
                # Skip enemy walls (they have separate collision below)
                if enemy.enemy_type == 'enemy_wall':
                    continue
                
                # Check if enemy is a regular enemy type
                if enemy.enemy_type.startswith(('enemy_ant', 'enemy_spider', 'enemy_wasp', 'enemy_scorpion', 'enemy_beetle')):
                    enemy_pos = (enemy.grid_x, enemy.grid_y)
                    
                    # For scorpions (2x2), check all grid cells they occupy
                    if enemy.enemy_type.startswith('enemy_scorpion'):
                        scorpion_cells = [
                            (enemy.grid_x, enemy.grid_y),
                            (enemy.grid_x + 1, enemy.grid_y),
                            (enemy.grid_x, enemy.grid_y + 1),
                            (enemy.grid_x + 1, enemy.grid_y + 1)
                        ]
                        if bullet_pos in scorpion_cells:
                            # Instant kill
                            enemy.alive = False
                            bullet.alive = False
                            self.sound_manager.play('die')
                            # Spawn particles at all 4 grid cells
                            for dx in range(2):
                                for dy in range(2):
                                    self.create_particles(
                                        (enemy.grid_x + dx) * GRID_SIZE + GRID_SIZE // 2,
                                        (enemy.grid_y + dy) * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                        None, None, particle_type='white')
                            print("Scorpion destroyed by bullet!")
                            break
                    else:
                        # Regular 1x1 enemies (ants, spiders, wasps, beetles)
                        if bullet_pos == enemy_pos:
                            # Instant kill
                            enemy.alive = False
                            bullet.alive = False
                            self.sound_manager.play('die')
                            # Spawn white particle
                            self.create_particles(
                                enemy.grid_x * GRID_SIZE + GRID_SIZE // 2,
                                enemy.grid_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                None, None, particle_type='white')
                            print(f"{enemy.enemy_type} destroyed by bullet!")
                            break
            
            if not bullet.alive:
                break  # Bullet hit something, stop checking
        
        # Check bullet collisions with enemy walls (destroyable)
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            
            bullet_pos = (bullet.grid_x, bullet.grid_y)
            
            for enemy in self.enemies:
                if not enemy.alive or enemy.enemy_type != 'enemy_wall':
                    continue
                
                enemy_pos = (enemy.grid_x, enemy.grid_y)
                if bullet_pos == enemy_pos:
                    # Hit enemy wall!
                    bullet.alive = False
                    enemy.health -= 1
                    self.sound_manager.play('eat_fruit')
                    
                    # Create particles at hit location
                    hit_x = bullet_pos[0] * GRID_SIZE + GRID_SIZE // 2
                    hit_y = bullet_pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                    self.create_particles(hit_x, hit_y, GRAY, 8)
                    
                    # Check if wall is destroyed
                    if enemy.health <= 0:
                        enemy.alive = False
                        self.sound_manager.play('coin')
                        print("Enemy wall destroyed!")
                    else:
                        print("Enemy wall hit! Health remaining: {}".format(enemy.health))
                    break
        
        # Check bullet collisions with boss
        if self.boss_active and self.boss_spawned and self.boss_health > 0:
            for bullet in self.bullets:
                if not bullet.alive:
                    continue
                
                hit_boss = False
                bullet_pixel_x = bullet.pixel_x
                bullet_pixel_y = bullet.pixel_y - GAME_OFFSET_Y  # Adjust for HUD offset
                
                # Check wormBoss collision (128x128 sprite)
                if self.boss_data == 'wormBoss':
                    boss_left = self.boss_position[0]
                    boss_right = self.boss_position[0] + 128
                    boss_top = self.boss_position[1]
                    boss_bottom = self.boss_position[1] + 128
                    
                    if (boss_left <= bullet_pixel_x <= boss_right and
                        boss_top <= bullet_pixel_y <= boss_bottom):
                        hit_boss = True
                
                # Check Frog Boss collision (2x2 grid cells = 64x64 pixels)
                elif self.boss_data == 'frog':
                    # Only vulnerable when on ground (not jumping/airborne)
                    if not self.frog_is_invulnerable and self.frog_state in ['landed', 'falling']:
                        frog_pixel_x = self.frog_position[0] * GRID_SIZE
                        frog_pixel_y = self.frog_position[1] * GRID_SIZE
                        frog_left = frog_pixel_x
                        frog_right = frog_pixel_x + GRID_SIZE * 2
                        frog_top = frog_pixel_y
                        frog_bottom = frog_pixel_y + GRID_SIZE * 2
                        
                        if (frog_left <= bullet_pixel_x <= frog_right and
                            frog_top <= bullet_pixel_y <= frog_bottom):
                            hit_boss = True
                
                if hit_boss:
                    # Boss hit!
                    bullet.alive = False
                    self.boss_health -= 1
                    self.boss_damage_flash = 10  # Flash for 10 frames
                    
                    # Play damage sound if not on cooldown
                    if self.boss_damage_sound_cooldown == 0:
                        self.sound_manager.play('bossWormDamage')
                        self.boss_damage_sound_cooldown = 15  # 15 frames (~0.25s) cooldown between damage sounds
                    
                    # Create particles at hit location
                    self.create_particles(int(bullet_pixel_x), int(bullet_pixel_y + GAME_OFFSET_Y), NEON_ORANGE, 15)
                    
                    # Update attack interval based on health (gets faster as health drops)
                    # Linear interpolation from max interval (at full health) to min interval (at 0 health)
                    health_percent = self.boss_health / self.boss_max_health
                    self.boss_attack_interval = int(self.boss_attack_interval_min + 
                                                   (self.boss_attack_interval_max - self.boss_attack_interval_min) * health_percent)
                    
                    print("Boss hit! Health: {}/{} - Attack interval now: {:.1f}s".format(
                        self.boss_health, self.boss_max_health, self.boss_attack_interval / 60.0))
                    
                    # Check if boss should trigger super attack at health threshold
                    for threshold in self.boss_super_attack_thresholds:
                        if health_percent <= threshold and threshold not in self.boss_super_attacks_used:
                            # Trigger super attack!
                            self.boss_super_attacks_used.add(threshold)
                            self.spawn_boss_super_attack()
                            break  # Only one super attack per hit
                    
                    # Check if boss is defeated
                    if self.boss_health <= 0 and not self.boss_defeated:
                        print("Boss defeated! Starting death animation phase 1...")
                        self.boss_defeated = True
                        # Freeze the player snake to prevent accidental death
                        self.player_frozen = True
                        # Start death animation phase 1
                        self.boss_death_phase = 1
                        # Try to use death animation, fallback to idle if not available
                        if 'wormBossDeath1' in self.boss_animations and self.boss_animations['wormBossDeath1']:
                            self.boss_current_animation = 'wormBossDeath1'
                            self.boss_animation_loop = False  # Play once
                        else:
                            # Fallback: switch to idle animation and keep looping
                            print("Warning: wormBossDeath1 not found, using looping idle fallback")
                            self.boss_current_animation = 'wormBossIdle'
                            self.boss_animation_loop = True  # Keep looping so it doesn't freeze
                        self.boss_animation_frame = 0
                        self.boss_animation_counter = 0  # Reset animation counter for smooth playback
                        # Stop attacking
                        self.boss_is_attacking = False
                        # Fade out music over 2 seconds and enable silent mode
                        pygame.mixer.music.fadeout(2000)  # 2000ms = 2 seconds
                        self.music_manager.silent_mode = True  # Prevent auto-play during death sequence
                        # Kill all boss minions
                        if hasattr(self, 'boss_minions') and self.boss_minions:
                            for minion in self.boss_minions:
                                if minion.alive:
                                    minion.alive = False
                                    # Create death particles for each minion
                                    for segment_x, segment_y in minion.body:
                                        self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                            segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                            None, None, particle_type='white')
                            # Clear respawn timers
                            self.boss_minion_respawn_timers.clear()
                            print("All boss minions eliminated!")
                        # Destroy all enemy walls immediately
                        if hasattr(self, 'enemies') and self.enemies:
                            for enemy in self.enemies:
                                if enemy.alive and enemy.enemy_type == 'enemy_wall':
                                    enemy.alive = False
                                    # Create particles where wall was
                                    self.create_particles(enemy.grid_x * GRID_SIZE + GRID_SIZE // 2,
                                                        enemy.grid_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                        GRAY, 12)
                            print("All enemy walls destroyed!")
                    
                    break
        
        if self.bonus_food_timer > 0:
            self.bonus_food_timer -= 1
            if self.bonus_food_timer == 0:
                self.bonus_food_pos = None
        
        # Update respawn eggs in multiplayer
        if self.is_multiplayer and self.state == GameState.PLAYING:
            for player_id in list(self.respawning_players.keys()):
                egg_data = self.respawning_players[player_id]
                egg_data['timer'] -= 1
                
                # Find the snake for this player
                snake = next((s for s in self.snakes if s.player_id == player_id), None)
                
                # CPU players hatch immediately with smart direction
                if snake and snake.is_cpu and egg_data['direction'] is None:
                    egg_data['direction'] = self.get_safe_cpu_direction(egg_data['pos'])
                    self.respawn_player(player_id, egg_data['pos'], egg_data['direction'])
                    continue
                
                # Auto-hatch human players when timer expires (reaches 0)
                if egg_data['timer'] <= 0 and egg_data['direction'] is None:
                    # Choose a safe direction for auto-hatch
                    safe_direction = self.get_safe_cpu_direction(egg_data['pos'])
                    self.respawn_player(player_id, egg_data['pos'], safe_direction)
                    print(f"Auto-hatched player {player_id} with direction {safe_direction.name}")  # DEBUG
                    continue
                
                # Auto-hatch in boss mode
                if self.state == GameState.EGG_HATCHING:
                    if hasattr(self, 'boss_active') and self.boss_active:
                        self.hatch_egg(Direction.RIGHT)
                    else:
                        # Immediately hatch with random direction after 1 second
                        self.egg_timer = getattr(self, 'egg_timer', 0) + 1
                        if self.egg_timer > 60:  # 1 second
                            # Auto-hatch with a random direction
                            direction = random.choice([Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT])
                            self.hatch_egg(direction)    
                            self.respawn_player(player_id, egg_data['pos'], egg_data['direction'])
        
        self.move_timer += 1
        
        if self.is_multiplayer:
            # In multiplayer, each snake moves at its own pace based on speed_modifier
            for snake in self.snakes:
                if not snake.alive:
                    continue
                
                # Calculate individual snake speed
                # Base speed: 16 frames, modified by speed_modifier
                # Each apple: -2 frames (faster), each black apple: +3 frames (slower)
                base_interval = 16
                move_interval = max(2, base_interval + snake.speed_modifier)
                
                # Update snake's individual timer
                snake.move_timer += 1
                
                # Check if this snake should move
                if snake.move_timer >= move_interval:
                    # CPU AI decision making (right before movement)
                    if snake.is_cpu and snake.player_id not in self.respawning_players:
                        self.update_cpu_decision(snake)
                    
                    snake.move_timer = 0
                    snake.last_move_interval = move_interval  # Track for interpolation
                    snake.move()
                    
                    # Check wall and self-collision
                    # In adventure mode, check for level walls only; otherwise check boundaries
                    hit_wall = False
                    if self.game_mode == "adventure":
                        head = snake.body[0]
                        if head in self.level_walls:
                            hit_wall = True
                        # Check enemy walls (destroyable walls from boss super attack)
                        if hasattr(self, 'enemies') and self.enemies:
                            for enemy in self.enemies:
                                if enemy.alive and enemy.enemy_type == 'enemy_wall':
                                    if head == (enemy.grid_x, enemy.grid_y):
                                        hit_wall = True
                                        break
                        # Check self-collision
                        if snake.body[0] in snake.body[1:]:
                            hit_wall = True
                    else:
                        # Multiplayer mode - check walls and self-collision
                        head = snake.body[0]
                        
                        # Check multiplayer level walls
                        if hasattr(self, 'walls') and self.walls:
                            if head in self.walls:
                                hit_wall = True
                        
                        # Check self-collision
                        if snake.body[0] in snake.body[1:]:
                            hit_wall = True
                        
                        # Wrap around screen edges (no death from edges)
                        # This is handled automatically by the snake movement
                    
                    if hit_wall:
                        self.handle_player_death(snake)
                        continue
                    
                    # Check collision with other snakes' bodies
                    for other_snake in self.snakes:
                        if other_snake.player_id != snake.player_id and other_snake.alive:
                            if snake.body[0] in other_snake.body:
                                self.handle_player_death(snake)
                                break
        else:
            # Single player mode - speed based on level (except in adventure mode)
            if self.game_mode == "adventure":
                # Fixed speed in adventure mode (doesn't increase with level)
                move_interval = 16
            else:
                # Endless mode - speed increases with level
                move_interval = max(1, 16 - self.level // 2)
            
            # Don't move if player is frozen (during boss death sequence) or during respawn delay or if snake has no body
            if self.move_timer >= move_interval and not self.player_frozen and self.respawn_timer == 0 and len(self.snake.body) > 0:
                self.move_timer = 0
                self.snake.move()
                
                # Check collision (wall collision and self-collision) - single player
                head = self.snake.body[0]
                hit_wall = False
                
                # Check if player entered the boss zone (lower right quadrant - wormBoss only)
                if hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned and self.boss_data == 'wormBoss':
                    head_x, head_y = head
                    # Lower right quadrant: x >= 8 and y >= 8
                    if head_x >= 8 and head_y >= 8:
                        hit_wall = True
                        print("Player entered boss zone and was crushed!")
                
                # Check collision with boss minions (player head hitting any part of minion)
                if self.boss_minions:
                    for minion in self.boss_minions:
                        if minion.alive and head in minion.body:
                            hit_wall = True
                            print("Player collided with boss minion!")
                            break
                
                # In adventure mode, only check level walls (no boundary walls)
                if self.game_mode == "adventure":
                    if head in self.level_walls:
                        hit_wall = True
                    # Only check self-collision, not boundary walls
                    if self.snake.body[0] in self.snake.body[1:]:
                        hit_wall = True
                else:
                    # In endless mode, wrap around screen edges (no death from edges)
                    hit_wall = self.snake.check_collision(wrap_around=True)
                
                if hit_wall:
                    self.sound_manager.play('die')
                    self.lives -= 1
                    
                    # Spawn white particles on all body segments including head
                    for segment_x, segment_y in self.snake.body:
                        self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                            segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                            None, None, particle_type='white')
                    
                    if self.lives < 0:
                        self.sound_manager.play('no_lives')
                        self.music_manager.play_game_over_music()
                        self.state = GameState.GAME_OVER
                        self.game_over_timer = self.game_over_delay
                    else:
                        # In adventure mode, wait before going to egg hatching to clear visuals
                        if self.game_mode == "adventure":
                            self.respawn_timer = self.respawn_delay
                            # Clear the snake body immediately
                            self.snake.body = []
                        else:
                            # Go to egg hatching state for respawn
                            self.state = GameState.EGG_HATCHING
                            # Mark this as a respawn for boss battles
                            if hasattr(self, 'boss_active') and self.boss_active:
                                self.boss_egg_is_respawn = True
                                self.egg_timer = 0
                
                # Update enemies in adventure mode
                if self.game_mode == "adventure" and hasattr(self, 'enemies'):
                    for enemy in self.enemies:
                        if enemy.alive:
                            # Skip collision check if snake body is empty (during respawn delay)
                            if len(self.snake.body) > 0:
                                enemy.update(self.snake.body, self.level_walls, self.food_items)
                            else:
                                # Update without snake interaction during respawn
                                enemy.update([], self.level_walls, self.food_items)
                            
                            # Update enemy animation
                            if enemy.enemy_type.startswith('enemy_ant') and self.ant_frames:
                                # Ants only animate when moving
                                enemy.update_animation(len(self.ant_frames), self.ant_animation_speed)
                            elif enemy.enemy_type.startswith('enemy_spider') and self.spider_frames:
                                # Spiders only animate when moving
                                enemy.update_animation(len(self.spider_frames), self.spider_animation_speed)
                            elif enemy.enemy_type.startswith('enemy_scorpion') and self.scorpion_frames:
                                # Scorpions only animate when moving
                                enemy.update_animation(len(self.scorpion_frames), self.scorpion_animation_speed)
                            elif enemy.enemy_type.startswith('enemy_wasp') and self.wasp_frames:
                                # Wasps animate freely every frame (rapid wing flapping)
                                enemy.animation_frame = (enemy.animation_frame + 1) % len(self.wasp_frames)
                            
                            # Check if scorpion should fire stinger (when attack_charge_time hits 15, halfway through attack)
                            if enemy.enemy_type.startswith('enemy_scorpion') and enemy.is_attacking and enemy.attack_charge_time == 15:
                                # Spawn stinger projectile from scorpion's center
                                from game_core import ScorpionStinger
                                stinger = ScorpionStinger(
                                    enemy.grid_x + 1,  # Center of 2x2 scorpion
                                    enemy.grid_y + 1,
                                    enemy.attack_direction,
                                    self.scorpion_attack_frames
                                )
                                self.scorpion_stingers.append(stinger)
                            
                            # Check if beetle should launch larvae (when attack_charge_time hits 30, halfway through attack)
                            if enemy.enemy_type.startswith('enemy_beetle') and enemy.is_attacking and enemy.attack_charge_time == 30:
                                # Spawn larvae projectiles in 4 cardinal directions
                                from game_core import BeetleLarvae, Direction
                                for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                                    larvae = BeetleLarvae(
                                        enemy.grid_x,
                                        enemy.grid_y,
                                        direction,
                                        self.beetle_larvae_frames
                                    )
                                    self.beetle_larvae.append(larvae)
                                print("Beetle launched 4 larvae projectiles!")
                            
                            # Check collision with snake (only if snake has a body)
                            if len(self.snake.body) > 0:
                                collision_type = enemy.check_collision_with_snake(self.snake.body[0], self.snake.body)
                            else:
                                collision_type = None
                            
                            if collision_type == 'head':
                                # Snake head hit enemy - snake dies
                                self.sound_manager.play('die')
                                self.lives -= 1
                                
                                # Spawn white particles on all snake body segments
                                for segment_x, segment_y in self.snake.body:
                                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                        None, None, particle_type='white')
                                
                                if self.lives < 0:
                                    self.sound_manager.play('no_lives')
                                    self.music_manager.play_game_over_music()
                                    self.state = GameState.GAME_OVER
                                    self.game_over_timer = self.game_over_delay
                                else:
                                    # In adventure mode, wait before going to egg hatching to clear visuals
                                    if self.game_mode == "adventure":
                                        self.respawn_timer = self.respawn_delay
                                        # Clear the snake body immediately
                                        self.snake.body = []
                                    else:
                                        # Go to egg hatching state for respawn
                                        self.state = GameState.EGG_HATCHING
                                        # Mark this as a respawn for boss battles
                                        if hasattr(self, 'boss_active') and self.boss_active:
                                            self.boss_egg_is_respawn = True
                                            self.egg_timer = 0
                                break  # Don't check more enemies this frame
                            
                            elif collision_type == 'body':
                                # Enemy hit snake body - enemy dies
                                enemy.alive = False
                                # Spawn white particles where enemy died
                                # Scorpions are 2x2, so spawn 4 particles across their body
                                if enemy.enemy_type.startswith('enemy_scorpion'):
                                    # Spawn particles at all 4 grid cells the scorpion occupies
                                    for dx in range(2):
                                        for dy in range(2):
                                            self.create_particles(
                                                (enemy.grid_x + dx) * GRID_SIZE + GRID_SIZE // 2,
                                                (enemy.grid_y + dy) * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                None, None, particle_type='white')
                                else:
                                    # Regular enemies spawn 1 particle
                                    self.create_particles(enemy.grid_x * GRID_SIZE + GRID_SIZE // 2,
                                                        enemy.grid_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                        None, None, particle_type='white')
        
        # Check Frog Boss collision with player
        # Don't check collision during egg hatching
        if self.boss_active and self.boss_data == 'frog' and self.boss_spawned and self.state == GameState.PLAYING:
            if len(self.snake.body) > 0 and not self.boss_defeated:
                player_head = self.snake.body[0]
                
                # Check collision with frog body (when on ground and at valid position)
                if self.frog_state == 'landed' and not self.frog_is_invulnerable:
                    frog_x = int(self.frog_position[0])
                    frog_y = int(self.frog_position[1])
                    
                    # Only check collision if frog is within valid grid bounds
                    if (0 <= frog_x < GRID_WIDTH - 3 and 0 <= frog_y < GRID_HEIGHT - 3):
                        # Frog occupies 4x4 grid cells (200% size)
                        frog_cells = []
                        for dx in range(4):
                            for dy in range(4):
                                frog_cells.append((frog_x + dx, frog_y + dy))
                        
                        # Check head collision - instant death
                        if player_head in frog_cells:
                            # Player dies from touching frog with head
                            self.sound_manager.play('die')
                            self.lives -= 1
                            
                            # Spawn white particles on all snake body segments
                            for segment_x, segment_y in self.snake.body:
                                self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                    segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    None, None, particle_type='white')
                            
                            if self.lives <= 0:
                                self.music_manager.play_game_over_music()
                                self.state = GameState.GAME_OVER
                                self.game_over_timer = self.game_over_delay
                            else:
                                self.state = GameState.EGG_HATCHING
                                if hasattr(self, 'boss_active') and self.boss_active:
                                    self.boss_egg_is_respawn = True
                                    self.egg_timer = 0
                                    # Generate random egg respawn position
                                    self.boss_egg_respawn_pos = self.find_random_unoccupied_position()
                                    print("Generated random egg respawn position: {}".format(self.boss_egg_respawn_pos))
                            print("Player died from touching Frog Boss!")
                        else:
                            # Check body collision - remove segments from hit point to tail
                            for frog_cell in frog_cells:
                                if frog_cell in self.snake.body[1:]:
                                    # Find which body segment was hit
                                    body_segment_index = self.snake.body.index(frog_cell)
                                    
                                    # Remove player body segments from hit point to tail
                                    removed_body_count = len(self.snake.body) - body_segment_index
                                    self.snake.body = self.snake.body[:body_segment_index]
                                    
                                    # Create particles at hit location
                                    hit_x = frog_cell[0] * GRID_SIZE + GRID_SIZE // 2
                                    hit_y = frog_cell[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                                    self.create_particles(hit_x, hit_y, RED, 10)
                                    self.sound_manager.play('eat_fruit')
                                    
                                    print("Frog landed on player body! {} body segments lost".format(removed_body_count))
                                    break  # Only process one collision per frame
                
                # Check collision with tongue (any segment kills on head contact)
                if len(self.frog_tongue_segments) > 0:
                    # Check if any tongue segment is in the same grid cell as player head
                    tongue_hit = False
                    for tongue_seg in self.frog_tongue_segments:
                        tongue_grid = (int(round(tongue_seg[0])), int(round(tongue_seg[1])))
                        if tongue_grid == player_head:
                            tongue_hit = True
                            break
                    if tongue_hit:
                        # Player dies from touching tongue with head
                        self.sound_manager.play('die')
                        self.lives -= 1
                        
                        # Spawn white particles on all snake body segments
                        for segment_x, segment_y in self.snake.body:
                            self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                None, None, particle_type='white')
                        
                        if self.lives <= 0:
                            self.music_manager.play_game_over_music()
                            self.state = GameState.GAME_OVER
                            self.game_over_timer = self.game_over_delay
                        else:
                            self.state = GameState.EGG_HATCHING
                            if hasattr(self, 'boss_active') and self.boss_active:
                                self.boss_egg_is_respawn = True
                                self.egg_timer = 0
                                # Generate random egg respawn position
                                self.boss_egg_respawn_pos = self.find_random_unoccupied_position()
                                print("Generated random egg respawn position: {}".format(self.boss_egg_respawn_pos))
                        print("Player died from touching tongue!")
        
        # Food collection (outside movement block)
        if self.is_multiplayer:
            # Check if any player ate food from food_items list
            for snake in self.snakes:
                if not snake.alive:
                    continue
                
                # Check all food items
                for i, (food_pos, food_type) in enumerate(self.food_items):
                    if snake.body[0] == food_pos:
                        fx, fy = food_pos
                        
                        if food_type == 'worm':
                            # Regular worm - grow normally
                            self.sound_manager.play('eat_fruit')
                            snake.grow(1)
                            self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, RED, 10)
                        elif food_type == 'apple':
                            # Apple - speed up
                            self.sound_manager.play('powerup')
                            snake.speed_modifier -= 2  # Faster (lower interval)
                            print("Player {} ate apple, speed_modifier: {}".format(snake.player_id + 1, snake.speed_modifier))
                            self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                None, None, particle_type='rainbow')
                        elif food_type == 'black_apple':
                            # Black apple - slow down
                            self.sound_manager.play('power_down')
                            snake.speed_modifier += 3  # Slower (higher interval)
                            print("Player {} ate black apple, speed_modifier: {}".format(snake.player_id + 1, snake.speed_modifier))
                            self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                None, None, particle_type='white')
                        
                        # Remove eaten food
                        self.food_items.pop(i)
                        
                        # Spawn replacement food based on item frequency setting
                        freq = self.lobby_settings['item_frequency']
                        ran = random.random()
                        
                        if freq == 0:  # Low - mostly worms
                            if ran < 0.75:
                                self.spawn_food_item('worm')
                            elif ran < 0.95:
                                self.spawn_food_item('apple')
                            # Black apples rare
                        elif freq == 1:  # Normal
                            if ran < 0.6:
                                self.spawn_food_item('worm')
                            elif ran < 0.85:
                                self.spawn_food_item('apple')
                            else:
                                self.spawn_food_item('black_apple')
                        else:  # High - more variety
                            if ran < 0.5:
                                self.spawn_food_item('worm')
                            elif ran < 0.8:
                                self.spawn_food_item('apple')
                            else:
                                self.spawn_food_item('black_apple')
                        
                        break  # Only eat one food per frame
        else:
            # Single player food collection
            if self.move_timer == 0 and len(self.snake.body) > 0:  # Only check after movement and if snake has body
                # Check if snake ate any food
                food_eaten = False
                
                if self.game_mode == "adventure":
                    # In Adventure mode, check food_items list for worms and bonus fruits
                    for i, (food_pos, food_type) in enumerate(self.food_items):
                        if self.snake.body[0] == food_pos:
                            # Handle different food types
                            if food_type == 'bonus':
                                # Bonus fruit gives extra points and special effects
                                self.sound_manager.play('powerup')
                                self.snake.grow(self.get_difficulty_length_modifier())
                                base_points = (47 + len(self.snake.body)) * self.level
                                self.score += int(base_points * self.get_score_multiplier())
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    None, None, particle_type='rainbow')
                                # Remove bonus fruit from list
                                self.food_items.pop(i)
                                self.bonus_fruits_collected += 1
                                # Bonus fruit doesn't count toward worms_required
                            elif food_type == 'coin':
                                # Coin collectible - adds 1 coin to persistent total
                                self.sound_manager.play('pickupCoin')
                                self.total_coins += 1
                                self.save_unlocked_levels()  # Save coins immediately
                                
                                # Check for Gold Farmer achievement (1000 coins)
                                if self.total_coins >= 1000:
                                    self.unlock_achievement(6)
                                
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    None, None, particle_type='yellow')
                                # Remove coin from list
                                self.food_items.pop(i)
                                # Coins don't grow snake or count toward completion
                            elif food_type == 'diamond':
                                # Diamond collectible - adds 10 coins to persistent total
                                self.sound_manager.play('pickupDiamond')
                                self.total_coins += 10
                                self.save_unlocked_levels()  # Save coins immediately
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    None, None, particle_type='yellow')
                                # Remove diamond from list
                                self.food_items.pop(i)
                                # Diamonds don't grow snake or count toward completion
                            elif food_type == 'isotope':
                                # Isotope collectible - grants shooting ability
                                self.sound_manager.play('powerup')
                                self.snake.can_shoot = True
                                # Grow snake when collecting isotope
                                if self.game_mode == 'adventure':
                                    self.snake.grow(5)  # Grant 5 segments in adventure mode
                                else:
                                    self.snake.grow(10)  # Grant 10 segments in boss mode
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    NEON_PURPLE, 15)
                                # Remove isotope from list
                                self.food_items.pop(i)
                                # Show "Press A to Fire" message for 5 seconds
                                self.isotope_message_timer = 300  # 5 seconds at 60 FPS
                                # Isotope doesn't count toward worms collected for level completion
                            else:
                                # Regular worm
                                self.sound_manager.play('eat_fruit')
                                self.snake.grow(1)
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, RED, 10)
                                # Remove worm from list
                                self.food_items.pop(i)
                                self.worms_collected += 1
                                
                                # In boss battles, respawn worms less frequently (30% chance)
                                if hasattr(self, 'boss_active') and self.boss_active:
                                    if random.random() < 0.3:  # 30% chance to spawn worm
                                        self.spawn_adventure_food()
                                
                                # Check if all worms collected (but not in boss mode)
                                # In boss mode, level only ends when boss is defeated
                                if self.worms_collected >= self.worms_required and not (hasattr(self, 'boss_active') and self.boss_active):
                                    self.sound_manager.play('level_up')
                                    
                                    # Calculate completion percentage for adventure mode
                                    # Starting length is 3 segments
                                    starting_length = 3
                                    # Include pending growth segments in the final count
                                    current_segments = len(self.snake.body) + self.snake.grow_pending
                                    segments_gained = current_segments - starting_length
                                    
                                    total_items = self.worms_required + self.total_bonus_fruits
                                    items_collected = self.worms_collected + self.bonus_fruits_collected
                                    
                                    # Completion = (items + segments) / (total_items * 2) * 100
                                    max_possible = total_items + total_items
                                    actual_earned = items_collected + segments_gained
                                    self.completion_percentage = int((actual_earned / max_possible) * 100) if max_possible > 0 else 0
                                    self.final_segments = current_segments
                                    
                                    # Save level score for adventure mode (still track for backwards compatibility)
                                    self.is_new_level_high_score = self.update_level_score(self.current_adventure_level, self.completion_percentage)
                                    # Unlock next level
                                    self.unlock_level(self.current_adventure_level + 1)
                                    # Play victory jingle
                                    self.music_manager.play_victory_jingle()
                                    self.state = GameState.LEVEL_COMPLETE
                            
                            food_eaten = True
                            break
                else:
                    # Endless mode - original logic
                    if self.snake.body[0] == self.food_pos:
                        self.sound_manager.play('eat_fruit')
                        self.snake.grow(self.get_difficulty_length_modifier())
                        base_points = (7 + len(self.snake.body)) *  self.level
                        self.score += int(base_points * self.get_score_multiplier())
                        fx, fy = self.food_pos
                        self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                            fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, RED, 10)
                        self.spawn_food()
                        food_eaten = True
                
                if food_eaten and self.game_mode == "endless":
                
                    # Check if snake filled the entire grid (GRID_WIDTH * GRID_HEIGHT = 225 cells)
                    max_snake_length = GRID_WIDTH * GRID_HEIGHT
                    if len(self.snake.body) >= max_snake_length:
                        self.sound_manager.play('fullSnake')
                        # Spawn rainbow particles on all body segments including head
                        for segment_x, segment_y in self.snake.body:
                            self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                                segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                None, None, particle_type='rainbow')
                        self.score += int(1000 * self.level * self.get_score_multiplier())
                        self.lives = min(99, self.lives + 10)  # Award 10 extra lives
                        # Reset snake after this incredible achievement
                        self.snake.reset()
                        self.spawn_food()
                        self.spawn_bonus_food()
                        self.spawn_bonus_food()
                        self.spawn_bonus_food()
                
                    # Increment fruit counter and check if player leveled up (20 fruits per level)
                    self.fruits_eaten_this_level += 1
                    if self.fruits_eaten_this_level >= 12:
                        self.sound_manager.play('level_up')
                        # In adventure mode, play victory jingle; in endless mode, just continue
                        if self.game_mode == "adventure":
                            self.music_manager.play_victory_jingle()
                        self.state = GameState.LEVEL_COMPLETE
                    ran = random.random()
                    if ran < 0.3:
                        self.spawn_bonus_food()
                    if ran < 0.2:
                        self.spawn_bonus_food()
                    if ran < 0.1:
                        self.spawn_bonus_food()
            
            # Bonus food collection
            if self.bonus_food_pos:
                if self.is_multiplayer:
                    for snake in self.snakes:
                        if not snake.alive:
                            continue
                        if snake.body[0] == self.bonus_food_pos:
                            self.sound_manager.play('powerup')
                            snake.grow(self.get_difficulty_length_modifier())
                            base_points = (47 + len(snake.body)) * self.level
                            snake.score += int(base_points * self.get_score_multiplier())
                            bx, by = self.bonus_food_pos
                            self.create_particles(bx * GRID_SIZE + GRID_SIZE // 2,
                                                by * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                None, None, particle_type='rainbow')
                            self.bonus_food_pos = None
                            self.bonus_food_timer = 0
                            break
                else:
                    if self.snake.body[0] == self.bonus_food_pos:
                        self.sound_manager.play('powerup')
                        self.snake.grow(self.get_difficulty_length_modifier())
                        base_points = (47 + len(self.snake.body)) * self.level
                        self.score += int(base_points * self.get_score_multiplier())
                        bx, by = self.bonus_food_pos
                        self.create_particles(bx * GRID_SIZE + GRID_SIZE // 2,
                                            by * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                            None, None, particle_type='rainbow')
                        self.bonus_food_pos = None
                        self.bonus_food_timer = 0
                
                # Note: Bonus food gives extra points but doesn't count toward level progression
    
    def handle_input(self):
        # Check for Start + Select combo to quit (gamepad)
        if self.joystick:
            start_pressed = self.joystick.get_button(GamepadButton.BTN_START)
            select_pressed = self.joystick.get_button(GamepadButton.BTN_SELECT)
            if start_pressed and select_pressed:
                pygame.event.set_grab(False)  # Release input grab before quitting
                pygame.quit()
                exit()
        
        keys = pygame.key.get_pressed()
        
        if self.state == GameState.EGG_HATCHING:
            # Egg hatching - choose direction
            # Network clients send hatch input to host
            if self.is_network_game and self.network_manager.is_client():
                if hasattr(self, 'network_player_id'):
                    new_direction = None
                    if keys[pygame.K_UP]:
                        new_direction = Direction.UP
                    elif keys[pygame.K_DOWN]:
                        new_direction = Direction.DOWN
                    elif keys[pygame.K_LEFT]:
                        new_direction = Direction.LEFT
                    elif keys[pygame.K_RIGHT]:
                        new_direction = Direction.RIGHT
                    
                    if new_direction:
                        print(f"Client sending hatch input: {new_direction.name}")  # DEBUG
                        self.send_input_to_host(new_direction)  # Send hatch direction
                return
            
            # Local game or host: directly hatch
            if keys[pygame.K_UP]:
                self.hatch_egg(Direction.UP)
            elif keys[pygame.K_DOWN]:
                self.hatch_egg(Direction.DOWN)
            elif keys[pygame.K_LEFT]:
                self.hatch_egg(Direction.LEFT)
            elif keys[pygame.K_RIGHT]:
                self.hatch_egg(Direction.RIGHT)
        elif self.state == GameState.PLAYING:
            # Special handling for network clients - they ALWAYS send inputs to host
            if self.is_network_game and self.network_manager.is_client():
                # Client: Send input to host instead of controlling locally
                if hasattr(self, 'network_player_id'):
                    # Track last sent direction to avoid spamming same input
                    if not hasattr(self, 'last_sent_direction'):
                        self.last_sent_direction = None
                    
                    new_direction = None
                    
                    # Check keyboard input
                    if keys[pygame.K_UP]:
                        new_direction = Direction.UP
                    elif keys[pygame.K_DOWN]:
                        new_direction = Direction.DOWN
                    elif keys[pygame.K_LEFT]:
                        new_direction = Direction.LEFT
                    elif keys[pygame.K_RIGHT]:
                        new_direction = Direction.RIGHT
                    
                    # Check gamepad input (D-pad and analog stick)
                    if new_direction is None and self.joystick:
                        # Check D-pad (hat)
                        if self.joystick.get_numhats() > 0:
                            hat = self.joystick.get_hat(0)
                            if hat[1] == 1:
                                new_direction = Direction.UP
                            elif hat[1] == -1:
                                new_direction = Direction.DOWN
                            elif hat[0] == -1:
                                new_direction = Direction.LEFT
                            elif hat[0] == 1:
                                new_direction = Direction.RIGHT
                        
                        # Check analog stick if no D-pad input
                        if new_direction is None and self.joystick.get_numaxes() >= 2:
                            axis_x = self.joystick.get_axis(0)
                            axis_y = self.joystick.get_axis(1)
                            dead_zone = 0.5
                            
                            if abs(axis_x) > dead_zone or abs(axis_y) > dead_zone:
                                if abs(axis_x) > abs(axis_y):
                                    if axis_x < -dead_zone:
                                        new_direction = Direction.LEFT
                                    elif axis_x > dead_zone:
                                        new_direction = Direction.RIGHT
                                else:
                                    if axis_y < -dead_zone:
                                        new_direction = Direction.UP
                                    elif axis_y > dead_zone:
                                        new_direction = Direction.DOWN
                    
                    # Only send if direction changed
                    if new_direction and new_direction != self.last_sent_direction:
                        print(f"Client sending input: {new_direction.name}")  # DEBUG
                        self.send_input_to_host(new_direction)
                        self.last_sent_direction = new_direction
                return  # Don't process local input for clients
            
            if self.is_multiplayer:
                
                # Handle input for each player based on their controller
                for i, snake in enumerate(self.snakes):
                    # Check if this player is respawning (has an egg)
                    if snake.player_id in self.respawning_players:
                        egg_data = self.respawning_players[snake.player_id]
                        
                        if i < len(self.player_controllers):
                            controller_type, controller_index = self.player_controllers[i]
                            
                            if controller_type == 'keyboard':
                                # Handle egg direction selection with keyboard
                                if keys[pygame.K_UP]:
                                    egg_data['direction'] = Direction.UP
                                    self.respawn_player(snake.player_id, egg_data['pos'], egg_data['direction'])
                                elif keys[pygame.K_DOWN]:
                                    egg_data['direction'] = Direction.DOWN
                                    self.respawn_player(snake.player_id, egg_data['pos'], egg_data['direction'])
                                elif keys[pygame.K_LEFT]:
                                    egg_data['direction'] = Direction.LEFT
                                    self.respawn_player(snake.player_id, egg_data['pos'], egg_data['direction'])
                                elif keys[pygame.K_RIGHT]:
                                    egg_data['direction'] = Direction.RIGHT
                                    self.respawn_player(snake.player_id, egg_data['pos'], egg_data['direction'])
                        continue
                    
                    if not snake.alive:
                        continue
                    
                    if i < len(self.player_controllers):
                        controller_type, controller_index = self.player_controllers[i]
                        
                        if controller_type == 'keyboard':
                            # Keyboard controls for this player
                            if keys[pygame.K_UP]:
                                snake.change_direction(Direction.UP)
                            elif keys[pygame.K_DOWN]:
                                snake.change_direction(Direction.DOWN)
                            elif keys[pygame.K_LEFT]:
                                snake.change_direction(Direction.LEFT)
                            elif keys[pygame.K_RIGHT]:
                                snake.change_direction(Direction.RIGHT)
                        elif controller_type == 'gamepad' and controller_index < len(self.joysticks):
                            # Gamepad controls for this player
                            joystick = self.joysticks[controller_index]
                            chosen_direction = None
                            
                            # Check hat (D-pad) if available
                            if joystick.get_numhats() > 0:
                                hat = joystick.get_hat(0)
                                if hat[1] == 1:
                                    chosen_direction = Direction.UP
                                elif hat[1] == -1:
                                    chosen_direction = Direction.DOWN
                                elif hat[0] == -1:
                                    chosen_direction = Direction.LEFT
                                elif hat[0] == 1:
                                    chosen_direction = Direction.RIGHT
                            # Otherwise use analog stick
                            elif joystick.get_numaxes() >= 2:
                                axis_x = joystick.get_axis(0)
                                axis_y = joystick.get_axis(1)
                                dead_zone = 0.5
                                
                                if abs(axis_x) > dead_zone or abs(axis_y) > dead_zone:
                                    if abs(axis_x) > abs(axis_y):
                                        if axis_x < -dead_zone:
                                            chosen_direction = Direction.LEFT
                                        elif axis_x > dead_zone:
                                            chosen_direction = Direction.RIGHT
                                    else:
                                        if axis_y < -dead_zone:
                                            chosen_direction = Direction.UP
                                        elif axis_y > dead_zone:
                                            chosen_direction = Direction.DOWN
                            
                            # Apply direction (either for egg or snake)
                            if chosen_direction:
                                if snake.player_id in self.respawning_players:
                                    egg_data = self.respawning_players[snake.player_id]
                                    egg_data['direction'] = chosen_direction
                                    self.respawn_player(snake.player_id, egg_data['pos'], chosen_direction)
                                else:
                                    snake.change_direction(chosen_direction)
            else:
                # Single player mode - use original controls
                if keys[pygame.K_UP]:
                    self.snake.change_direction(Direction.UP)
                elif keys[pygame.K_DOWN]:
                    self.snake.change_direction(Direction.DOWN)
                elif keys[pygame.K_LEFT]:
                    self.snake.change_direction(Direction.LEFT)
                elif keys[pygame.K_RIGHT]:
                    self.snake.change_direction(Direction.RIGHT)
        
        # Only poll hat if joystick has one (otherwise rely on JOYHATMOTION events or axes)
        # But skip this in multiplayer mode - controller mapping is handled above
        if not self.is_multiplayer and self.joystick and self.joystick_has_hat:
            hat = self.joystick.get_hat(0)
            if self.state == GameState.EGG_HATCHING:
                if hat[1] == 1:
                    self.hatch_egg(Direction.UP)
                elif hat[1] == -1:
                    self.hatch_egg(Direction.DOWN)
                elif hat[0] == -1:
                    self.hatch_egg(Direction.LEFT)
                elif hat[0] == 1:
                    self.hatch_egg(Direction.RIGHT)
            elif self.state == GameState.PLAYING:
                if hat[1] == 1:
                    self.snake.change_direction(Direction.UP)
                elif hat[1] == -1:
                    self.snake.change_direction(Direction.DOWN)
                elif hat[0] == -1:
                    self.snake.change_direction(Direction.LEFT)
                elif hat[0] == 1:
                    self.snake.change_direction(Direction.RIGHT)
        
        # For joysticks without hats, use axes (analog stick)
        # But skip this in multiplayer mode - controller mapping is handled above
        elif not self.is_multiplayer and self.joystick and not self.joystick_has_hat:
            if self.joystick.get_numaxes() >= 2:
                axis_x = self.joystick.get_axis(0)
                axis_y = self.joystick.get_axis(1)
                
                # Use a threshold to avoid drift
                threshold = 0.5
                
                # Check if axis is in neutral position
                is_neutral = abs(axis_x) < threshold and abs(axis_y) < threshold
                
                if self.state == GameState.EGG_HATCHING:
                    # Prioritize the axis with larger absolute value
                    if abs(axis_y) > abs(axis_x) and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.hatch_egg(Direction.UP)
                        elif axis_y > threshold:
                            self.hatch_egg(Direction.DOWN)
                    elif abs(axis_x) > threshold:
                        if axis_x < -threshold:
                            self.hatch_egg(Direction.LEFT)
                        elif axis_x > threshold:
                            self.hatch_egg(Direction.RIGHT)
                elif self.state == GameState.PLAYING:
                    # Prioritize the axis with larger absolute value
                    if abs(axis_y) > abs(axis_x) and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.snake.change_direction(Direction.UP)
                        elif axis_y > threshold:
                            self.snake.change_direction(Direction.DOWN)
                    elif abs(axis_x) > threshold:
                        if axis_x < -threshold:
                            self.snake.change_direction(Direction.LEFT)
                        elif axis_x > threshold:
                            self.snake.change_direction(Direction.RIGHT)
                
                # Handle menu navigation with debouncing
                elif self.state == GameState.MENU:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.SINGLE_PLAYER_MENU:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.single_player_selection = (self.single_player_selection - 1) % len(self.single_player_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.single_player_selection = (self.single_player_selection + 1) % len(self.single_player_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.MULTIPLAYER_MENU:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.multiplayer_menu_selection = (self.multiplayer_menu_selection - 1) % len(self.multiplayer_menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.multiplayer_menu_selection = (self.multiplayer_menu_selection + 1) % len(self.multiplayer_menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.NETWORK_MENU:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.network_menu_selection = (self.network_menu_selection - 1) % len(self.network_menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.network_menu_selection = (self.network_menu_selection + 1) % len(self.network_menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.MULTIPLAYER_LOBBY:
                    # Only host can navigate and change settings in network games
                    can_change = not self.is_network_game or self.network_manager.is_host()
                    if can_change and self.axis_was_neutral:
                        if abs(axis_y) > threshold:
                            if axis_y < -threshold:
                                self.lobby_selection = (self.lobby_selection - 1) % 8  # 4 settings + 4 players
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                            elif axis_y > threshold:
                                self.lobby_selection = (self.lobby_selection + 1) % 8
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                        elif abs(axis_x) > threshold:
                            # Left/right to change settings
                            direction = 1 if axis_x > threshold else -1
                            self.change_lobby_setting(self.lobby_selection, direction)
                            self.axis_was_neutral = False
                
                elif self.state == GameState.NETWORK_CLIENT_LOBBY:
                    # Analog stick for server list navigation
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            # Up - navigate up in server list
                            if len(self.discovered_servers) > 0 and self.server_selection > 0:
                                self.server_selection -= 1
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                        elif axis_y > threshold:
                            # Down - navigate down in server list
                            if len(self.discovered_servers) > 0 and self.server_selection < len(self.discovered_servers) - 1:
                                self.server_selection += 1
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                
                elif self.state == GameState.EXTRAS_MENU:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.extras_menu_selection = (self.extras_menu_selection - 1) % len(self.extras_menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.extras_menu_selection = (self.extras_menu_selection + 1) % len(self.extras_menu_options)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.MUSIC_PLAYER:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.music_player_selection = (self.music_player_selection - 1) % len(self.music_player_tracks)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.music_player_selection = (self.music_player_selection + 1) % len(self.music_player_tracks)
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.ADVENTURE_LEVEL_SELECT:
                    if self.axis_was_neutral:
                        # Grid navigation (8 columns)
                        cols = 8
                        if abs(axis_x) > threshold:
                            if axis_x < -threshold:
                                self.adventure_level_selection = max(0, self.adventure_level_selection - 1)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                            elif axis_x > threshold:
                                self.adventure_level_selection = min(self.total_levels - 1, self.adventure_level_selection + 1)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                        elif abs(axis_y) > threshold:
                            if axis_y < -threshold:
                                self.adventure_level_selection = max(0, self.adventure_level_selection - cols)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                            elif axis_y > threshold:
                                self.adventure_level_selection = min(self.total_levels - 1, self.adventure_level_selection + cols)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                
                elif self.state == GameState.DIFFICULTY_SELECT:
                    if self.axis_was_neutral and abs(axis_y) > threshold:
                        if axis_y < -threshold:
                            self.difficulty_selection = (self.difficulty_selection - 1) % 3
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                        elif axis_y > threshold:
                            self.difficulty_selection = (self.difficulty_selection + 1) % 3
                            self.sound_manager.play('blip_select')
                            self.axis_was_neutral = False
                
                elif self.state == GameState.HIGH_SCORE_ENTRY:
                    if self.axis_was_neutral:
                        if abs(axis_x) > threshold:
                            if axis_x < -threshold:
                                self.keyboard_selection[1] = max(0, self.keyboard_selection[1] - 1)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                            elif axis_x > threshold:
                                self.keyboard_selection[1] = min(9, self.keyboard_selection[1] + 1)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                        elif abs(axis_y) > threshold:
                            if axis_y < -threshold:
                                self.keyboard_selection[0] = max(0, self.keyboard_selection[0] - 1)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                            elif axis_y > threshold:
                                self.keyboard_selection[0] = min(3, self.keyboard_selection[0] + 1)
                                self.sound_manager.play('blip_select')
                                self.axis_was_neutral = False
                
                # Reset neutral flag when axis returns to center
                if is_neutral:
                    self.axis_was_neutral = True
    
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            # Skip splash screen on any key press
            if self.state == GameState.SPLASH:
                self.state = GameState.MENU
                # Ensure theme music is playing
                if not self.music_manager.theme_mode:
                    self.music_manager.play_theme()
                return True
            
            # Skip intro with ESC, Enter, or any other key
            if self.state == GameState.INTRO:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.intro_seen = True
                    self.save_unlocked_levels()
                    self.state = GameState.ADVENTURE_LEVEL_SELECT
                    self.adventure_level_selection = 0
                return True
            
            # Skip outro with ESC, Enter, or Space
            if self.state == GameState.OUTRO:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.state = GameState.CREDITS
                return True
            
            if self.state == GameState.MENU:
                if event.key == pygame.K_UP:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    self.select_menu_option()
            elif self.state == GameState.SINGLE_PLAYER_MENU:
                if event.key == pygame.K_UP:
                    self.single_player_selection = (self.single_player_selection - 1) % len(self.single_player_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.single_player_selection = (self.single_player_selection + 1) % len(self.single_player_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    self.select_single_player_option()
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.EXTRAS_MENU:
                if event.key == pygame.K_UP:
                    self.extras_menu_selection = (self.extras_menu_selection - 1) % len(self.extras_menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.extras_menu_selection = (self.extras_menu_selection + 1) % len(self.extras_menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    self.select_extras_option()
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.ADVENTURE_LEVEL_SELECT:
                cols = 8
                if event.key == pygame.K_LEFT:
                    self.adventure_level_selection = max(0, self.adventure_level_selection - 1)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RIGHT:
                    self.adventure_level_selection = min(self.total_levels - 1, self.adventure_level_selection + 1)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_UP:
                    self.adventure_level_selection = max(0, self.adventure_level_selection - cols)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.adventure_level_selection = min(self.total_levels - 1, self.adventure_level_selection + cols)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    # Load and start the selected level
                    level_num = self.adventure_level_selection + 1
                    # Only allow playing unlocked levels
                    if self.is_level_unlocked(level_num):
                        if self.load_level(level_num):
                            self.sound_manager.play('start_game')
                            self.lives = 3  # Reset lives when starting a level
                            self.state = GameState.EGG_HATCHING
                            self.score = 0
                            self.level = level_num
                    else:
                        # Play error sound if level is locked
                        self.sound_manager.play('blip_select')
                elif event.key == pygame.K_y:
                    # View intro if available
                    if len(self.intro_images) > 0:
                        self.sound_manager.play('blip_select')
                        self.start_intro()
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.SINGLE_PLAYER_MENU
            elif self.state == GameState.PLAYING:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PAUSED
                elif event.key == pygame.K_SPACE:
                    # Shooting in adventure mode
                    if self.game_mode == "adventure" and self.snake.can_shoot:
                        # Check if player has enough segments (need more than 3)
                        if len(self.snake.body) > 3:
                            # Fire a bullet in the current direction
                            head_x, head_y = self.snake.body[0]
                            bullet = Bullet(head_x, head_y, self.snake.direction)
                            self.bullets.append(bullet)
                            # Remove a segment from the snake
                            if self.snake.body:
                                self.snake.body.pop()
                            # Play laser shoot sound
                            self.sound_manager.play('laser_shoot')
                            # If segments are now 3 or less, lose shooting ability
                            if len(self.snake.body) <= 3:
                                self.snake.can_shoot = False
            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    # Exit game - for network games, use special handling
                    if self.is_network_game:
                        self.exit_network_game()
                    elif self.is_multiplayer:
                        # Local multiplayer - return to multiplayer menu
                        self.state = GameState.MULTIPLAYER_MENU
                    else:
                        # Single player - return to appropriate menu
                        self.music_manager.play_theme()
                        if self.game_mode == "adventure":
                            self.state = GameState.ADVENTURE_LEVEL_SELECT
                        else:
                            self.state = GameState.MENU
            elif self.state == GameState.GAME_OVER:
                # Only allow input after the 3-second timer expires
                if self.game_over_timer == 0 and event.key == pygame.K_RETURN:
                    if self.is_network_game:
                        # Network game - only host can progress
                        if self.network_manager.is_host():
                            self.sound_manager.play('blip_select')
                            return_msg = create_return_to_lobby_message()
                            self.network_manager.broadcast_to_clients(return_msg)
                            self.state = GameState.MULTIPLAYER_LOBBY
                            self.multiplayer_end_timer_phase = 0
                            self.broadcast_lobby_state()
                        # Client ignores input - waits for host
                    elif self.is_multiplayer:
                        # Local multiplayer - go back to lobby
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MULTIPLAYER_LOBBY
                    elif self.game_mode == "adventure":
                        # Adventure mode - reset lives and go back to level select
                        self.sound_manager.play('blip_select')
                        self.lives = 3
                        self.music_manager.stop_game_over_music()
                        self.music_manager.play_theme()
                        self.state = GameState.ADVENTURE_LEVEL_SELECT
                    else:
                        # Endless mode - reset game and go to menu
                        self.reset_game()
                        self.state = GameState.MENU
                        # Returning to menu - play theme music
                        self.music_manager.stop_game_over_music()
                        self.music_manager.play_theme()
            elif self.state == GameState.LEVEL_COMPLETE:
                if event.key == pygame.K_RETURN:
                    # Adventure mode returns to level select, endless continues to next level
                    if self.game_mode == "adventure":
                        self.lives = 3  # Reset lives after completing a level
                        self.state = GameState.ADVENTURE_LEVEL_SELECT
                        # Stop victory jingle and start theme music
                        pygame.mixer.music.stop()
                        self.music_manager.play_theme()
                    else:
                        self.next_level()
            elif self.state == GameState.CREDITS:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    # Return to extras menu if accessed from there
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
                    # Play theme music
                    if not self.music_manager.theme_mode:
                        self.music_manager.play_theme()
            elif self.state == GameState.ACHIEVEMENTS:
                achievements = self.get_achievement_list()
                if event.key == pygame.K_UP and achievements:
                    self.achievement_selection = (self.achievement_selection - 1) % len(achievements)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN and achievements:
                    self.achievement_selection = (self.achievement_selection + 1) % len(achievements)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
            elif self.state == GameState.MUSIC_PLAYER:
                if event.key == pygame.K_UP:
                    self.music_player_selection = (self.music_player_selection - 1) % len(self.music_player_tracks)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.music_player_selection = (self.music_player_selection + 1) % len(self.music_player_tracks)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Play/Pause or select track
                    self.toggle_music_player_track()
                elif event.key == pygame.K_LEFT:
                    # Previous track
                    self.music_player_previous_track()
                elif event.key == pygame.K_RIGHT:
                    # Next track
                    self.music_player_next_track()
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
                    # Stop music player and resume theme
                    self.music_player_stop()
                    self.music_manager.play_theme()
            elif self.state == GameState.LEVEL_EDITOR_MENU:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
            elif self.state == GameState.HIGH_SCORE_ENTRY:
                self.handle_high_score_keyboard(event)
            elif self.state == GameState.HIGH_SCORES:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.MENU
                    # Ensure theme music is playing when returning to menu
                    if not self.music_manager.theme_mode:
                        self.music_manager.play_theme()
            elif self.state == GameState.MULTIPLAYER_MENU:
                if event.key == pygame.K_UP:
                    self.multiplayer_menu_selection = (self.multiplayer_menu_selection - 1) % len(self.multiplayer_menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.multiplayer_menu_selection = (self.multiplayer_menu_selection + 1) % len(self.multiplayer_menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    if self.multiplayer_menu_selection == 0:
                        # Same Screen - Go directly to lobby (level selection is in lobby now)
                        self.sound_manager.play('blip_select')
                        self.is_multiplayer = True
                        self.is_network_game = False
                        self.lobby_settings['level'] = 0  # Default to first level
                        self.load_selected_multiplayer_level()
                        self.setup_multiplayer_game()
                        self.state = GameState.MULTIPLAYER_LOBBY
                    elif self.multiplayer_menu_selection == 1:
                        # Network Game - Go to network menu
                        self.sound_manager.play('blip_select')
                        self.state = GameState.NETWORK_MENU
                    elif self.multiplayer_menu_selection == 2:
                        # Back to main menu
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MENU
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.NETWORK_MENU:
                if event.key == pygame.K_UP:
                    self.network_menu_selection = (self.network_menu_selection - 1) % len(self.network_menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.network_menu_selection = (self.network_menu_selection + 1) % len(self.network_menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    if self.network_menu_selection == 0:
                        # Host Game
                        self.sound_manager.play('blip_select')
                        success, result = self.network_manager.start_host(max_players=4)
                        if success:
                            self.network_host_ip = result
                            self.network_status_message = f"Hosting on {result}"
                            self.is_multiplayer = True
                            self.is_network_game = True
                            # Initialize default lobby settings
                            self.player_slots = ['player', 'cpu', 'cpu', 'cpu']  # Host is player 1, rest are CPU
                            self.lobby_selection = 0
                            # Go to multiplayer lobby (setup screen)
                            self.state = GameState.MULTIPLAYER_LOBBY
                        else:
                            self.network_status_message = f"Failed to host: {result}"
                    elif self.network_menu_selection == 1:
                        # Join Game - start server discovery and go to server list
                        self.sound_manager.play('blip_select')
                        self.network_manager.start_discovery()
                        self.discovered_servers = []
                        self.server_selection = 0
                        self.state = GameState.NETWORK_CLIENT_LOBBY
                        self.network_status_message = "Searching for LAN servers..."
                    elif self.network_menu_selection == 2:
                        # Back
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MULTIPLAYER_MENU
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MULTIPLAYER_MENU
            elif self.state == GameState.NETWORK_HOST_LOBBY:
                # Host lobby - waiting for players to join
                if event.key == pygame.K_RETURN:
                    # Start game if we have at least 2 players (host + 1 client)
                    if self.network_manager.get_connected_players() >= 2:
                        self.sound_manager.play('start_game')
                        # Start game on host first (this selects music)
                        self.music_manager.stop_game_over_music()
                        self.reset_game()
                        # Broadcast game start to all clients WITH current music track
                        num_players = self.network_manager.get_connected_players()
                        music_track_index = self.music_manager.get_track_index()
                        print(f"[HOST] Broadcasting game start with music_track_index: {music_track_index}")  # DEBUG
                        start_msg = create_game_start_message(num_players, music_track_index, self.current_level_data)
                        self.network_manager.broadcast_to_clients(start_msg)
                    else:
                        self.network_status_message = "Need at least 2 players"
                elif event.key == pygame.K_ESCAPE:
                    # Cancel hosting
                    self.sound_manager.play('blip_select')
                    self.network_manager.cleanup()
                    self.is_multiplayer = False
                    self.is_network_game = False
                    self.state = GameState.NETWORK_MENU
            elif self.state == GameState.NETWORK_CLIENT_LOBBY:
                # Client - server list navigation and connection
                if event.key == pygame.K_UP:
                    # Navigate up in server list
                    if len(self.discovered_servers) > 0 and self.server_selection > 0:
                        self.server_selection -= 1
                        self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    # Navigate down in server list
                    if len(self.discovered_servers) > 0 and self.server_selection < len(self.discovered_servers) - 1:
                        self.server_selection += 1
                        self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    # Connect to selected server
                    if len(self.discovered_servers) > 0 and self.server_selection < len(self.discovered_servers):
                        self.sound_manager.play('blip_select')
                        name, ip, port = self.discovered_servers[self.server_selection]
                        self.network_status_message = f"Connecting to {name}..."
                        self.network_manager.stop_discovery()
                        success, result = self.network_manager.connect_to_host(ip)
                        if success:
                            self.network_status_message = "Connected! Waiting for host..."
                            self.is_multiplayer = True
                            self.is_network_game = True
                        else:
                            self.network_status_message = f"Failed: {result}"
                            self.network_manager.cleanup()
                            # Restart discovery
                            self.network_manager.start_discovery()
                    else:
                        self.network_status_message = "No server selected"
                elif event.key == pygame.K_r:
                    # Refresh server list
                    self.sound_manager.play('blip_select')
                    self.network_manager.stop_discovery()
                    self.network_manager.start_discovery()
                    self.discovered_servers = []
                    self.server_selection = 0
                    self.network_status_message = "Refreshing server list..."
                elif event.key == pygame.K_ESCAPE:
                    # Cancel and go back
                    self.sound_manager.play('blip_select')
                    self.network_manager.cleanup()
                    self.state = GameState.NETWORK_MENU
            elif self.state == GameState.MULTIPLAYER_LEVEL_SELECT:
                if event.key == pygame.K_UP:
                    if len(self.multiplayer_levels) > 0:
                        self.multiplayer_level_selection = (self.multiplayer_level_selection - 1) % len(self.multiplayer_levels)
                        self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    if len(self.multiplayer_levels) > 0:
                        self.multiplayer_level_selection = (self.multiplayer_level_selection + 1) % len(self.multiplayer_levels)
                        self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    # Select level and return to lobby
                    if len(self.multiplayer_levels) > 0:
                        self.sound_manager.play('blip_select')
                        # Update lobby level setting
                        self.lobby_settings['level'] = self.multiplayer_level_selection
                        self.load_selected_multiplayer_level()
                        # Return to lobby (or multiplayer menu if no return state)
                        if self.level_select_return_state:
                            self.state = self.level_select_return_state
                            self.level_select_return_state = None
                            # Broadcast updated lobby state to clients
                            if self.is_network_game and self.network_manager.is_host():
                                self.broadcast_lobby_state()
                        else:
                            self.state = GameState.MULTIPLAYER_LOBBY
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    # Return to lobby if coming from there, otherwise multiplayer menu
                    if self.level_select_return_state:
                        self.state = self.level_select_return_state
                        self.level_select_return_state = None
                    else:
                        self.state = GameState.MULTIPLAYER_MENU
            elif self.state == GameState.MULTIPLAYER_LOBBY:
                # Only host can navigate and change settings in network games
                can_change = not self.is_network_game or self.network_manager.is_host()
                
                if event.key == pygame.K_UP and can_change:
                    self.lobby_selection = (self.lobby_selection - 1) % 8  # 4 settings + 4 players
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN and can_change:
                    self.lobby_selection = (self.lobby_selection + 1) % 8
                    self.sound_manager.play('blip_select')
                elif (event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT) and can_change:
                    direction = 1 if event.key == pygame.K_RIGHT else -1
                    self.change_lobby_setting(self.lobby_selection, direction)
                elif event.key == pygame.K_a and can_change:
                    # A key opens level select when on level option
                    if self.lobby_selection == 3:
                        self.sound_manager.play('blip_select')
                        self.level_select_return_state = GameState.MULTIPLAYER_LOBBY
                        self.multiplayer_level_selection = self.lobby_settings.get('level', 0)
                        self.state = GameState.MULTIPLAYER_LEVEL_SELECT
                elif event.key == pygame.K_RETURN:
                    # Only host can start game in network mode
                    if not self.is_network_game or self.network_manager.is_host():
                        self.sound_manager.play('start_game')
                        # Start game first (this selects music)
                        self.music_manager.stop_game_over_music()
                        self.reset_game()
                        # Broadcast game start to network clients WITH music track
                        if self.is_network_game:
                            num_players = len([s for s in self.player_slots if s != 'off'])
                            music_track_index = self.music_manager.get_track_index()
                            start_msg = create_game_start_message(num_players, music_track_index, self.current_level_data)
                            self.network_manager.broadcast_to_clients(start_msg)
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    # Network clients disconnect, host cancels
                    if self.is_network_game:
                        self.network_manager.cleanup()
                        self.is_network_game = False
                        self.is_multiplayer = False
                        self.state = GameState.NETWORK_MENU if self.network_manager.role == NetworkRole.CLIENT else GameState.NETWORK_MENU
                    else:
                        self.state = GameState.MULTIPLAYER_MENU
            elif self.state == GameState.DIFFICULTY_SELECT:
                if event.key == pygame.K_UP:
                    self.difficulty_selection = (self.difficulty_selection - 1) % 3
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.difficulty_selection = (self.difficulty_selection + 1) % 3
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    # Set difficulty and start game
                    if self.difficulty_selection == 0:
                        self.difficulty = Difficulty.EASY
                    elif self.difficulty_selection == 1:
                        self.difficulty = Difficulty.MEDIUM
                    else:
                        self.difficulty = Difficulty.HARD
                    self.sound_manager.play('start_game')
                    self.music_manager.stop_game_over_music()
                    self.reset_game()
                    # reset_game() already sets state to EGG_HATCHING, don't override it
        
        if event.type == pygame.JOYBUTTONDOWN and self.joystick:
            button = event.button
            # Skip intro with any button press
            if self.state == GameState.INTRO:
                self.intro_seen = True
                self.save_unlocked_levels()
                self.state = GameState.ADVENTURE_LEVEL_SELECT
                self.adventure_level_selection = 0
            elif self.state == GameState.MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    self.select_menu_option()
            elif self.state == GameState.SINGLE_PLAYER_MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    self.select_single_player_option()
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.EXTRAS_MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    self.select_extras_option()
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.ADVENTURE_LEVEL_SELECT:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    level_num = self.adventure_level_selection + 1
                    # Only allow playing unlocked levels
                    if self.is_level_unlocked(level_num):
                        if self.load_level(level_num):
                            self.sound_manager.play('start_game')
                            self.lives = 3  # Reset lives when starting a level
                            self.state = GameState.EGG_HATCHING
                            self.score = 0
                            self.level = level_num
                    else:
                        # Play error sound or do nothing if level is locked
                        self.sound_manager.play('blip_select')
                elif button == GamepadButton.BTN_Y:
                    # View intro if available
                    if len(self.intro_images) > 0:
                        self.sound_manager.play('blip_select')
                        self.start_intro()
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.SINGLE_PLAYER_MENU
            elif self.state == GameState.PLAYING:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.PAUSED
                elif button == GamepadButton.BTN_A:
                    # Shooting in adventure mode
                    if self.game_mode == "adventure" and self.snake.can_shoot:
                        # Check if player has enough segments (need more than 3)
                        if len(self.snake.body) > 3:
                            # Fire a bullet in the current direction
                            head_x, head_y = self.snake.body[0]
                            bullet = Bullet(head_x, head_y, self.snake.direction)
                            self.bullets.append(bullet)
                            # Remove a segment from the snake
                            if self.snake.body:
                                self.snake.body.pop()
                            # Play laser shoot sound
                            self.sound_manager.play('laser_shoot')
                            # If segments are now 3 or less, lose shooting ability
                            if len(self.snake.body) <= 3:
                                self.snake.can_shoot = False
            elif self.state == GameState.PAUSED:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.PLAYING
                elif button == GamepadButton.BTN_B:
                    # Exit game - for network games, use special handling
                    if self.is_network_game:
                        self.exit_network_game()
                    elif self.is_multiplayer:
                        # Local multiplayer - return to multiplayer menu
                        self.state = GameState.MULTIPLAYER_MENU
                    else:
                        # Single player - return to appropriate menu
                        self.music_manager.play_theme()
                        if self.game_mode == "adventure":
                            self.state = GameState.ADVENTURE_LEVEL_SELECT
                        else:
                            self.state = GameState.MENU
            elif self.state == GameState.GAME_OVER:
                # Only allow input after the 3-second timer expires
                if self.game_over_timer == 0 and button == GamepadButton.BTN_START:
                    if self.is_network_game:
                        # Network game - only host can progress
                        if self.network_manager.is_host():
                            self.sound_manager.play('blip_select')
                            return_msg = create_return_to_lobby_message()
                            self.network_manager.broadcast_to_clients(return_msg)
                            self.state = GameState.MULTIPLAYER_LOBBY
                            self.multiplayer_end_timer_phase = 0
                            self.broadcast_lobby_state()
                        # Client ignores input - waits for host
                    elif self.is_multiplayer:
                        # Local multiplayer - go back to lobby
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MULTIPLAYER_LOBBY
                    elif self.game_mode == "adventure":
                        # Adventure mode - reset lives and go back to level select
                        self.sound_manager.play('blip_select')
                        self.lives = 3
                        self.state = GameState.ADVENTURE_LEVEL_SELECT
                    else:
                        # Endless mode - reset game and go to menu
                        self.reset_game()
                        self.state = GameState.MENU
            elif self.state == GameState.LEVEL_COMPLETE:
                if button == GamepadButton.BTN_START:
                    # Adventure mode returns to level select, endless continues to next level
                    if self.game_mode == "adventure":
                        self.lives = 3  # Reset lives after completing a level
                        self.state = GameState.ADVENTURE_LEVEL_SELECT
                        # Stop victory jingle and start theme music
                        pygame.mixer.music.stop()
                        self.music_manager.play_theme()
                    else:
                        self.next_level()
            elif self.state == GameState.CREDITS:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_B:
                    # Return to extras menu
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
                    # Play theme music
                    if not self.music_manager.theme_mode:
                        self.music_manager.play_theme()
            elif self.state == GameState.ACHIEVEMENTS:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
            elif self.state == GameState.MUSIC_PLAYER:
                if button == GamepadButton.BTN_A:
                    # Play/Pause or select track
                    self.toggle_music_player_track()
                elif button == GamepadButton.BTN_L:
                    # Previous track
                    self.music_player_previous_track()
                elif button == GamepadButton.BTN_R:
                    # Next track
                    self.music_player_next_track()
                elif button == GamepadButton.BTN_START or button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
                    # Stop music player and resume theme
                    self.music_player_stop()
                    self.music_manager.play_theme()
            elif self.state == GameState.LEVEL_EDITOR_MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.EXTRAS_MENU
            elif self.state == GameState.HIGH_SCORE_ENTRY:
                if button == GamepadButton.BTN_A:
                    self.use_onscreen_keyboard()
                elif button == GamepadButton.BTN_B:
                    if self.name_index > 0:
                        self.name_index -= 1
                elif button == GamepadButton.BTN_START:
                    name = ''.join(self.player_name)
                    self.add_high_score(name, self.score)
                    self.state = GameState.HIGH_SCORES
            elif self.state == GameState.HIGH_SCORES:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.MENU
            elif self.state == GameState.MULTIPLAYER_MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    if self.multiplayer_menu_selection == 0:
                        # Same Screen - Go directly to lobby (level selection is in lobby now)
                        self.sound_manager.play('blip_select')
                        self.is_multiplayer = True
                        self.is_network_game = False
                        self.lobby_settings['level'] = 0  # Default to first level
                        self.load_selected_multiplayer_level()
                        self.setup_multiplayer_game()
                        self.state = GameState.MULTIPLAYER_LOBBY
                    elif self.multiplayer_menu_selection == 1:
                        # Network Game - Go to network menu
                        self.sound_manager.play('blip_select')
                        self.state = GameState.NETWORK_MENU
                    elif self.multiplayer_menu_selection == 2:
                        # Back to main menu
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MENU
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.NETWORK_MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    if self.network_menu_selection == 0:
                        # Host Game
                        self.sound_manager.play('blip_select')
                        success, result = self.network_manager.start_host(max_players=4)
                        if success:
                            self.network_host_ip = result
                            self.network_status_message = f"Hosting on {result}"
                            self.is_multiplayer = True
                            self.is_network_game = True
                            # Initialize default lobby settings
                            self.player_slots = ['player', 'cpu', 'cpu', 'cpu']  # Host is player 1, rest are CPU
                            self.lobby_selection = 0
                            # Go to multiplayer lobby (setup screen)
                            self.state = GameState.MULTIPLAYER_LOBBY
                        else:
                            self.network_status_message = f"Failed to host: {result}"
                    elif self.network_menu_selection == 1:
                        # Join Game - start server discovery and go to server list
                        self.sound_manager.play('blip_select')
                        self.network_manager.start_discovery()
                        self.discovered_servers = []
                        self.server_selection = 0
                        self.state = GameState.NETWORK_CLIENT_LOBBY
                        self.network_status_message = "Searching for LAN servers..."
                    elif self.network_menu_selection == 2:
                        # Back
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MULTIPLAYER_MENU
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MULTIPLAYER_MENU
            elif self.state == GameState.NETWORK_CLIENT_LOBBY:
                # Server list navigation with gamepad
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    # Connect to selected server
                    if len(self.discovered_servers) > 0 and self.server_selection < len(self.discovered_servers):
                        self.sound_manager.play('blip_select')
                        name, ip, port = self.discovered_servers[self.server_selection]
                        self.network_status_message = f"Connecting to {name}..."
                        self.network_manager.stop_discovery()
                        success, result = self.network_manager.connect_to_host(ip)
                        if success:
                            self.network_status_message = "Connected! Waiting for host..."
                            self.is_multiplayer = True
                            self.is_network_game = True
                        else:
                            self.network_status_message = f"Failed: {result}"
                            self.network_manager.cleanup()
                            self.network_manager.start_discovery()
                    else:
                        self.network_status_message = "No server selected"
                elif button == GamepadButton.BTN_B:
                    # Cancel and go back
                    self.sound_manager.play('blip_select')
                    self.network_manager.cleanup()
                    self.state = GameState.NETWORK_MENU
                elif button == GamepadButton.BTN_Y:
                    # Refresh server list
                    self.sound_manager.play('blip_select')
                    self.network_manager.stop_discovery()
                    self.network_manager.start_discovery()
                    self.discovered_servers = []
                    self.server_selection = 0
                    self.network_status_message = "Refreshing server list..."
            elif self.state == GameState.MULTIPLAYER_LOBBY:
                # Only host can change settings in network games
                can_change = not self.is_network_game or self.network_manager.is_host()
                
                if button == GamepadButton.BTN_START:
                    # Only host can start game in network mode
                    if not self.is_network_game or self.network_manager.is_host():
                        self.sound_manager.play('start_game')
                        # Start game first (this selects music)
                        self.music_manager.stop_game_over_music()
                        self.reset_game()
                        # Broadcast game start to network clients WITH music track
                        if self.is_network_game:
                            num_players = len([s for s in self.player_slots if s != 'off'])
                            music_track_index = self.music_manager.get_track_index()
                            start_msg = create_game_start_message(num_players, music_track_index, self.current_level_data)
                            self.network_manager.broadcast_to_clients(start_msg)
                elif button == GamepadButton.BTN_A and can_change:
                    # A button opens level select when on level option, otherwise cycles settings forward
                    if self.lobby_selection == 3:
                        self.sound_manager.play('blip_select')
                        self.level_select_return_state = GameState.MULTIPLAYER_LOBBY
                        self.multiplayer_level_selection = self.lobby_settings.get('level', 0)
                        self.state = GameState.MULTIPLAYER_LEVEL_SELECT
                    else:
                        self.change_lobby_setting(self.lobby_selection, 1)
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    # Network clients disconnect, host cancels
                    if self.is_network_game:
                        self.network_manager.cleanup()
                        self.is_network_game = False
                        self.is_multiplayer = False
                        self.state = GameState.NETWORK_MENU if self.network_manager.role == NetworkRole.CLIENT else GameState.NETWORK_MENU
                    else:
                        self.state = GameState.MULTIPLAYER_MENU
            elif self.state == GameState.DIFFICULTY_SELECT:
                if button == GamepadButton.BTN_START:
                    # Set difficulty and start game
                    if self.difficulty_selection == 0:
                        self.difficulty = Difficulty.EASY
                    elif self.difficulty_selection == 1:
                        self.difficulty = Difficulty.MEDIUM
                    else:
                        self.difficulty = Difficulty.HARD
                    self.sound_manager.play('start_game')
                    self.music_manager.stop_game_over_music()
                    self.reset_game()
                    # reset_game() already sets state to EGG_HATCHING, don't override it
        
        if event.type == pygame.JOYHATMOTION and self.joystick:
            hat = event.value
            if self.state == GameState.MENU:
                if hat[1] == 1:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
            elif self.state == GameState.MULTIPLAYER_MENU:
                if hat[1] == 1:
                    self.multiplayer_menu_selection = (self.multiplayer_menu_selection - 1) % len(self.multiplayer_menu_options)
                    self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    self.multiplayer_menu_selection = (self.multiplayer_menu_selection + 1) % len(self.multiplayer_menu_options)
                    self.sound_manager.play('blip_select')
            elif self.state == GameState.NETWORK_MENU:
                if hat[1] == 1:
                    self.network_menu_selection = (self.network_menu_selection - 1) % len(self.network_menu_options)
                    self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    self.network_menu_selection = (self.network_menu_selection + 1) % len(self.network_menu_options)
                    self.sound_manager.play('blip_select')
            elif self.state == GameState.MULTIPLAYER_LOBBY:
                # Only host can navigate and change settings in network games
                can_change = not self.is_network_game or self.network_manager.is_host()
                if can_change:
                    if hat[1] == 1:
                        self.lobby_selection = (self.lobby_selection - 1) % 8  # 4 settings + 4 players
                        self.sound_manager.play('blip_select')
                    elif hat[1] == -1:
                        self.lobby_selection = (self.lobby_selection + 1) % 8
                        self.sound_manager.play('blip_select')
                    elif hat[0] == -1 or hat[0] == 1:
                        # Left/right to change settings
                        direction = 1 if hat[0] == 1 else -1
                        self.change_lobby_setting(self.lobby_selection, direction)
            elif self.state == GameState.NETWORK_CLIENT_LOBBY:
                # D-pad navigation for server list
                if hat[1] == 1:
                    # Up - navigate up in server list
                    if len(self.discovered_servers) > 0 and self.server_selection > 0:
                        self.server_selection -= 1
                        self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    # Down - navigate down in server list
                    if len(self.discovered_servers) > 0 and self.server_selection < len(self.discovered_servers) - 1:
                        self.server_selection += 1
                        self.sound_manager.play('blip_select')
            elif self.state == GameState.DIFFICULTY_SELECT:
                if hat[1] == 1:
                    self.difficulty_selection = (self.difficulty_selection - 1) % 3
                    self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    self.difficulty_selection = (self.difficulty_selection + 1) % 3
                    self.sound_manager.play('blip_select')
            elif self.state == GameState.HIGH_SCORE_ENTRY:
                if hat[0] == -1:
                    self.keyboard_selection[1] = max(0, self.keyboard_selection[1] - 1)
                    self.sound_manager.play('blip_select')
                elif hat[0] == 1:
                    self.keyboard_selection[1] = min(9, self.keyboard_selection[1] + 1)
                    self.sound_manager.play('blip_select')
                elif hat[1] == 1:
                    self.keyboard_selection[0] = max(0, self.keyboard_selection[0] - 1)
                    self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    self.keyboard_selection[0] = min(3, self.keyboard_selection[0] + 1)
                    self.sound_manager.play('blip_select')
        
        # CRITICAL: Consume ALL gamepad events to prevent passthrough to EmulationStation
        # This includes axis motion, button presses, hat motion, etc.
        if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, 
                          pygame.JOYAXISMOTION, pygame.JOYHATMOTION,
                          pygame.JOYBALLMOTION, pygame.JOYDEVICEADDED, 
                          pygame.JOYDEVICEREMOVED):
            return True  # Event consumed - won't pass through to underlying system
        
        return True
    
    def handle_high_score_keyboard(self, event):
        if event.key == pygame.K_BACKSPACE:
            if self.name_index > 0:
                self.name_index -= 1
                self.player_name[self.name_index] = 'A'
                self.sound_manager.play('blip_select')
        elif event.key == pygame.K_LEFT:
            if self.name_index > 0:
                self.name_index -= 1
                self.sound_manager.play('blip_select')
        elif event.key == pygame.K_RIGHT:
            if self.name_index < 2:
                self.name_index += 1
                self.sound_manager.play('blip_select')
        elif event.key == pygame.K_UP:
            # Optional: Navigate onscreen keyboard
            self.keyboard_selection[0] = max(0, self.keyboard_selection[0] - 1)
            self.sound_manager.play('blip_select')
        elif event.key == pygame.K_DOWN:
            # Optional: Navigate onscreen keyboard
            self.keyboard_selection[0] = min(3, self.keyboard_selection[0] + 1)
            self.sound_manager.play('blip_select')
        elif event.key == pygame.K_RETURN:
            self.sound_manager.play('select_letter')
            name = ''.join(self.player_name)
            self.add_high_score(name, self.score)
            self.state = GameState.HIGH_SCORES
        elif event.key == pygame.K_SPACE:
            # Use onscreen keyboard selection
            self.use_onscreen_keyboard()
        elif event.unicode.isalnum() and len(event.unicode) == 1:
            # Direct keyboard input - just type the letters!
            self.sound_manager.play('select_letter')
            self.player_name[self.name_index] = event.unicode.upper()
            if self.name_index < 2:
                self.name_index += 1
    
    def use_onscreen_keyboard(self):
        row, col = self.keyboard_selection
        char = self.keyboard_layout[row][col]
        if char == '<':
            if self.name_index > 0:
                self.name_index -= 1
                self.sound_manager.play('blip_select')
        elif char == '>':
            if self.name_index < 2:
                self.name_index += 1
                self.sound_manager.play('blip_select')
        elif char != ' ':
            self.sound_manager.play('select_letter')
            self.player_name[self.name_index] = char
            if self.name_index < 2:
                self.name_index += 1
    
    def select_menu_option(self):
        if self.menu_selection == 0:
            # Single Player - Go to single player submenu
            self.sound_manager.play('blip_select')
            self.state = GameState.SINGLE_PLAYER_MENU
            self.single_player_selection = 0
        elif self.menu_selection == 1:
            # Multiplayer - Go to multiplayer menu
            self.sound_manager.play('blip_select')
            self.state = GameState.MULTIPLAYER_MENU
            self.multiplayer_menu_selection = 0
        elif self.menu_selection == 2:
            # Extras - Go to extras menu
            self.sound_manager.play('blip_select')
            self.state = GameState.EXTRAS_MENU
            self.extras_menu_selection = 0
        elif self.menu_selection == 3:
            # Quit
            pygame.event.set_grab(False)  # Release input grab before quitting
            pygame.quit()
            exit()
    
    def select_single_player_option(self):
        """Handle single player submenu selection"""
        if self.single_player_selection == 0:
            # Adventure Mode - Check if intro has been seen
            self.sound_manager.play('blip_select')
            self.game_mode = "adventure"
            self.is_multiplayer = False
            
            # If intro hasn't been seen, show intro first
            if not self.intro_seen:
                self.start_intro()
            else:
                self.state = GameState.ADVENTURE_LEVEL_SELECT
                self.adventure_level_selection = 0
        elif self.single_player_selection == 1:
            # Endless Mode - Go to difficulty selection
            self.sound_manager.play('blip_select')
            self.game_mode = "endless"
            self.is_multiplayer = False
            self.state = GameState.DIFFICULTY_SELECT
        elif self.single_player_selection == 2:
            # Back to main menu
            self.sound_manager.play('blip_select')
            self.state = GameState.MENU
    
    def select_extras_option(self):
        """Handle extras submenu selection"""
        if self.extras_menu_selection == 0:
            # Achievements
            self.sound_manager.play('blip_select')
            self.state = GameState.ACHIEVEMENTS
        elif self.extras_menu_selection == 1:
            # Music Player
            self.sound_manager.play('blip_select')
            self.state = GameState.MUSIC_PLAYER
            # Stop theme music when entering music player
            self.music_manager.stop_theme()
        elif self.extras_menu_selection == 2:
            # Level Editor
            self.sound_manager.play('blip_select')
            self.state = GameState.LEVEL_EDITOR_MENU
        elif self.extras_menu_selection == 3:
            # Credits
            self.sound_manager.play('blip_select')
            self.state = GameState.CREDITS
        elif self.extras_menu_selection == 4:
            # Back to main menu
            self.sound_manager.play('blip_select')
            self.state = GameState.MENU
    
    def toggle_music_player_track(self):
        """Play or pause the selected track in the music player, or purchase if locked."""
        if len(self.music_player_tracks) == 0:
            return
        
        selected_track = self.music_player_tracks[self.music_player_selection]
        track_name, track_path, filename = selected_track
        
        # Check if track is locked
        if not self.is_music_unlocked(filename):
            # Try to purchase
            if self.unlock_music(filename):
                self.sound_manager.play('pickupCoin')
                # Now play the newly unlocked track
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
                self.music_player_current_track = self.music_player_selection
                self.music_player_playing = True
            else:
                # Not enough coins
                self.sound_manager.play('blip_select')
            return
        
        # If currently playing
        if self.music_player_playing:
            # If clicking the same track, pause it
            if self.music_player_current_track == self.music_player_selection:
                pygame.mixer.music.pause()
                self.music_player_playing = False
                self.sound_manager.play('blip_select')
            else:
                # Different track selected, play it
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()  # Play once (will auto-advance)
                self.music_player_current_track = self.music_player_selection
                self.music_player_playing = True
                self.sound_manager.play('blip_select')
        else:
            # Not playing - check if we're resuming or starting new
            if self.music_player_current_track == self.music_player_selection:
                # Resume the paused track
                pygame.mixer.music.unpause()
                self.music_player_playing = True
                self.sound_manager.play('blip_select')
            else:
                # Start playing the selected track
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()  # Play once (will auto-advance)
                self.music_player_current_track = self.music_player_selection
                self.music_player_playing = True
                self.sound_manager.play('blip_select')
    
    def music_player_previous_track(self):
        """Skip to the previous track."""
        if len(self.music_player_tracks) == 0:
            return
        
        self.music_player_selection = (self.music_player_selection - 1) % len(self.music_player_tracks)
        self.sound_manager.play('blip_select')
        
        # If music is playing, auto-play the new track (only if unlocked)
        if self.music_player_playing:
            track_name, track_path, filename = self.music_player_tracks[self.music_player_selection]
            if self.is_music_unlocked(filename):
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()  # Play once (will auto-advance)
                self.music_player_current_track = self.music_player_selection
            else:
                # Track is locked, stop playing
                self.music_player_playing = False
                pygame.mixer.music.stop()
    
    def music_player_next_track(self):
        """Skip to the next track, finding the next unlocked track if auto-advancing."""
        if len(self.music_player_tracks) == 0:
            return
        
        # If music is playing (auto-advance), find next unlocked track
        if self.music_player_playing:
            start_idx = self.music_player_selection
            attempts = 0
            while attempts < len(self.music_player_tracks):
                self.music_player_selection = (self.music_player_selection + 1) % len(self.music_player_tracks)
                track_name, track_path, filename = self.music_player_tracks[self.music_player_selection]
                
                if self.is_music_unlocked(filename):
                    # Found an unlocked track, play it
                    pygame.mixer.music.load(track_path)
                    pygame.mixer.music.play()  # Play once (will auto-advance)
                    self.music_player_current_track = self.music_player_selection
                    self.sound_manager.play('blip_select')
                    return
                
                attempts += 1
            
            # No unlocked tracks found, stop playing
            self.music_player_playing = False
            pygame.mixer.music.stop()
        else:
            # Manual skip, just move selection
            self.music_player_selection = (self.music_player_selection + 1) % len(self.music_player_tracks)
            self.sound_manager.play('blip_select')
    
    def music_player_stop(self):
        """Stop the music player."""
        if self.music_player_playing:
            pygame.mixer.music.stop()
            self.music_player_playing = False
            self.music_player_current_track = None
    
    def load_level(self, level_number):
        """Load a level from JSON file"""
        try:
            level_file = os.path.join(SCRIPT_DIR, 'levels', 'level_{:02d}.json'.format(level_number))
            with open(level_file, 'r') as f:
                self.current_level_data = json.load(f)
            
            # Store current level number for score tracking
            self.current_adventure_level = level_number
            
            # Parse level data
            self.level_walls = [(w['x'], w['y']) for w in self.current_level_data['walls']]
            self.worms_required = self.current_level_data['worms_required']
            self.worms_collected = 0
            self.bonus_fruits_collected = 0
            self.total_bonus_fruits = len(self.current_level_data.get('bonus_fruit_positions', []))
            
            # Load level-specific background image if specified
            if 'background_image' in self.current_level_data and self.current_level_data['background_image']:
                try:
                    bg_filename = self.current_level_data['background_image']
                    bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', bg_filename)
                    self.background = pygame.image.load(bg_path).convert()
                    self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    print("Loaded level background: {}".format(bg_filename))
                except Exception as e:
                    print("Warning: Could not load level background '{}': {}".format(self.current_level_data['background_image'], e))
            
            # Set up starting position
            start_pos = self.current_level_data['starting_position']
            start_dir_str = self.current_level_data['starting_direction']
            
            # Convert direction string to Direction enum
            direction_map = {
                'UP': Direction.UP,
                'DOWN': Direction.DOWN,
                'LEFT': Direction.LEFT,
                'RIGHT': Direction.RIGHT
            }
            start_dir = direction_map.get(start_dir_str, Direction.RIGHT)
            
            # Reset snake to starting position
            self.snake = Snake(player_id=0)
            self.snakes = [self.snake]
            self.snake.body = [start_pos]
            self.snake.direction = start_dir
            self.snake.next_direction = start_dir
            
            # Spawn worms at specified positions
            self.food_items = []
            for worm_data in self.current_level_data['worm_positions']:
                self.food_items.append(((worm_data['x'], worm_data['y']), 'worm'))
            
            # Spawn bonus fruits at specified positions (if any)
            if 'bonus_fruit_positions' in self.current_level_data:
                for bonus_data in self.current_level_data['bonus_fruit_positions']:
                    self.food_items.append(((bonus_data['x'], bonus_data['y']), 'bonus'))
            
            # Spawn coins at specified positions (if any)
            if 'coin_positions' in self.current_level_data:
                for coin_data in self.current_level_data['coin_positions']:
                    self.food_items.append(((coin_data['x'], coin_data['y']), 'coin'))
            
            # Spawn diamonds at specified positions (if any)
            if 'diamond_positions' in self.current_level_data:
                for diamond_data in self.current_level_data['diamond_positions']:
                    self.food_items.append(((diamond_data['x'], diamond_data['y']), 'diamond'))
            
            # Spawn isotopes at specified positions (if any)
            if 'isotope_positions' in self.current_level_data:
                for isotope_data in self.current_level_data['isotope_positions']:
                    self.food_items.append(((isotope_data['x'], isotope_data['y']), 'isotope'))
            
            # Load enemies (if any)
            self.enemies = []
            self.enemy_snakes = []  # Clear enemy snakes list
            if 'enemies' in self.current_level_data:
                for enemy_data in self.current_level_data['enemies']:
                    enemy_type = enemy_data['type']
                    
                    # Handle snake enemies differently - create Snake objects
                    if enemy_type == 'enemy_snake':
                        snake_enemy = Snake(player_id=200 + len(self.enemy_snakes))  # Use high IDs (200+)
                        snake_enemy.is_cpu = True
                        snake_enemy.cpu_difficulty = 2  # Hard difficulty like boss minions
                        snake_enemy.is_enemy_snake = True  # Mark as enemy snake
                        snake_enemy.can_eat = False  # Cannot eat food
                        # Set starting position and direction
                        spawn_pos = (enemy_data['x'], enemy_data['y'])
                        spawn_dir = Direction.LEFT  # Default direction
                        snake_enemy.reset(spawn_pos=spawn_pos, direction=spawn_dir)
                        # Set starting length to 6
                        snake_enemy.body = [spawn_pos]
                        for i in range(5):  # Add 5 more segments for total of 6
                            # Add segments behind the head
                            if spawn_dir == Direction.LEFT:
                                new_seg = (spawn_pos[0] + i + 1, spawn_pos[1])
                            elif spawn_dir == Direction.RIGHT:
                                new_seg = (spawn_pos[0] - i - 1, spawn_pos[1])
                            elif spawn_dir == Direction.UP:
                                new_seg = (spawn_pos[0], spawn_pos[1] + i + 1)
                            else:  # DOWN
                                new_seg = (spawn_pos[0], spawn_pos[1] - i - 1)
                            snake_enemy.body.append(new_seg)
                        snake_enemy.alive = True
                        # Initialize movement tracking for smooth interpolation
                        snake_enemy.move_timer = 0
                        snake_enemy.last_move_interval = 16
                        snake_enemy.previous_body = snake_enemy.body.copy()
                        self.enemy_snakes.append(snake_enemy)
                        print("Spawned enemy snake at {} with length {}".format(spawn_pos, len(snake_enemy.body)))
                    else:
                        # Regular enemies (ant, spider, etc.)
                        enemy = Enemy(enemy_data['x'], enemy_data['y'], enemy_type)
                        self.enemies.append(enemy)
            
            # Clear all boss-related entities from previous attempts
            self.boss_minions = []
            self.boss_minion_respawn_timers = {}
            self.spewtums = []
            self.bullets = []
            self.scorpion_stingers = []
            self.beetle_larvae = []
            self.boss_damage_flash = 0
            self.boss_damage_sound_cooldown = 0
            self.boss_death_phase = 0
            self.boss_death_timer = 0
            self.boss_death_particle_timer = 0
            if hasattr(self, 'boss_death_phase1_timer'):
                del self.boss_death_phase1_timer
            
            # Handle boss battle data
            if 'boss_data' in self.current_level_data and self.current_level_data['boss_data']:
                self.boss_data = self.current_level_data['boss_data']
                self.boss_active = True
                self.boss_spawned = False
                self.boss_spawn_timer = 0
                self.boss_attack_timer = 0
                self.boss_is_attacking = False
                self.screen_shake_intensity = 0
                # Reset boss health to full
                self.boss_health = self.boss_max_health
                # Reset attack interval to starting value
                self.boss_attack_interval = self.boss_attack_interval_max
                # Isotope spawning for boss battles
                self.isotope_spawn_timer = 0
                self.isotope_spawn_interval = 300  # Spawn every 5 seconds (60 FPS * 5)
                # Egg respawn flag (False for initial spawn, True for respawns after death)
                self.boss_egg_is_respawn = False
                self.egg_timer = 0
                # Reset boss defeated state
                self.boss_defeated = False
                self.player_frozen = False  # Unfreeze player for replay
                self.boss_death_delay = 0
                self.boss_death_phase = 0
                self.boss_death_timer = 0
                self.boss_death_particle_timer = 0
                self.boss_slide_offset_y = 0
                self.boss_slide_timer = 0
                if hasattr(self, 'boss_death_phase1_timer'):
                    del self.boss_death_phase1_timer
                # Reset super attack tracking
                self.boss_super_attacks_used = set()
                
                # If it's a wormBoss (FINAL BOSS), play epic FinalBoss music
                if self.boss_data == 'wormBoss':
                    try:
                        boss_music_path = os.path.join(SCRIPT_DIR, 'sound', 'music', 'FinalBoss.ogg')
                        pygame.mixer.music.load(boss_music_path)
                        pygame.mixer.music.set_volume(0.9)
                        pygame.mixer.music.play(-1)  # Loop
                        self.music_manager.theme_mode = False
                        print("Playing FinalBoss music for final boss battle")
                    except Exception as e:
                        print("Warning: Could not load FinalBoss.ogg: {}".format(e))
                
                # If it's a Frog Boss, initialize frog-specific state
                if self.boss_data == 'frog':
                    self.boss_max_health = 30  # Frog boss has 30 health
                    self.boss_health = 30
                    self.boss_spawned = True  # Frog spawns immediately
                    self.frog_state = 'waiting'  # Start with 2-second waiting period
                    self.frog_position = [GRID_WIDTH // 2, 2]  # Top of level
                    self.frog_shadow_position = [GRID_WIDTH // 2, 2]  # Top of level
                    self.frog_fall_timer = 0
                    self.frog_initial_spawn_timer = 0  # Timer for 2-second delay
                    self.frog_jump_timer = 0
                    self.frog_airborne_timer = 0
                    self.frog_tongue_segments = []
                    self.frog_tongue_extending = False
                    self.frog_tongue_retracting = False
                    self.frog_tongue_timer = 0
                    self.frog_tongue_direction = (0, -1)
                    self.frog_jump_count = 0
                    self.frog_tracking_player = False
                    self.frog_is_invulnerable = True  # Invulnerable during entrance
                    self.frog_landed_timer = 0  # Timer for delay after landing before tongue attack
                    self.frog_rotation_angle = 0
                    self.frog_target_rotation = 0
                    print("Frog Boss initialized with 30 health")
                    
                    # Play boss music if available
                    try:
                        boss_music_path = os.path.join(SCRIPT_DIR, 'sound', 'music', 'Boss.ogg')
                        pygame.mixer.music.load(boss_music_path)
                        pygame.mixer.music.set_volume(0.9)
                        pygame.mixer.music.play(-1)  # Loop
                        self.music_manager.theme_mode = False
                        print("Playing Boss music for Frog Boss battle")
                    except Exception as e:
                        print("Warning: Could not load Boss.ogg: {}".format(e))
            else:
                self.boss_data = None
                self.boss_active = False
            
            # Always unfreeze player when loading a new level (in case previous level had boss)
            self.player_frozen = False
            
            # Don't set food_pos in Adventure mode - use food_items list instead
            self.food_pos = None
            
            print("Loaded level {}: {}".format(level_number, self.current_level_data['name']))
            return True
            
        except Exception as e:
            print("Error loading level {}: {}".format(level_number, e))
            return False
    def change_lobby_setting(self, selection, direction):
        """Change a lobby setting or player slot."""
        self.sound_manager.play('blip_select')
        
        if selection == 0:
            # Lives
            self.lobby_settings['lives'] = max(1, min(10, self.lobby_settings['lives'] + direction))
        elif selection == 1:
            # Item frequency
            self.lobby_settings['item_frequency'] = (self.lobby_settings['item_frequency'] + direction) % 3
        elif selection == 2:
            # CPU difficulty
            self.lobby_settings['cpu_difficulty'] = (self.lobby_settings['cpu_difficulty'] + direction) % 4
        elif selection == 3:
            # Level selection - cycle through available levels with left/right
            if len(self.multiplayer_levels) > 0:
                self.lobby_settings['level'] = (self.lobby_settings['level'] + direction) % len(self.multiplayer_levels)
                # Load the selected level data
                self.load_selected_multiplayer_level()
        elif selection >= 4 and selection <= 7:
            # Player slots (shifted by 1 to make room for level)
            player_idx = selection - 4
            current = self.player_slots[player_idx]
            
            # Cycle: player -> cpu -> off -> player
            if direction > 0:
                if current == 'player':
                    self.player_slots[player_idx] = 'cpu'
                elif current == 'cpu':
                    self.player_slots[player_idx] = 'off'
                else:
                    self.player_slots[player_idx] = 'player'
            else:
                if current == 'player':
                    self.player_slots[player_idx] = 'off'
                elif current == 'cpu':
                    self.player_slots[player_idx] = 'player'
                else:
                    self.player_slots[player_idx] = 'cpu'
            
            # Auto-set to player if controller detected, CPU if not
            if self.player_slots[player_idx] == 'player':
                if player_idx >= len(self.player_controllers):
                    # No controller - switch to CPU
                    self.player_slots[player_idx] = 'cpu'
        
        # Broadcast lobby state to all clients in network game
        if self.is_network_game and self.network_manager.is_host():
            self.broadcast_lobby_state()
    
    def setup_multiplayer_game(self):
        """Initialize multiplayer game based on lobby settings."""
        # Count active players (not 'off')
        active_slots = [i for i, slot_type in enumerate(self.player_slots) if slot_type != 'off']
        self.num_players = len(active_slots)
        
        if self.num_players < 2:
            self.num_players = 2  # Minimum 2 players
            self.player_slots[0] = 'player'
            self.player_slots[1] = 'player'
            active_slots = [0, 1]
        
        print("Setting up multiplayer game for {} players".format(self.num_players))
        
        # Create snakes for each active player
        self.snakes = []
        spawn_positions = self.get_spawn_positions(self.num_players)
        spawn_directions = self.get_spawn_directions(self.num_players)
        
        for idx, slot_id in enumerate(active_slots):
            snake = Snake(player_id=slot_id)
            snake.speed_modifier = 0
            snake.lives = self.lobby_settings['lives']
            snake.is_cpu = (self.player_slots[slot_id] == 'cpu')
            snake.cpu_difficulty = self.lobby_settings['cpu_difficulty'] if snake.is_cpu else 0
            snake.reset(spawn_pos=spawn_positions[idx], direction=spawn_directions[idx])
            self.snakes.append(snake)
        
        # Initialize food
        self.food_items = []
        self.respawning_players = {}
        
        # Set first snake for backwards compatibility
        self.snake = self.snakes[0]
    
    def get_spawn_positions(self, num_players):
        """Get spawn positions for multiple players in corners."""
        # Players spawn in corners:
        # Player 1: top left
        # Player 2: top right
        # Player 3: bottom right
        # Player 4: bottom left
        positions = [
            (3, 3),  # Top left
            (GRID_WIDTH - 4, 3),  # Top right
            (GRID_WIDTH - 4, GRID_HEIGHT - 4),  # Bottom right
            (3, GRID_HEIGHT - 4)  # Bottom left
        ]
        
        return positions[:num_players]
    
    def get_spawn_directions(self, num_players):
        """Get predetermined spawn directions for each player."""
        # Player 1: face right
        # Player 2: face down
        # Player 3: face left
        # Player 4: face up
        directions = [
            Direction.RIGHT,  # Player 1
            Direction.DOWN,   # Player 2
            Direction.LEFT,   # Player 3
            Direction.UP      # Player 4
        ]
        
        return directions[:num_players]

    def reset_game(self):
        if self.is_multiplayer:
            # Multiplayer reset - start fresh
            self.setup_multiplayer_game()
            
            print("DEBUG: reset_game called for multiplayer")
            print("DEBUG: Has current_level_data?", hasattr(self, 'current_level_data'))
            if hasattr(self, 'current_level_data'):
                print("DEBUG: current_level_data is not None?", self.current_level_data is not None)
            
            # Apply loaded multiplayer level data if available
            if hasattr(self, 'current_level_data') and self.current_level_data:
                # Load walls from level
                self.walls = []
                for wall in self.current_level_data.get('walls', []):
                    self.walls.append((wall['x'], wall['y']))
                
                # Load background
                bg_image = self.current_level_data.get('background_image', 'bg.png')
                try:
                    bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', bg_image)
                    self.background = pygame.image.load(bg_path).convert()
                    print("Loaded background: {}".format(bg_image))
                except Exception as e:
                    print("Warning: Could not load background: {} - {}".format(bg_image, e))
                
                print("Applied multiplayer level: {} walls, background: {}".format(len(self.walls), bg_image))
            else:
                # No level loaded, use default (no walls)
                self.walls = []
            
            # Initialize multiplayer food based on settings
            self.food_items = []
            freq = self.lobby_settings['item_frequency']
            
            if freq == 0:  # Low
                worm_count, apple_count, black_apple_count = 2, 1, 0
            elif freq == 1:  # Normal
                worm_count, apple_count, black_apple_count = 3, 1, 1
            else:  # High
                worm_count, apple_count, black_apple_count = 4, 2, 1
            
            for _ in range(worm_count):
                self.spawn_food_item('worm')
            for _ in range(apple_count):
                self.spawn_food_item('apple')
            for _ in range(black_apple_count):
                self.spawn_food_item('black_apple')
        else:
            # Single player reset
            self.snakes = [Snake(player_id=0)]
            self.snake = self.snakes[0]
            self.score = 0
            self.spawn_food()
            
            # Load appropriate background for game mode
            if self.game_mode == "endless":
                # Endless mode starts at level 1, so load BG1
                try:
                    bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'BG1.png')
                    self.background = pygame.image.load(bg_path).convert()
                    self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    print("Loaded background for endless mode level 1: BG1.png")
                except Exception as e:
                    print("Warning: Could not load BG1.png: {}".format(e))
                    self.background = None
            # Adventure mode backgrounds are loaded when the level is loaded, not here
        
        self.level = 1
        self.lives = 3
        self.fruits_eaten_this_level = 0
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.particles = []
        self.egg_pieces = []
        
        # Clear adventure mode specific flags that could interfere with endless mode
        self.player_frozen = False
        self.respawn_timer = 0
        self.boss_active = False
        self.boss_spawned = False
        self.boss_minions = []
        self.boss_minion_respawn_timers = {}
        self.bullets = []
        self.spewtums = []
        self.enemy_walls = []
        self.level_walls = []
        
        # In multiplayer, skip egg hatching and go straight to playing
        if self.is_multiplayer:
            self.state = GameState.PLAYING
            # Stop theme music and start gameplay music for multiplayer
            if self.music_manager.theme_mode:
                pygame.mixer.music.stop()
                self.music_manager.play_next()
        else:
            # Don't reset snake yet - wait for egg hatching
            self.state = GameState.EGG_HATCHING
    
    def hatch_egg(self, direction):
        """Hatch the egg and spawn the snake in the chosen direction"""
        self.sound_manager.play('crack')
        
        # Reset snake with chosen direction
        # Check if we have a boss egg respawn position (random position after death)
        if (hasattr(self, 'boss_egg_respawn_pos') and self.boss_egg_respawn_pos is not None and 
            hasattr(self, 'boss_egg_is_respawn') and self.boss_egg_is_respawn):
            start_pos = tuple(self.boss_egg_respawn_pos)
            self.snake.reset(spawn_pos=start_pos, direction=direction)
        # In adventure mode, use the level's starting position
        elif self.game_mode == "adventure" and hasattr(self, 'current_level_data'):
            start_pos = tuple(self.current_level_data['starting_position'])
            self.snake.reset(spawn_pos=start_pos, direction=direction)
        else:
            self.snake.reset()
            self.snake.direction = direction
            self.snake.next_direction = direction
        
        # Create flying egg pieces
        # Check if we have a boss egg respawn position (random position after death)
        if (hasattr(self, 'boss_egg_respawn_pos') and self.boss_egg_respawn_pos is not None and 
            hasattr(self, 'boss_egg_is_respawn') and self.boss_egg_is_respawn):
            egg_x, egg_y = self.boss_egg_respawn_pos
            center_x = egg_x * GRID_SIZE + GRID_SIZE // 2
            center_y = egg_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
        # In adventure mode, spawn pieces at the starting position
        elif self.game_mode == "adventure" and hasattr(self, 'current_level_data'):
            egg_x, egg_y = self.current_level_data['starting_position']
            center_x = egg_x * GRID_SIZE + GRID_SIZE // 2
            center_y = egg_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
        else:
            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2
        
        if len(self.egg_piece_imgs) == 4:
            # Create 4 egg pieces flying in different directions
            velocities = [
                (-4, -6),  # Top-left
                (4, -6),   # Top-right
                (-5, -3),  # Left
                (5, -3)    # Right
            ]
            
            for i, (vx, vy) in enumerate(velocities):
                piece = EggPiece(center_x, center_y, self.egg_piece_imgs[i], (vx, vy))
                self.egg_pieces.append(piece)
        
        # Reset boss egg respawn flag, position, and timer
        if hasattr(self, 'boss_egg_is_respawn'):
            self.boss_egg_is_respawn = False
        if hasattr(self, 'boss_egg_respawn_pos'):
            self.boss_egg_respawn_pos = None
        self.egg_timer = 0
        
        # Transition to playing - start gameplay music
        self.state = GameState.PLAYING
        # Switch from theme music to gameplay music
        if self.music_manager.theme_mode:
            pygame.mixer.music.stop()
            self.music_manager.play_next()
    
    def next_level(self):
        self.level += 1
        self.lives = min(5, self.lives + 1)
        self.fruits_eaten_this_level = 0  # Reset fruit counter for new level
        # Don't reset snake - size persists across levels!
        self.spawn_food()
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        
        # In endless mode, cycle through backgrounds BG1-BG12
        if self.game_mode == "endless":
            # Calculate which background to use (cycles through 1-12)
            bg_num = ((self.level - 1) % 12) + 1
            bg_filename = "BG{}.png".format(bg_num)
            
            # Free old background from memory
            if hasattr(self, 'background') and self.background is not None:
                del self.background
                self.background = None
                gc.collect()
            
            # Lazy load new background
            try:
                bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', bg_filename)
                self.background = pygame.image.load(bg_path).convert()
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print("Loaded background for level {}: {}".format(self.level, bg_filename))
            except Exception as e:
                print("Warning: Could not load background '{}': {}".format(bg_filename, e))
                self.background = None
        
        self.state = GameState.PLAYING
        
        # Handle music/sound based on game mode
        if self.game_mode == "endless":
            # In endless mode, just play level up sound effect (don't change music)
            self.sound_manager.play('level_up')
        else:
            # In adventure mode, if theme music was playing, switch to gameplay music
            if self.music_manager.theme_mode:
                pygame.mixer.music.stop()
                self.music_manager.play_next()
    
    def start_intro(self):
        """Initialize intro sequence"""
        # If no intro images exist, skip directly to level select
        if len(self.intro_images) == 0:
            self.intro_seen = True
            self.save_unlocked_levels()
            self.state = GameState.ADVENTURE_LEVEL_SELECT
            self.adventure_level_selection = 0
            return
        
        self.state = GameState.INTRO
        self.intro_current_image = 0
        self.intro_timer = 0
        self.intro_image_duration = 300  # 5 seconds at 60 FPS
        self.intro_fade_duration = 30  # 0.5 seconds fade
        self.intro_fade_alpha = 0
        self.intro_fading = False
        self.intro_final_fade = False
        self.intro_final_fade_timer = 0
        self.intro_final_fade_duration = 120  # 2 seconds fade to black
        
        # Shot 1: Meteorite animation variables
        self.intro_meteorite_active = False
        self.intro_meteorite_x = 0
        self.intro_meteorite_y = 0
        self.intro_meteorite_particles = []
        self.intro_meteorite_crashed = False
        
        # Restart theme music for intro
        self.music_manager.play_theme()
    
    def update_intro(self):
        """Update intro sequence"""
        if self.intro_final_fade:
            # Final fade to black after last image
            self.intro_final_fade_timer += 1
            if self.intro_final_fade_timer >= self.intro_final_fade_duration:
                # Intro complete - mark as seen and go to level select
                self.intro_seen = True
                self.save_unlocked_levels()
                self.state = GameState.ADVENTURE_LEVEL_SELECT
                self.adventure_level_selection = 0
            return
        
        # Shot 1: Meteorite animation
        if self.intro_current_image == 0:
            # Start meteorite after 0.5 seconds
            if self.intro_timer == 30 and not self.intro_meteorite_active and not self.intro_meteorite_crashed:
                self.intro_meteorite_active = True
                self.intro_meteorite_x = -50  # Start off-screen left
                self.intro_meteorite_y = SCREEN_HEIGHT // 2
            
            # Update meteorite position
            if self.intro_meteorite_active and not self.intro_meteorite_crashed:
                self.intro_meteorite_x += 8  # Move right
                
                # Crash when reaching center
                if self.intro_meteorite_x >= SCREEN_WIDTH // 2:
                    self.intro_meteorite_crashed = True
                    self.intro_meteorite_active = False
                    
                    # Create white particles at crash point
                    crash_x = SCREEN_WIDTH // 2
                    crash_y = SCREEN_HEIGHT // 2
                    for _ in range(20):
                        particle = {
                            'x': crash_x,
                            'y': crash_y,
                            'vx': random.uniform(-5, 5),
                            'vy': random.uniform(-5, 5),
                            'life': 30,
                            'max_life': 30
                        }
                        self.intro_meteorite_particles.append(particle)
            
            # Update particles
            for particle in self.intro_meteorite_particles[:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['life'] -= 1
                if particle['life'] <= 0:
                    self.intro_meteorite_particles.remove(particle)
        
        # Update timer for current image
        self.intro_timer += 1
        
        # Check if it's time to fade to next image
        if self.intro_timer >= self.intro_image_duration - self.intro_fade_duration and not self.intro_fading:
            self.intro_fading = True
            self.intro_fade_alpha = 0
        
        # Update fade
        if self.intro_fading:
            self.intro_fade_alpha += 255 / self.intro_fade_duration
            if self.intro_fade_alpha >= 255:
                self.intro_fade_alpha = 255
                # Move to next image
                self.intro_current_image += 1
                self.intro_timer = 0
                self.intro_fading = False
                
                # Reset meteorite animation for next shot
                self.intro_meteorite_active = False
                self.intro_meteorite_crashed = False
                self.intro_meteorite_particles = []
                
                # Check if we've shown all images
                if self.intro_current_image >= len(self.intro_images):
                    # Start final fade to black
                    self.intro_final_fade = True
                    self.intro_final_fade_timer = 0
    
    def draw_intro(self):
        """Draw intro sequence"""
        if self.intro_final_fade:
            # Fade to black
            self.screen.fill(BLACK)
            fade_alpha = int((self.intro_final_fade_timer / self.intro_final_fade_duration) * 255)
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill(BLACK)
            fade_surface.set_alpha(fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            return
        
        # Draw current image
        if self.intro_current_image < len(self.intro_images):
            self.screen.blit(self.intro_images[self.intro_current_image], (0, 0))
            
            # Draw next image on top if fading
            if self.intro_fading and self.intro_current_image + 1 < len(self.intro_images):
                next_img = self.intro_images[self.intro_current_image + 1].copy()
                next_img.set_alpha(int(self.intro_fade_alpha))
                self.screen.blit(next_img, (0, 0))
        
        # Shot 1: Draw meteorite animation
        if self.intro_current_image == 0:
            # Draw meteorite
            if self.intro_meteorite_active and self.isotope_img:
                # Scale and rotate the isotope
                meteorite_size = GRID_SIZE
                meteorite_scaled = pygame.transform.scale(self.isotope_img, (meteorite_size, meteorite_size))
                meteorite_rotated = pygame.transform.rotate(meteorite_scaled, -90)
                self.screen.blit(meteorite_rotated, 
                               (int(self.intro_meteorite_x) - meteorite_rotated.get_width() // 2, 
                                int(self.intro_meteorite_y) - meteorite_rotated.get_height() // 2))
            
            # Draw blue particles
            for particle in self.intro_meteorite_particles:
                alpha = int(255 * (particle['life'] / particle['max_life']))
                particle_size = 4
                particle_surf = pygame.Surface((particle_size, particle_size))
                particle_surf.fill((0, 100, 255))  # Blue color
                particle_surf.set_alpha(alpha)
                self.screen.blit(particle_surf, (int(particle['x']), int(particle['y'])))
    
    def start_outro(self):
        """Initialize outro sequence"""
        # If no outro images exist, skip directly to credits
        if len(self.outro_images) == 0:
            self.state = GameState.CREDITS
            self.music_manager.play_final_song()
            return
        
        self.state = GameState.OUTRO
        self.outro_current_image = 0
        self.outro_timer = 0
        self.outro_image_duration = 300  # 5 seconds at 60 FPS
        self.outro_fade_duration = 30  # 0.5 seconds fade
        self.outro_fade_alpha = 0
        self.outro_fading = False
        self.outro_final_fade = False
        self.outro_final_fade_timer = 0
        self.outro_final_fade_duration = 120  # 2 seconds fade to black
        
        # Image 4 panning variables (taller image that pans from top to bottom)
        self.outro_pan_offset = 0  # Y offset for panning
        self.outro_pan_speed = 0.5  # Pixels per frame to pan
        self.outro_pan_complete = False
        self.outro_pan_hold_timer = 0
        self.outro_pan_hold_duration = 600  # 10 seconds total at 60 FPS
        
        # Keep music playing (Final.ogg should already be playing)
        # No need to restart it
    
    def update_outro(self):
        """Update outro sequence"""
        if self.outro_final_fade:
            # Final fade to black after last image
            self.outro_final_fade_timer += 1
            if self.outro_final_fade_timer >= self.outro_final_fade_duration:
                # Outro complete - go to credits screen
                self.state = GameState.CREDITS
                # Music should already be playing Final.ogg
            return
        
        # Special handling for image 4 (index 3) - the tall panning image
        if self.outro_current_image == 3 and len(self.outro_images) > 3:
            outro_img = self.outro_images[3]
            img_width = outro_img.get_width()
            img_height = outro_img.get_height()
            
            # Calculate scaled height (image is scaled to screen width in rendering)
            scale_factor = SCREEN_WIDTH / img_width
            scaled_height = int(img_height * scale_factor)
            
            # Calculate max pan offset (stop panning to reveal more of the bottom)
            max_pan = scaled_height - SCREEN_HEIGHT - 32  # Stop earlier to show more content
            
            # DEBUG: Print on first frame only
            if self.outro_pan_offset == 0:
                print(f"DEBUG OUTRO: original={img_height}, scaled={scaled_height}, max_pan={max_pan}, SCREEN_HEIGHT={SCREEN_HEIGHT}")
            
            if not self.outro_pan_complete:
                # Pan down from top to bottom
                self.outro_pan_offset += self.outro_pan_speed
                
                # DEBUG: Print every 60 frames (once per second)
                if int(self.outro_pan_offset) % 60 == 0:
                    print(f"DEBUG PAN: offset={self.outro_pan_offset:.1f}, max_pan={max_pan}, complete={self.outro_pan_complete}")
                
                # Check if we've reached the bottom
                if self.outro_pan_offset >= max_pan:
                    print(f"DEBUG: Reached max_pan! Setting outro_pan_complete=True")
                    self.outro_pan_offset = max_pan
                    self.outro_pan_complete = True
            else:
                # Hold at bottom for remaining time
                self.outro_pan_hold_timer += 1
                
                # After holding for full duration, start final fade
                if self.outro_pan_hold_timer >= self.outro_pan_hold_duration:
                    # This is the last image, start final fade
                    self.outro_final_fade = True
                    self.outro_final_fade_timer = 0
            
            return
        
        # Standard timing for images 1-3
        self.outro_timer += 1
        
        # Check if it's time to fade to next image
        if self.outro_timer >= self.outro_image_duration - self.outro_fade_duration and not self.outro_fading:
            self.outro_fading = True
            self.outro_fade_alpha = 0
        
        # Update fade
        if self.outro_fading:
            self.outro_fade_alpha += 255 / self.outro_fade_duration
            if self.outro_fade_alpha >= 255:
                self.outro_fade_alpha = 255
                # Move to next image
                self.outro_current_image += 1
                self.outro_timer = 0
                self.outro_fading = False
                
                # Reset panning variables for image 4
                if self.outro_current_image == 3:
                    self.outro_pan_offset = 0
                    self.outro_pan_complete = False
                    self.outro_pan_hold_timer = 0
                
                # Check if we've shown all images
                if self.outro_current_image >= len(self.outro_images):
                    # Start final fade to black
                    self.outro_final_fade = True
                    self.outro_final_fade_timer = 0
    
    def draw_outro(self):
        """Draw outro sequence"""
        if self.outro_final_fade:
            # Fade to black
            self.screen.fill(BLACK)
            fade_alpha = int((self.outro_final_fade_timer / self.outro_final_fade_duration) * 255)
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill(BLACK)
            fade_surface.set_alpha(fade_alpha)
            self.screen.blit(fade_surface, (0, 0))
            return
        
        # Draw current image
        if self.outro_current_image < len(self.outro_images):
            outro_img = self.outro_images[self.outro_current_image]
            
            # Special handling for image 4 (index 3) - tall image with panning
            if self.outro_current_image == 3:
                # Scale the image to screen width, maintain aspect ratio
                img_width = outro_img.get_width()
                img_height = outro_img.get_height()
                scale_factor = SCREEN_WIDTH / img_width
                scaled_width = SCREEN_WIDTH
                scaled_height = int(img_height * scale_factor)
                
                # Scale the image
                scaled_img = pygame.transform.scale(outro_img, (scaled_width, scaled_height))
                
                # Create a subsurface for the visible portion (panning from top)
                visible_rect = pygame.Rect(0, int(self.outro_pan_offset), SCREEN_WIDTH, SCREEN_HEIGHT)
                try:
                    visible_portion = scaled_img.subsurface(visible_rect)
                    self.screen.blit(visible_portion, (0, 0))
                except:
                    # Fallback if subsurface fails
                    self.screen.blit(scaled_img, (0, -int(self.outro_pan_offset)))
            else:
                # Images 1-3: Scale to fit screen
                scaled_img = pygame.transform.scale(outro_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.screen.blit(scaled_img, (0, 0))
                
                # Draw next image on top if fading
                if self.outro_fading and self.outro_current_image + 1 < len(self.outro_images):
                    next_img = self.outro_images[self.outro_current_image + 1]
                    
                    # Check if next image is the tall one (image 4)
                    if self.outro_current_image + 1 == 3:
                        # Scale next image (image 4) to screen width
                        img_width = next_img.get_width()
                        img_height = next_img.get_height()
                        scale_factor = SCREEN_WIDTH / img_width
                        scaled_width = SCREEN_WIDTH
                        scaled_height = int(img_height * scale_factor)
                        next_scaled = pygame.transform.scale(next_img, (scaled_width, scaled_height))
                        
                        # Show top portion for fade-in
                        visible_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
                        try:
                            visible_portion = next_scaled.subsurface(visible_rect)
                            visible_portion_copy = visible_portion.copy()
                            visible_portion_copy.set_alpha(int(self.outro_fade_alpha))
                            self.screen.blit(visible_portion_copy, (0, 0))
                        except:
                            # Fallback
                            next_scaled_copy = next_scaled.copy()
                            next_scaled_copy.set_alpha(int(self.outro_fade_alpha))
                            self.screen.blit(next_scaled_copy, (0, 0))
                    else:
                        # Normal fade for images 1-3
                        next_scaled = pygame.transform.scale(next_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                        next_scaled.set_alpha(int(self.outro_fade_alpha))
                        self.screen.blit(next_scaled, (0, 0))
    
    def process_network_messages(self):
        """Process all pending network messages"""
        messages = self.network_manager.get_messages()
        
        for message in messages:
            msg_type = message.get('type')
            
            if msg_type == MessageType.INPUT.value:
                # Host receives input from client
                if self.network_manager.is_host():
                    self.handle_network_input(message)
            
            elif msg_type == MessageType.GAME_STATE.value:
                # Client receives game state from host
                if self.network_manager.is_client():
                    self.apply_network_game_state(message)
            
            elif msg_type == MessageType.GAME_START.value:
                # Client receives game start from host
                if self.network_manager.is_client():
                    self.handle_network_game_start(message)
            
            elif msg_type == MessageType.GAME_END.value:
                # Client receives game end from host
                if self.network_manager.is_client():
                    self.handle_network_game_end(message)
            
            elif msg_type == MessageType.PLAYER_ASSIGNED.value:
                # Client receives player ID assignment
                if self.network_manager.is_client():
                    self.network_player_id = message.get('player_id', 1)
                    print(f"Assigned as Player {self.network_player_id + 1}")
                    # After assignment, transition to lobby
                    self.is_multiplayer = True
                    self.is_network_game = True
                    self.state = GameState.MULTIPLAYER_LOBBY
            
            elif msg_type == MessageType.LOBBY_STATE.value:
                # Client receives lobby state update from host
                if self.network_manager.is_client():
                    self.player_slots = message.get('player_slots', ['player'] * 4)
                    self.lobby_settings = message.get('lobby_settings', self.lobby_settings)
                    # Update player count display
                    self.num_players = message.get('num_connected', 2)
                    # Store host IP if provided
                    host_ip = message.get('host_ip')
                    if host_ip:
                        self.network_host_ip = host_ip
            
            elif msg_type == MessageType.RETURN_TO_LOBBY.value:
                # Host sent everyone back to lobby
                self.state = GameState.MULTIPLAYER_LOBBY
                self.is_multiplayer = True
            
            elif msg_type == 'player_joined':
                # New player joined (from NetworkManager)
                player_id = message.get('player_id')
                address = message.get('address')
                print(f"Player {player_id + 1} joined from {address}")
                # Assign player ID to the new client
                assign_msg = create_player_assigned_message(player_id, player_id)
                self.network_manager.send_to_client(player_id - 1, assign_msg)
                
                # Check if game is in progress - send spectator mode message
                if self.state == GameState.PLAYING and self.network_manager.is_host():
                    print(f"Game in progress - Player {player_id + 1} joins as spectator")
                    walls = getattr(self, 'walls', [])
                    progress_msg = create_game_in_progress_message(self.snakes, self.food_items, walls)
                    self.network_manager.send_to_client(player_id - 1, progress_msg)
                else:
                    # Mark their slot as 'player' (connected)
                    if player_id < len(self.player_slots):
                        self.player_slots[player_id] = 'player'
                    # Broadcast updated lobby state to all clients
                    if self.network_manager.is_host():
                        self.broadcast_lobby_state()
            
            elif msg_type == 'player_left':
                # Player disconnected (from NetworkManager internal message)
                player_id = message.get('player_id')
                print(f"Player {player_id + 1} disconnected")
                # Handle disconnection during gameplay
                if self.state == GameState.PLAYING and self.network_manager.is_host():
                    self.handle_player_disconnect(player_id)
                # Update lobby state if in lobby
                elif self.state == GameState.MULTIPLAYER_LOBBY:
                    if player_id < len(self.player_slots):
                        self.player_slots[player_id] = 'cpu'  # Revert to CPU
                    self.broadcast_lobby_state()
            
            elif msg_type == MessageType.HOST_SHUTDOWN.value:
                # Host is shutting down - client should return to menu
                print("Host has shut down the game")
                self.network_manager.cleanup()
                self.is_network_game = False
                self.is_multiplayer = False
                self.state = GameState.NETWORK_MENU
            
            elif msg_type == MessageType.CLIENT_LEAVE.value:
                # Client is leaving (host receives this)
                if self.network_manager.is_host():
                    player_id = message.get('player_id')
                    print(f"Player {player_id + 1} is leaving the game")
                    self.handle_player_disconnect(player_id)
            
            elif msg_type == MessageType.PLAYER_DISCONNECTED.value:
                # Host notifies clients that a player disconnected
                if self.network_manager.is_client():
                    player_id = message.get('player_id')
                    print(f"Player {player_id + 1} has disconnected")
            
            elif msg_type == MessageType.GAME_IN_PROGRESS.value:
                # Client joined mid-game, enter spectator mode
                if self.network_manager.is_client():
                    print("Game in progress - entering spectator mode")
                    self.is_spectator = True
                    self.state = GameState.PLAYING
    
    def handle_network_input(self, message):
        """Host processes input from a network client"""
        player_id = message.get('player_id')
        direction_str = message.get('direction')
        
        # Convert direction string to Direction enum
        try:
            direction = Direction[direction_str]
        except:
            return
        
        # Apply input to the corresponding snake
        if player_id < len(self.snakes):
            snake = self.snakes[player_id]
            
            # Check if this player is in an egg (respawning)
            if player_id in self.respawning_players:
                print(f"Host received HATCH input from player {player_id}: {direction.name}")  # DEBUG
                egg_data = self.respawning_players[player_id]
                # Respawn the player with chosen direction
                self.respawn_player(player_id, egg_data['pos'], direction)
                print(f"  -> Player {player_id} hatched!")  # DEBUG
                return
            
            print(f"Host received input from player {player_id}: {direction.name}, current dir: {snake.direction.name}")  # DEBUG
            # Only update if it's a valid direction change (not opposite)
            if direction == Direction.UP and snake.direction != Direction.DOWN:
                snake.next_direction = direction
                print(f"  -> Applied UP to player {player_id}")  # DEBUG
            elif direction == Direction.DOWN and snake.direction != Direction.UP:
                snake.next_direction = direction
                print(f"  -> Applied DOWN to player {player_id}")  # DEBUG
            elif direction == Direction.LEFT and snake.direction != Direction.RIGHT:
                snake.next_direction = direction
                print(f"  -> Applied LEFT to player {player_id}")  # DEBUG
            elif direction == Direction.RIGHT and snake.direction != Direction.LEFT:
                snake.next_direction = direction
                print(f"  -> Applied RIGHT to player {player_id}")  # DEBUG
    
    def send_input_to_host(self, direction):
        """Client sends input to the host"""
        if not self.network_manager.is_client():
            print("ERROR: Not a client, can't send to host")  # DEBUG
            return
        
        if not hasattr(self, 'network_player_id'):
            print("ERROR: No network_player_id assigned")  # DEBUG
            return
        
        message = create_input_message(self.network_player_id, direction.name)
        print(f"Sending to network_manager: {message}")  # DEBUG
        self.network_manager.send_to_host(message)
        print(f"Message sent to host")  # DEBUG
    
    def broadcast_lobby_state(self):
        """Host broadcasts lobby state to all clients"""
        if not self.network_manager.is_host():
            return
        
        num_connected = self.network_manager.get_connected_players()
        message = create_lobby_state_message(self.player_slots, self.lobby_settings, num_connected, self.network_host_ip)
        self.network_manager.broadcast_to_clients(message)
    
    def broadcast_game_state(self):
        """Host broadcasts current game state to all clients"""
        if not self.network_manager.is_host():
            return
        
        # Only broadcast during active gameplay
        if self.state != GameState.PLAYING:
            return
        
        # Create and send game state message
        frame = getattr(self, 'network_frame', 0)
        message = create_game_state_message(self.snakes, self.food_items, frame, self.respawning_players)
        self.network_manager.broadcast_to_clients(message)
        self.network_frame = frame + 1
    
    def apply_network_game_state(self, message):
        """Client applies received game state from host"""
        # Feed state into interpolator for smooth lag compensation
        snake_data = message.get('snakes', [])
        frame_number = message.get('frame', 0)
        
        # Add to interpolation buffer
        self.network_interpolator.add_server_state(snake_data, frame_number)
        
        # Process snake data for death effects and state updates
        for data in snake_data:
            player_id = data.get('player_id')
            if player_id < len(self.snakes):
                snake = self.snakes[player_id]
                new_body = [tuple(pos) for pos in data.get('body', [])]
                new_alive = data.get('alive', True)
                
                # Check if snake actually moved (head position changed) for smooth interpolation
                snake_moved = False
                if hasattr(snake, 'body') and snake.body and new_body:
                    if snake.body[0] != new_body[0]:
                        snake_moved = True
                elif new_body and (not hasattr(snake, 'body') or not snake.body):
                    snake_moved = True
                
                # Update interpolation tracking when snake moves
                if snake_moved:
                    # Store previous body for per-frame interpolation
                    if hasattr(snake, 'body') and snake.body:
                        snake.previous_body = snake.body.copy()
                    else:
                        snake.previous_body = new_body.copy()
                    
                    # Track time between moves for interpolation speed
                    if hasattr(snake, 'move_timer'):
                        snake.last_move_interval = max(1, snake.move_timer)
                    else:
                        snake.last_move_interval = 16
                    
                    # Reset move timer for smooth interpolation
                    snake.move_timer = 0
                
                # Check for death transition (was alive, now dead) - trigger death effects
                was_alive = snake.alive
                
                if was_alive and not new_alive:
                    # Snake just died - play death sound and spawn particles
                    self.sound_manager.play('die')
                    # Spawn white particles on all body segments
                    for segment_x, segment_y in snake.body if snake.body else new_body:
                        self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                            segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                            None, None, particle_type='white')
                
                # Update authoritative state (used as fallback and for game logic)
                snake.body = new_body
                snake.alive = new_alive
                snake.lives = data.get('lives', 3)
                
                # Update direction
                try:
                    snake.direction = Direction[data.get('direction', 'RIGHT')]
                except:
                    pass
                
                # Initialize interpolation attributes if missing
                if not hasattr(snake, 'move_timer'):
                    snake.move_timer = 0
                if not hasattr(snake, 'last_move_interval'):
                    snake.last_move_interval = 16
                if not hasattr(snake, 'previous_body'):
                    snake.previous_body = snake.body.copy() if snake.body else []
        
        # Update food items - detect eaten food for effects
        food_data = message.get('food_items', [])
        new_food_items = [(tuple(item['pos']), item['type']) for item in food_data]
        
        # Check for eaten food (was in old list, not in new list, snake head at position)
        if hasattr(self, 'food_items') and self.food_items:
            old_food_set = {pos: ftype for pos, ftype in self.food_items}
            new_food_set = {pos: ftype for pos, ftype in new_food_items}
            
            # Find food that disappeared
            for pos, food_type in self.food_items:
                if pos not in new_food_set:
                    # Food was eaten - check if any snake head is near this position
                    for snake in self.snakes:
                        if snake.alive and snake.body:
                            head = snake.body[0]
                            # Check if head is at or adjacent to food position (to account for timing)
                            if head == pos or (abs(head[0] - pos[0]) <= 1 and abs(head[1] - pos[1]) <= 1):
                                fx, fy = pos
                                # Create particles and play sound based on food type
                                if food_type == 'worm':
                                    self.sound_manager.play('eat_fruit')
                                    self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                        fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, RED, 10)
                                elif food_type == 'apple':
                                    self.sound_manager.play('powerup')
                                    self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                        fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                        None, None, particle_type='rainbow')
                                elif food_type == 'black_apple':
                                    self.sound_manager.play('power_down')
                                    self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                        fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y,
                                                        None, None, particle_type='white')
                                break  # Only trigger once per food item
        
        self.food_items = new_food_items
        
        # Update respawning players (eggs)
        egg_data = message.get('respawning_players', [])
        self.respawning_players = {}
        for egg in egg_data:
            player_id = egg.get('player_id')
            self.respawning_players[player_id] = {
                'pos': tuple(egg.get('pos')),
                'timer': egg.get('timer', 0),
                'direction': None
            }
    
    def handle_network_game_start(self, message):
        """Client handles game start message from host"""
        print("Game starting!")
        num_players = message.get('num_players', 2)
        
        # Reset network interpolator for fresh game
        self.network_interpolator.reset()
        
        # Initialize client game state with level data from host
        # Load walls from message - walls come as dicts with 'x' and 'y' keys
        walls_data = message.get('walls', [])
        self.walls = [(int(w['x']), int(w['y'])) for w in walls_data]
        print(f"[CLIENT] Loaded {len(self.walls)} walls from host")
        
        # Load background from message (backgrounds are in img/bg/ folder)
        bg_filename = message.get('background', 'bg.png')
        bg_path = os.path.join(SCRIPT_DIR, 'img', 'bg', bg_filename)
        try:
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            print(f"[CLIENT] Loaded background: {bg_filename}")
        except Exception as e:
            print(f"[CLIENT] Could not load background {bg_filename}: {e}")
        
        self.food_items = []
        self.particles = []
        self.bullets = []
        self.respawning_players = {}
        
        # Initialize snakes for all players with proper interpolation attributes
        self.snakes = []
        for i in range(num_players):
            snake = Snake(player_id=i)
            snake.lives = 3
            # Initialize movement tracking for smooth interpolation
            snake.move_timer = 0
            snake.last_move_interval = 16
            snake.previous_body = snake.body.copy()
            self.snakes.append(snake)
        self.snake = self.snakes[0]  # For backwards compatibility
        
        # Setup player controllers (keyboard for client)
        self.player_controllers = [('keyboard', 0)] * num_players
        
        self.state = GameState.PLAYING
        
        # Sync music with host - check for track BEFORE stopping game over music
        # (stop_game_over_music calls play_next internally which we want to avoid)
        music_track_index = message.get('music_track')
        print(f"[CLIENT] Received music_track_index: {music_track_index}")  # DEBUG
        
        # Stop any game over music without starting new music
        if self.music_manager.game_over_mode:
            self.music_manager.game_over_mode = False
            pygame.mixer.music.stop()
        
        # Now play the correct music by index (uses client's local paths)
        if music_track_index is not None:
            print(f"[CLIENT] Playing track by index: {music_track_index}")  # DEBUG
            self.music_manager.play_by_index(music_track_index)
        else:
            print("[CLIENT] No music track received, playing random")  # DEBUG
            if self.music_manager.theme_mode:
                pygame.mixer.music.stop()
                self.music_manager.theme_mode = False
            self.music_manager.play_next()
    
    def handle_network_game_end(self, message):
        """Client handles game end message from host"""
        winner = message.get('winner')
        if winner >= 0:
            print(f"Game over! Player {winner + 1} wins!")
        else:
            print(f"Game over! Draw!")
        # Start the same delay as host before showing game over screen
        self.multiplayer_end_timer = 120  # 2 seconds delay to match host
        self.multiplayer_end_timer_phase = 1  # Phase 1: waiting to show game over
        self.network_game_over_auto_timer = 600  # 10 seconds auto-progress to lobby
    
    def handle_player_disconnect(self, player_id):
        """Host handles a player disconnecting during gameplay"""
        if not self.network_manager.is_host():
            return
        
        # Find the snake for this player
        if player_id < len(self.snakes):
            snake = self.snakes[player_id]
            
            # Remove all their lives and kill them
            snake.lives = 0
            if snake.alive:
                snake.alive = False
                self.sound_manager.play('die')
                
                # Spawn death particles
                for segment_x, segment_y in snake.body:
                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                        None, None, particle_type='white')
            
            # Remove from respawning if they were in an egg
            if player_id in self.respawning_players:
                del self.respawning_players[player_id]
            
            print(f"Player {player_id + 1} disconnected - removed from game")
        
        # Notify other clients
        disconnect_msg = create_player_disconnected_message(player_id)
        self.network_manager.broadcast_to_clients(disconnect_msg)
        
        # Check if this triggers win condition
        players_with_lives = [s for s in self.snakes if s.lives > 0]
        if len(players_with_lives) == 1:
            winner = players_with_lives[0]
            print(f"Player {winner.player_id + 1} wins due to disconnect!")
            self.sound_manager.play('level_up')
            final_scores = [0] * len(self.snakes)
            end_msg = create_game_end_message(winner.player_id, final_scores)
            self.network_manager.broadcast_to_clients(end_msg)
            self.multiplayer_end_timer = 120
        elif len(players_with_lives) == 0:
            print("Draw - all players eliminated!")
            self.sound_manager.play('no_lives')
            final_scores = [0] * len(self.snakes)
            end_msg = create_game_end_message(-1, final_scores)
            self.network_manager.broadcast_to_clients(end_msg)
            self.multiplayer_end_timer = 120
    
    def exit_network_game(self):
        """Exit the current network game (works for both host and client)"""
        if self.network_manager.is_host():
            # Host: notify all clients, return everyone to lobby
            print("Host exiting game - returning all players to lobby")
            return_msg = create_return_to_lobby_message()
            self.network_manager.broadcast_to_clients(return_msg)
            self.state = GameState.MULTIPLAYER_LOBBY
            self.is_multiplayer = True
            self.broadcast_lobby_state()
        elif self.network_manager.is_client():
            # Client: notify host of leaving, then disconnect
            print("Client leaving game")
            if hasattr(self, 'network_player_id'):
                leave_msg = create_client_leave_message(self.network_player_id)
                self.network_manager.send_to_host(leave_msg)
            self.network_manager.cleanup()
            self.is_network_game = False
            self.is_multiplayer = False
            self.state = GameState.NETWORK_MENU
    
    def shutdown_network_game(self):
        """Host shuts down the entire network game"""
        if not self.network_manager.is_host():
            return
        
        print("Host shutting down network game")
        shutdown_msg = create_host_shutdown_message()
        self.network_manager.broadcast_to_clients(shutdown_msg)
        self.network_manager.cleanup()
        self.is_network_game = False
        self.is_multiplayer = False
        self.state = GameState.NETWORK_MENU
    
    def check_client_connection(self):
        """Check client connection health and handle disconnection"""
        if not self.network_manager.is_client():
            return
        
        if self.network_manager.is_connection_lost():
            # Connection was truly lost - don't auto-reconnect, just return to menu
            reason = self.network_manager.get_disconnect_reason()
            print(f"Connection lost: {reason}")
            print("Returning to network menu - you can rejoin manually")
            self.network_manager.cleanup()
            self.is_network_game = False
            self.is_multiplayer = False
            self.state = GameState.NETWORK_MENU
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            
            self.handle_input()
            
            # Process network messages (if in network game)
            if self.is_network_game:
                self.process_network_messages()
                # Check client connection health
                self.check_client_connection()
            
            # Handle splash screen timer
            if self.state == GameState.SPLASH:
                current_time = pygame.time.get_ticks()
                if current_time - self.splash_start_time >= self.splash_duration:
                    # Transition to menu after 3 seconds
                    self.state = GameState.MENU
            
            # Handle intro sequence
            if self.state == GameState.INTRO:
                self.update_intro()
                # Update music - intro uses menu music (theme)
                self.music_manager.update(in_menu=True)
            
            # Handle outro sequence
            if self.state == GameState.OUTRO:
                self.update_outro()
                # Update music - outro uses Final.ogg
                self.music_manager.update(in_menu=True)
            
            if self.state == GameState.EGG_HATCHING:
                # In boss mode, give player 5 seconds to choose direction (after death, not initial spawn)
                if hasattr(self, 'boss_active') and self.boss_active:
                    # Check if this is a respawn (not the initial spawn)
                    is_respawn = hasattr(self, 'boss_egg_is_respawn') and self.boss_egg_is_respawn
                    
                    if is_respawn:
                        # Give player 5 seconds to choose a direction
                        self.egg_timer = getattr(self, 'egg_timer', 0) + 1
                        if self.egg_timer >= 300:  # 5 seconds at 60 FPS
                            # Auto-hatch facing right after 5 seconds
                            self.hatch_egg(Direction.RIGHT)
                            self.boss_egg_is_respawn = False
                            self.egg_timer = 0
                    else:
                        # Initial spawn - immediately hatch facing right
                        self.hatch_egg(Direction.RIGHT)
                
                # Update particles (death particles from previous life)
                self.particles = [p for p in self.particles if p.is_alive()]
                for particle in self.particles:
                    particle.update()
                
                # Update egg pieces and animations while waiting for player input
                self.egg_pieces = [p for p in self.egg_pieces if p.is_alive()]
                for piece in self.egg_pieces:
                    piece.update()
                
                # Update worm animation
                if self.worm_frames:
                    self.worm_animation_counter += 1
                    if self.worm_animation_counter >= self.worm_animation_speed:
                        self.worm_animation_counter = 0
                        self.worm_frame_index = (self.worm_frame_index + 1) % len(self.worm_frames)
                
                # Update music - LEVEL_COMPLETE is a menu state (returning to menus)
                self.music_manager.update(in_menu=True)
            elif self.state == GameState.MUSIC_PLAYER:
                # Auto-advance to next track when current track finishes
                if self.music_player_playing and not pygame.mixer.music.get_busy():
                    # Track finished, advance to next
                    self.music_player_next_track()
            elif self.state == GameState.PLAYING:
                self.update_game()
            elif self.state == GameState.GAME_OVER:
                # Update game over timer and music even when not playing
                # Game over has its own music, so pass in_menu=False
                self.music_manager.update(in_menu=False)
                if self.game_over_timer > 0:
                    self.game_over_timer -= 1
                    if self.game_over_timer == 0:
                        # Timer expired, transition to appropriate screen
                        # Only check for high score in endless mode (not adventure or multiplayer)
                        if self.game_mode == "endless" and self.is_high_score(self.score):
                            self.state = GameState.HIGH_SCORE_ENTRY
                            self.player_name = ['A', 'A', 'A']
                            self.name_index = 0
                            # Pick a random hint for this high score entry session
                            hints = [
                                "Length increases score multiplier!", 
                                "Fill entire screen for massive bonus!", 
                                "Your level increases score multiplier!", 
                                "Your level increases snakebird speed!", 
                                "Snakebird grows faster on hard!"]
                            self.current_hint = random.choice(hints)
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.event.set_grab(False)  # Release input grab before quitting
        pygame.quit()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.SPLASH:
            self.draw_splash()
        elif self.state == GameState.INTRO:
            self.draw_intro()
        elif self.state == GameState.OUTRO:
            self.draw_outro()
        elif self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.SINGLE_PLAYER_MENU:
            self.draw_single_player_menu()
        elif self.state == GameState.ADVENTURE_LEVEL_SELECT:
            self.draw_adventure_level_select()
        elif self.state == GameState.MULTIPLAYER_MENU:
            self.draw_multiplayer_menu()
        elif self.state == GameState.NETWORK_MENU:
            self.draw_network_menu()
        elif self.state == GameState.NETWORK_HOST_LOBBY:
            self.draw_network_host_lobby()
        elif self.state == GameState.NETWORK_CLIENT_LOBBY:
            self.draw_network_client_lobby()
        elif self.state == GameState.MULTIPLAYER_LEVEL_SELECT:
            self.draw_multiplayer_level_select()
        elif self.state == GameState.MULTIPLAYER_LOBBY:
            self.draw_multiplayer_lobby()
        elif self.state == GameState.EGG_HATCHING:
            # Draw the live game world, then overlay egg hatching UI
            self.draw_game()
            self.draw_egg_hatching_overlay()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.PAUSED:
            self.draw_game()
            self.draw_pause()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.HIGH_SCORE_ENTRY:
            self.draw_high_score_entry()
        elif self.state == GameState.HIGH_SCORES:
            self.draw_high_scores()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_game()
            self.draw_level_complete()
        elif self.state == GameState.EXTRAS_MENU:
            self.draw_extras_menu()
        elif self.state == GameState.ACHIEVEMENTS:
            self.draw_achievements()
        elif self.state == GameState.MUSIC_PLAYER:
            self.draw_music_player()
        elif self.state == GameState.LEVEL_EDITOR_MENU:
            self.draw_level_editor_menu()
        elif self.state == GameState.CREDITS:
            self.draw_credits()
        elif self.state == GameState.DIFFICULTY_SELECT:
            self.draw_difficulty_select()
        
        # Scale the render surface to the display surface
        scaled_screen = pygame.transform.scale(self.screen, (SCREEN_WIDTH * self.scale, SCREEN_HEIGHT * self.scale))
        
        # Apply screen shake offset if active
        shake_x, shake_y = self.screen_shake_offset if hasattr(self, 'screen_shake_offset') else (0, 0)
        self.display.blit(scaled_screen, (shake_x * self.scale, shake_y * self.scale))
        pygame.display.flip()
    
    def draw_splash(self):
        """Draw the splash screen."""
        if self.splash_screen:
            self.screen.blit(self.splash_screen, (0, 0))
        else:
            # Fallback if splash screen not loaded
            self.screen.fill(BLACK)
    
    def draw_menu(self):
        # Draw title screen image (includes game name)
        if self.title_screen:
            self.screen.blit(self.title_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
            # Fallback: Render title text if no images available
            title = self.font_large.render("SNAKE", True, NEON_GREEN)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
            self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.menu_options):
            color = NEON_YELLOW if i == self.menu_selection else NEON_CYAN
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, 146 + i * 25))  # Moved lower to avoid snake
            
            # Draw text
            self.screen.blit(text, text_rect)
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 145 + i * 25))  # Moved lower to avoid snake
            
            # Draw text
            self.screen.blit(text, text_rect)
        
        # Draw Tweetrix logo at bottom left
        if self.tweetrix_logo:
            logo_x = 5  # 5 pixels from left edge
            logo_y = SCREEN_HEIGHT - self.tweetrix_logo.get_height() - 5  # 5 pixels from bottom
            self.screen.blit(self.tweetrix_logo, (logo_x, logo_y))
    
    def draw_single_player_menu(self):
        """Draw the single player mode selection menu."""
        # Use difficulty screen as background (no text conflicts)
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("SINGLE PLAYER", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 52))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("SINGLE PLAYER", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.single_player_options):
            color = NEON_YELLOW if i == self.single_player_selection else NEON_CYAN
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, 131 + i * 25))  # Moved lower to avoid snake
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 130 + i * 25))  # Moved lower to avoid snake
            self.screen.blit(text, text_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press B to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 201))  # Moved below menu options
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press B to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 200))  # Moved below menu options
        self.screen.blit(hint_text, hint_rect)
    
    def draw_adventure_level_select(self):
        """Draw the adventure mode level selection screen."""
        # Use difficulty screen or background
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("LEVEL SELECT", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 17))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("LEVEL SELECT", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 15))
        self.screen.blit(title, title_rect)
        
        # Draw level grid (8 columns x 4 rows for 32 levels)
        cols = 8
        rows = 4
        cell_size = 25  # Halved from 50
        spacing = 5  # Halved from 10
        start_x = (SCREEN_WIDTH - (cols * cell_size + (cols - 1) * spacing)) // 2
        start_y = 40  # Halved from 80
        
        for i in range(self.total_levels):
            row = i // cols
            col = i % cols
            x = start_x + col * (cell_size + spacing)
            y = start_y + row * (cell_size + spacing)
            
            # Draw level box
            rect = pygame.Rect(x, y, cell_size, cell_size)
            level_num = i + 1
            is_unlocked = self.is_level_unlocked(level_num)
            
            # Different colors for locked, selected, unlocked levels
            if not is_unlocked:
                # Locked level - dark/grayed out
                color = DARK_GRAY
                border_color = DARK_GRAY
                fill_color = (30, 30, 30)
                pygame.draw.rect(self.screen, fill_color, rect)  # Fill background
            elif i == self.adventure_level_selection:
                # Selected level
                color = NEON_YELLOW
                border_color = NEON_YELLOW
            elif i >= 30:  # Bonus levels
                color = NEON_PURPLE
                border_color = NEON_PURPLE
            else:
                # Unlocked level
                color = NEON_CYAN
                border_color = NEON_CYAN
            
            # Draw box border
            pygame.draw.rect(self.screen, border_color, rect, 3)
            
            # Draw level number or lock icon for locked levels
            if not is_unlocked:
                # Draw "X" or "?" for locked levels
                lock_text = self.font_medium.render("?", True, color)
                lock_rect = lock_text.get_rect(center=rect.center)
                self.screen.blit(lock_text, lock_rect)
            else:
                num_text = self.font_small.render(str(level_num), True, color)
                num_rect = num_text.get_rect(center=rect.center)
                self.screen.blit(num_text, num_rect)
        
        # Display selected level info
        selected_level = self.adventure_level_selection + 1
        info_y = start_y + rows * (cell_size + spacing) + 10
        
        info_text = self.font_medium.render("Level {}".format(selected_level), True, BLACK)
        info_rect = info_text.get_rect(center=((SCREEN_WIDTH // 2)+2, info_y + 2))
        self.screen.blit(info_text, info_rect)
        info_text = self.font_medium.render("Level {}".format(selected_level), True, NEON_GREEN)
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, info_y))
        self.screen.blit(info_text, info_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press Start to begin", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 201))  # Moved below level boxes
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press Start to begin", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 200))  # Moved below level boxes
        self.screen.blit(hint_text, hint_rect)
        
        # View Intro button (if intro images are available)
        if len(self.intro_images) > 0:
            intro_text = self.font_small.render("Press Y to view intro", True, BLACK)
            intro_rect = intro_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))
            self.screen.blit(intro_text, intro_rect)
            intro_text = self.font_small.render("Press Y to view intro", True, NEON_CYAN)
            intro_rect = intro_text.get_rect(center=(SCREEN_WIDTH // 2, 225))
            self.screen.blit(intro_text, intro_rect)
    
    def draw_multiplayer_menu(self):
        """Draw the multiplayer mode selection menu."""
        # Use difficulty screen as background (no text conflicts)
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        elif self.title_screen:
            self.screen.blit(self.title_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("MULTIPLAYER", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 39))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("MULTIPLAYER", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 37))
        self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.multiplayer_menu_options):
            color = NEON_YELLOW if i == self.multiplayer_menu_selection else NEON_CYAN
            
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, 131 + i * 20))  # Moved lower to avoid snake
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 130 + i * 20))  # Moved lower to avoid snake
            self.screen.blit(text, text_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press B to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))  # Halved from 452
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press B to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Halved from 450
        self.screen.blit(hint_text, hint_rect)
    
    def draw_network_menu(self):
        """Draw the network game menu (Host/Join)."""
        # Use difficulty screen as background
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        elif self.title_screen:
            self.screen.blit(self.title_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("NETWORK GAME", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 39))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("NETWORK GAME", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 37))
        self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.network_menu_options):
            color = NEON_YELLOW if i == self.network_menu_selection else NEON_CYAN
            
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, 121 + i * 20))
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 120 + i * 20))
            self.screen.blit(text, text_rect)
        
        # Status message if any
        if self.network_status_message:
            status_text = self.font_small.render(self.network_status_message, True, BLACK)
            status_rect = status_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 196))
            self.screen.blit(status_text, status_rect)
            status_text = self.font_small.render(self.network_status_message, True, NEON_ORANGE)
            status_rect = status_text.get_rect(center=(SCREEN_WIDTH // 2, 195))
            self.screen.blit(status_text, status_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press B to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press B to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_network_host_lobby(self):
        """Draw the host lobby screen (waiting for players to join)."""
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("HOSTING GAME", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 29))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("HOSTING GAME", True, NEON_GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 27))
        self.screen.blit(title, title_rect)
        
        # Show host IP
        ip_text = self.font_medium.render(f"Your IP: {self.network_host_ip}", True, BLACK)
        ip_rect = ip_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 61))
        self.screen.blit(ip_text, ip_rect)
        ip_text = self.font_medium.render(f"Your IP: {self.network_host_ip}", True, NEON_CYAN)
        ip_rect = ip_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(ip_text, ip_rect)
        
        # Show connected players count
        player_count = self.network_manager.get_connected_players()
        count_text = self.font_medium.render(f"Players: {player_count}/4", True, BLACK)
        count_rect = count_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 91))
        self.screen.blit(count_text, count_rect)
        count_text = self.font_medium.render(f"Players: {player_count}/4", True, NEON_YELLOW)
        count_rect = count_text.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(count_text, count_rect)
        
        # Show connected client addresses
        y_offset = 120
        for i, addr in enumerate(self.network_manager.client_addresses):
            client_text = self.font_small.render(f"Player {i+2}: {addr}", True, BLACK)
            client_rect = client_text.get_rect(center=((SCREEN_WIDTH // 2)+1, y_offset+1))
            self.screen.blit(client_text, client_rect)
            client_text = self.font_small.render(f"Player {i+2}: {addr}", True, WHITE)
            client_rect = client_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(client_text, client_rect)
            y_offset += 15
        
        # Status message
        if self.network_status_message:
            status_text = self.font_small.render(self.network_status_message, True, BLACK)
            status_rect = status_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 186))
            self.screen.blit(status_text, status_rect)
            status_text = self.font_small.render(self.network_status_message, True, NEON_ORANGE)
            status_rect = status_text.get_rect(center=(SCREEN_WIDTH // 2, 185))
            self.screen.blit(status_text, status_rect)
        
        # Instructions
        hint1 = self.font_small.render("Waiting for players to join...", True, BLACK)
        hint1_rect = hint1.get_rect(center=((SCREEN_WIDTH // 2)+1, 206))
        self.screen.blit(hint1, hint1_rect)
        hint1 = self.font_small.render("Waiting for players to join...", True, NEON_PURPLE)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, 205))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = self.font_small.render("Press START to begin (2+ players)", True, BLACK)
        hint2_rect = hint2.get_rect(center=((SCREEN_WIDTH // 2)+1, 221))
        self.screen.blit(hint2, hint2_rect)
        hint2 = self.font_small.render("Press START to begin (2+ players)", True, NEON_CYAN)
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(hint2, hint2_rect)
    
    def draw_network_client_lobby(self):
        """Draw the client lobby screen (server list or waiting)."""
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("JOIN GAME", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 29))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("JOIN GAME", True, NEON_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 27))
        self.screen.blit(title, title_rect)
        
        if self.network_manager.is_connected():
            # Connected - waiting for host to start
            status_text = self.font_medium.render("Connected!", True, BLACK)
            status_rect = status_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 91))
            self.screen.blit(status_text, status_rect)
            status_text = self.font_medium.render("Connected!", True, NEON_GREEN)
            status_rect = status_text.get_rect(center=(SCREEN_WIDTH // 2, 90))
            self.screen.blit(status_text, status_rect)
            
            wait_text = self.font_small.render("Waiting for host to start game...", True, BLACK)
            wait_rect = wait_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 121))
            self.screen.blit(wait_text, wait_rect)
            wait_text = self.font_small.render("Waiting for host to start game...", True, NEON_PURPLE)
            wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
            self.screen.blit(wait_text, wait_rect)
        else:
            # Not connected - show server list from LAN discovery
            # Update discovered servers from network manager
            self.discovered_servers = self.network_manager.get_discovered_servers()
            
            prompt_text = self.font_medium.render("LAN Servers:", True, BLACK)
            prompt_rect = prompt_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 51))
            self.screen.blit(prompt_text, prompt_rect)
            prompt_text = self.font_medium.render("LAN Servers:", True, NEON_YELLOW)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(prompt_text, prompt_rect)
            
            if len(self.discovered_servers) > 0:
                # Show server list (max 4 visible)
                max_visible = 4
                start_y = 75
                for i, (name, ip, port) in enumerate(self.discovered_servers[:max_visible]):
                    # Highlight selected server
                    if i == self.server_selection:
                        color = NEON_YELLOW
                        prefix = "> "
                    else:
                        color = NEON_CYAN
                        prefix = "  "
                    
                    # Truncate name if too long
                    display_name = name[:16] if len(name) > 16 else name
                    server_text = f"{prefix}{display_name} ({ip})"
                    
                    text = self.font_small.render(server_text, True, BLACK)
                    text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, start_y + i * 18))
                    self.screen.blit(text, text_rect)
                    text = self.font_small.render(server_text, True, color)
                    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y - 1 + i * 18))
                    self.screen.blit(text, text_rect)
                
                if len(self.discovered_servers) > max_visible:
                    more_text = f"... and {len(self.discovered_servers) - max_visible} more"
                    text = self.font_small.render(more_text, True, WHITE)
                    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + max_visible * 18))
                    self.screen.blit(text, text_rect)
            else:
                # No servers found
                no_server = self.font_small.render("No servers found", True, BLACK)
                no_rect = no_server.get_rect(center=((SCREEN_WIDTH // 2)+1, 96))
                self.screen.blit(no_server, no_rect)
                no_server = self.font_small.render("No servers found", True, NEON_ORANGE)
                no_rect = no_server.get_rect(center=(SCREEN_WIDTH // 2, 95))
                self.screen.blit(no_server, no_rect)
                
                scanning = self.font_small.render("Scanning LAN...", True, WHITE)
                scan_rect = scanning.get_rect(center=(SCREEN_WIDTH // 2, 115))
                self.screen.blit(scanning, scan_rect)
        
        # Status message
        if self.network_status_message:
            status_text = self.font_small.render(self.network_status_message, True, BLACK)
            status_rect = status_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 181))
            self.screen.blit(status_text, status_rect)
            status_text = self.font_small.render(self.network_status_message, True, NEON_ORANGE)
            status_rect = status_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
            self.screen.blit(status_text, status_rect)
        
        # Bottom hints
        hint1 = self.font_small.render("START: Join | Y/R: Refresh | B: Back", True, BLACK)
        hint1_rect = hint1.get_rect(center=((SCREEN_WIDTH // 2)+1, 211))
        self.screen.blit(hint1, hint1_rect)
        hint1 = self.font_small.render("START: Join | Y/R: Refresh | B: Back", True, NEON_PURPLE)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(hint1, hint1_rect)
    
    def draw_extras_menu(self):
        """Draw the extras menu."""
        # Use difficulty screen as background (no text conflicts)
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("EXTRAS", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+2, 39))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("EXTRAS", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 37))
        self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.extras_menu_options):
            color = NEON_YELLOW if i == self.extras_menu_selection else NEON_CYAN
            
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, 125 + i * 17))  # Moved lower and spread out more
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 124 + i * 17))  # Moved lower and spread out more
            self.screen.blit(text, text_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press B to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 211))  # Moved below menu options
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press B to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 210))  # Moved below menu options
        self.screen.blit(hint_text, hint_rect)
    
    def draw_multiplayer_level_select(self):
        """Draw the multiplayer level selection screen with preview."""
        # Use background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("SELECT LEVEL", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 18))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("SELECT LEVEL", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 15))
        self.screen.blit(title, title_rect)
        
        if len(self.multiplayer_levels) == 0:
            # No levels available
            msg = self.font_medium.render("No multiplayer levels found", True, BLACK)
            msg_rect = msg.get_rect(center=((SCREEN_WIDTH // 2)+1, 121))  # Halved from 242
            self.screen.blit(msg, msg_rect)
            msg = self.font_medium.render("No multiplayer levels found", True, NEON_CYAN)
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, 120))  # Halved from 240
            self.screen.blit(msg, msg_rect)
        else:
            # Draw level list on the left side
            list_x = 15  # Halved from 30
            list_y = 70  # Moved down to avoid title overlap
            line_height = 14  # Halved from 28
            visible_levels = 10  # Show 10 levels at a time
            
            # Calculate scroll offset to keep selected level visible
            scroll_offset = max(0, self.multiplayer_level_selection - visible_levels + 1)
            if self.multiplayer_level_selection < scroll_offset:
                scroll_offset = self.multiplayer_level_selection
            
            # Draw visible levels
            for i in range(min(visible_levels, len(self.multiplayer_levels))):
                level_index = i + scroll_offset
                if level_index >= len(self.multiplayer_levels):
                    break
                
                level = self.multiplayer_levels[level_index]
                y_pos = list_y + i * line_height
                
                # Highlight selected level
                is_selected = (level_index == self.multiplayer_level_selection)
                
                if is_selected:
                    # Draw selection indicator
                    indicator = self.font_small.render(">", True, NEON_YELLOW)
                    self.screen.blit(indicator, (list_x - 15, y_pos))
                
                # Draw level number and name
                level_text = "Level {:02d}".format(level['number'])
                color = NEON_CYAN if is_selected else WHITE
                
                # Shadow
                text_shadow = self.font_small.render(level_text, True, BLACK)
                self.screen.blit(text_shadow, (list_x + 2, y_pos + 2))
                
                # Main text
                text = self.font_small.render(level_text, True, color)
                self.screen.blit(text, (list_x, y_pos))
            
            # Draw scroll indicators if needed
            if scroll_offset > 0:
                up_arrow = self.font_small.render("▲ More", True, NEON_YELLOW)
                self.screen.blit(up_arrow, (list_x, 40))
            
            if scroll_offset + visible_levels < len(self.multiplayer_levels):
                down_arrow = self.font_small.render("▼ More", True, NEON_YELLOW)
                self.screen.blit(down_arrow, (list_x, list_y + visible_levels * line_height + 5))
            
            # Draw preview on the right side
            preview_x = 135  # Centered in right half of screen
            preview_y = 70   # Same starting height as level list
            
            # Preview box background (adjusted size for 90px preview)
            preview_box = pygame.Surface((110, 110))
            preview_box.fill(BLACK)
            preview_box.set_alpha(200)
            self.screen.blit(preview_box, (preview_x - 10, preview_y - 10))
            
            # Draw "PREVIEW" label
            preview_label = self.font_small.render("PREVIEW", True, BLACK)
            self.screen.blit(preview_label, (preview_x + 12, 45))
            preview_label = self.font_small.render("PREVIEW", True, NEON_YELLOW)
            self.screen.blit(preview_label, (preview_x + 10, 43))
            
            # Generate and display preview
            preview_surface = self.generate_level_preview(self.multiplayer_level_selection)
            if preview_surface:
                self.screen.blit(preview_surface, (preview_x, preview_y))
            
            # Draw selected level info below preview
            selected_level = self.multiplayer_levels[self.multiplayer_level_selection]
            info_y = preview_y + 100
            
            # Level number
            level_info = "Level {:02d}".format(selected_level['number'])
            info_shadow = self.font_medium.render(level_info, True, BLACK)
            self.screen.blit(info_shadow, (preview_x + 2, info_y + 2))
            info_text = self.font_medium.render(level_info, True, NEON_CYAN)
            self.screen.blit(info_text, (preview_x, info_y))
            
            # Wall count
            wall_count = len(selected_level['walls'])
            walls_text = "{} walls".format(wall_count)
            walls_shadow = self.font_small.render(walls_text, True, BLACK)
            self.screen.blit(walls_shadow, (preview_x + 12, info_y + 17))
            walls_display = self.font_small.render(walls_text, True, WHITE)
            self.screen.blit(walls_display, (preview_x + 10, info_y + 15))
        
        # Hint text
        hint_text = self.font_small.render("Start to select, Back to cancel", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))  # Halved from 452
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Start to select, Back to cancel", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Halved from 450
        self.screen.blit(hint_text, hint_rect)
    
    def draw_multiplayer_lobby(self):
        """Draw the multiplayer lobby with settings and players."""
        # Use multiplayer setup background
        if self.multi_bg:
            self.screen.blit(self.multi_bg, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("SETUP", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 18))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("SETUP", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 15))
        self.screen.blit(title, title_rect)
        
        y = 45  # Start higher to fit everything
        center_x = SCREEN_WIDTH // 2
        
        # Settings section with visual icons
        # Lives setting with egg icons
        is_selected = (self.lobby_selection == 0)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "Lives" label
        label = self.font_small.render("Lives:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 50 + 1, y + 1))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("Lives:", True, color)
        label_rect = label.get_rect(midright=(center_x - 50, y))
        self.screen.blit(label, label_rect)
        
        # Draw egg icons for lives (show all eggs, not capped at 5)
        lives = self.lobby_settings['lives']
        egg_size = 14  # Halved from 28
        egg_spacing = 16  # Halved from 32
        start_x = center_x - 40  # Halved from 80
        max_eggs_per_row = 10  # Display up to 10 eggs
        
        for i in range(max_eggs_per_row):
            if i < lives and self.player_egg_imgs and self.player_egg_imgs[0]:
                # Show filled egg
                egg = pygame.transform.scale(self.player_egg_imgs[0], (egg_size, egg_size))
                self.screen.blit(egg, (start_x + i * egg_spacing, y - egg_size // 2))
            elif i < max_eggs_per_row:
                # Show dimmed egg for empty slots
                if self.player_egg_imgs and self.player_egg_imgs[0]:
                    egg = pygame.transform.scale(self.player_egg_imgs[0], (egg_size, egg_size))
                    egg = egg.copy()  # Make a copy to avoid modifying original
                    egg.set_alpha(50)  # Dim the egg
                    self.screen.blit(egg, (start_x + i * egg_spacing, y - egg_size // 2))
        
        y += 18  # Compact spacing
        
        # Item Spawn setting with apple icons (1-3 apples)
        is_selected = (self.lobby_selection == 1)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "Item Spawn" label
        label = self.font_small.render("Item Spawn:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 50 + 1, y + 1))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("Item Spawn:", True, color)
        label_rect = label.get_rect(midright=(center_x - 50, y))
        self.screen.blit(label, label_rect)
        
        # Draw apple icons (1=Low, 2=Normal, 3=High) using bonus.png
        item_freq = self.lobby_settings['item_frequency']
        num_apples = item_freq + 1  # 0→1, 1→2, 2→3
        apple_size = 14  # Halved from 28
        apple_spacing = 16  # Halved from 32
        start_x = center_x - 40  # Halved from 80
        
        for i in range(3):  # Max 3 apples
            if self.bonus_img:
                apple = pygame.transform.scale(self.bonus_img, (apple_size, apple_size))
                if i < num_apples:
                    # Show filled/active apple
                    self.screen.blit(apple, (start_x + i * apple_spacing, y - apple_size // 2))
                else:
                    # Show dimmed apple for inactive slots
                    apple = apple.copy()
                    apple.set_alpha(50)
                    self.screen.blit(apple, (start_x + i * apple_spacing, y - apple_size // 2))
        
        y += 18  # Compact spacing
        
        # CPU Difficulty with star rating
        is_selected = (self.lobby_selection == 2)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "CPU Difficulty" label
        label = self.font_small.render("CPU Level:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 50 + 1, y + 1))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("CPU Level:", True, color)
        label_rect = label.get_rect(midright=(center_x - 50, y))
        self.screen.blit(label, label_rect)
        
        # Draw star rating (4 stars total: easy, medium, hard, brutal)
        difficulty_level = self.lobby_settings['cpu_difficulty']
        star_spacing = 19  # Halved from 38
        start_x = center_x - 40  # Halved from 80
        star_names = ['easy', 'medium', 'hard', 'brutal']
        
        for i, star_name in enumerate(star_names):
            # Show filled star up to difficulty level, empty after
            if i <= difficulty_level:
                star_img = self.star_icons.get(star_name)
            else:
                star_img = self.star_icons.get('starEmpty')
            
            if star_img:
                # Scale star down slightly for better fit
                star_scaled = pygame.transform.scale(star_img, (18, 18))  # Halved from 36
                self.screen.blit(star_scaled, (start_x + i * star_spacing, y - 9))  # Halved from 18
        
        y += 18  # Compact spacing
        
        # Level selection (index 3)
        is_selected = (self.lobby_selection == 3)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "Level" label
        label = self.font_small.render("Level:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 50 + 1, y + 1))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("Level:", True, color)
        label_rect = label.get_rect(midright=(center_x - 50, y))
        self.screen.blit(label, label_rect)
        
        # Draw level number/name
        level_idx = self.lobby_settings.get('level', 0)
        if len(self.multiplayer_levels) > 0 and level_idx < len(self.multiplayer_levels):
            level_info = self.multiplayer_levels[level_idx]
            level_text = f"{level_info['number']:02d}"
        else:
            level_text = "01"
        
        level_label = self.font_small.render(level_text, True, BLACK)
        level_rect = level_label.get_rect(midleft=(center_x - 40 + 1, y + 1))
        self.screen.blit(level_label, level_rect)
        level_label = self.font_small.render(level_text, True, color)
        level_rect = level_label.get_rect(midleft=(center_x - 40, y))
        self.screen.blit(level_label, level_rect)
        
        # Draw small level preview to the right of level number (moved down to not overlap stars)
        preview = self.generate_level_preview(level_idx)
        if preview:
            # Scale down to small thumbnail
            small_preview = pygame.transform.scale(preview, (32, 32))
            self.screen.blit(small_preview, (center_x + 10, y - 10))
        
        y += 28  # More spacing after level for player slots
        
        # Player slots (starting at selection index 4)
        # Use hatchling heads with input icons
        head_size = 24  # Halved from 48 for 240x240 resolution
        for i in range(4):
            player_name = self.player_names[i]
            player_color = self.player_colors[i]
            slot_type = self.player_slots[i]
            
            is_selected = (self.lobby_selection == 4 + i)
            
            # Draw player hatchling head
            if self.snake_head_frames_all and len(self.snake_head_frames_all) > i:
                if self.snake_head_frames_all[i]:
                    head = self.snake_head_frames_all[i][0]  # First frame
                    head_scaled = pygame.transform.scale(head, (head_size, head_size))
                    
                    # Dim if OFF
                    if slot_type == 'off':
                        head_scaled = head_scaled.copy()
                        head_scaled.set_alpha(80)
                    
                    head_x = center_x - 65  # Halved from 130
                    head_y = y - head_size // 2
                    self.screen.blit(head_scaled, (head_x, head_y))
                    
                    # Draw selection indicator (thicker border)
                    if is_selected:
                        pygame.draw.rect(self.screen, NEON_YELLOW, 
                                       (head_x - 3, head_y - 3, head_size + 6, head_size + 6), 3)
            
            # Draw player name
            name_color = player_color if slot_type != 'off' else DARK_GRAY
            if is_selected:
                name_color = NEON_YELLOW
            
            text = self.font_small.render(player_name, True, BLACK)
            rect = text.get_rect(left=center_x - 25 + 1, centery=y + 1)
            self.screen.blit(text, rect)
            text = self.font_small.render(player_name, True, name_color)
            rect = text.get_rect(left=center_x - 25, centery=y)
            self.screen.blit(text, rect)
            
            # Draw input icon (keyboard/gamepad/robot/off)
            icon = None
            if slot_type == 'player':
                # For network games, connected players get gamepad icon
                if self.is_network_game:
                    # Host (player 0) or connected clients show gamepad icon
                    if i == 0 or (self.network_manager.is_host() and i < self.network_manager.get_connected_players()):
                        icon = self.gamepad_icon
                    elif self.network_manager.is_client() and i < self.num_players:
                        # Clients see gamepad icons for all active players
                        icon = self.gamepad_icon
                    else:
                        # Should be CPU if not connected
                        self.player_slots[i] = 'cpu'
                        icon = self.robot_icon
                else:
                    # Local multiplayer: check controllers
                    if i < len(self.player_controllers):
                        ctrl_type, ctrl_idx = self.player_controllers[i]
                        if ctrl_type == 'keyboard':
                            icon = self.keyboard_icon
                        else:
                            icon = self.gamepad_icon
                    else:
                        # No controller available - auto-switch to CPU
                        self.player_slots[i] = 'cpu'
                        icon = self.robot_icon
            elif slot_type == 'cpu':
                icon = self.robot_icon
            # else: slot_type == 'off', no icon
            
            if icon and slot_type != 'off':
                icon_x = center_x + 35  # Halved from 70
                icon_y = y - 9  # Halved from 18
                # Scale icon down to match other elements
                icon_scaled = pygame.transform.scale(icon, (18, 18))  # Halved from 36
                self.screen.blit(icon_scaled, (icon_x, icon_y))
            
            y += 26  # Reduced spacing between players
        
        # Simple hint at bottom - just START to begin
        hint = "START: Begin Game"
        if self.is_network_game and self.network_manager.is_client():
            hint = "Waiting for host..."
        
        text = self.font_small.render(hint, True, BLACK)
        rect = text.get_rect(center=((SCREEN_WIDTH // 2)+1, SCREEN_HEIGHT - 12))
        self.screen.blit(text, rect)
        text = self.font_small.render(hint, True, NEON_CYAN)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 13))
        self.screen.blit(text, rect)
    
    def draw_difficulty_select(self):
        # Draw difficulty screen image as background
        if self.difficulty_screen:
            self.screen.blit(self.difficulty_screen, (0, 0))
        elif self.title_screen:
            self.screen.blit(self.title_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Render title with more space from top
        title = self.font_large.render("SELECT DIFFICULTY", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 77))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("SELECT DIFFICULTY", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 75))
        self.screen.blit(title, title_rect)
        
        # Difficulty descriptions
        descriptions = [
            "Score multiplier: X 1/2",
            "Score multiplier: X 1",
            "Score multiplier: X 2"
        ]
        
        # Render difficulty options with better spacing
        start_y = 140  # Halved from 280
        spacing = 20  # Halved from 40
        
        for i, option in enumerate(self.difficulty_options):
            color = NEON_YELLOW if i == self.difficulty_selection else NEON_GREEN
            
            # draw shadow
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+3, start_y + i * spacing+2))
            self.screen.blit(text, text_rect)
            # Draw option text
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * spacing))
            
            # Draw selection box
            # if i == self.difficulty_selection:
            #     glow_rect = pygame.Rect(text_rect.left - 10, text_rect.top - 2, 
            #                            text_rect.width + 20, text_rect.height + 4)
            #     pygame.draw.rect(self.screen, NEON_PINK, glow_rect, 2)
            
            self.screen.blit(text, text_rect)

        # Draw description text based on difficulty selected
        desc_text = self.font_small.render(descriptions[self.difficulty_selection], True, BLACK)
        desc_rect = desc_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))  # Halved from 452
        self.screen.blit(desc_text, desc_rect)
        # Draw description text based on difficulty selected
        desc_text = self.font_small.render(descriptions[self.difficulty_selection], True, NEON_PURPLE)
        desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Halved from 450
        self.screen.blit(desc_text, desc_rect)


    
    def draw_egg_hatching_overlay(self):
        """Draw egg and instruction text overlay on top of the live game world"""
        # Draw egg at starting position (adventure mode) or center (endless mode)
        if self.egg_img:
            # Check if we have a boss egg respawn position (random position after death)
            if (hasattr(self, 'boss_egg_respawn_pos') and self.boss_egg_respawn_pos is not None and 
                hasattr(self, 'boss_egg_is_respawn') and self.boss_egg_is_respawn):
                egg_x, egg_y = self.boss_egg_respawn_pos
                # Center the 2x2 egg over the spawn point
                egg_pixel_x = egg_x * GRID_SIZE - GRID_SIZE // 2
                egg_pixel_y = egg_y * GRID_SIZE + GAME_OFFSET_Y - GRID_SIZE // 2
            elif self.game_mode == "adventure" and hasattr(self, 'current_level_data'):
                # Use level's starting position
                egg_x, egg_y = self.current_level_data['starting_position']
                # Center the 2x2 egg over the 1x1 spawn point
                egg_pixel_x = egg_x * GRID_SIZE - GRID_SIZE // 2
                egg_pixel_y = egg_y * GRID_SIZE + GAME_OFFSET_Y - GRID_SIZE // 2
            else:
                # Default to center for endless mode
                egg_pixel_x = SCREEN_WIDTH // 2 - GRID_SIZE
                egg_pixel_y = SCREEN_HEIGHT // 2 - GRID_SIZE
            self.screen.blit(self.egg_img, (egg_pixel_x, egg_pixel_y))
        
        # Draw instruction text (with timer if in boss mode respawn)
        instruction_text = "Press a direction to hatch!"
        if hasattr(self, 'boss_active') and self.boss_active and hasattr(self, 'boss_egg_is_respawn') and self.boss_egg_is_respawn:
            # Show countdown timer (5 seconds = 300 frames)
            time_left = max(0, (300 - getattr(self, 'egg_timer', 0)) // 60)
            instruction_text = "Choose direction! Auto-hatch in {}s".format(time_left)
        
        instruction = self.font_medium.render(instruction_text, True, BLACK)
        instruction_rect = instruction.get_rect(center=((SCREEN_WIDTH // 2)+2, SCREEN_HEIGHT - 19))
        self.screen.blit(instruction, instruction_rect)
        instruction = self.font_medium.render(instruction_text, True, NEON_YELLOW)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        self.screen.blit(instruction, instruction_rect)
    
    def draw_snake(self, snake, player_id):
        """Draw a single snake with its color-shifted graphics."""
        # Get interpolated positions for smooth movement
        is_boss_minion = hasattr(snake, 'is_boss_minion') and snake.is_boss_minion
        is_enemy_snake = hasattr(snake, 'is_enemy_snake') and snake.is_enemy_snake
        
        # Calculate progress between frames for smooth per-frame interpolation
        if self.is_multiplayer or is_boss_minion or is_enemy_snake:
            # Use snake's individual timer and interval (for multiplayer, boss minions, or enemy snakes)
            move_interval = max(1, snake.last_move_interval)
            progress = min(1.0, snake.move_timer / move_interval)
        else:
            # Single player - use global timer and calculate speed same as movement logic
            if self.game_mode == "adventure":
                # Fixed speed in adventure mode (doesn't increase with level)
                move_interval = 16
            else:
                # Endless mode - speed increases with level
                move_interval = max(1, 16 - self.level // 2)
            progress = min(1.0, self.move_timer / move_interval)
        
        interpolated_positions = []
        for i, current_pos in enumerate(snake.body):
            if i < len(snake.previous_body):
                previous_pos = snake.previous_body[i]
            else:
                previous_pos = current_pos
            
            # Handle wrapping - detect if snake wrapped around screen edges
            dx = current_pos[0] - previous_pos[0]
            dy = current_pos[1] - previous_pos[1]
            
            # Adjust for wrapping (if difference is too large, it wrapped)
            if abs(dx) > GRID_WIDTH // 2:
                if dx > 0:
                    previous_pos = (previous_pos[0] + GRID_WIDTH, previous_pos[1])
                else:
                    previous_pos = (previous_pos[0] - GRID_WIDTH, previous_pos[1])
            
            if abs(dy) > GRID_HEIGHT // 2:
                if dy > 0:
                    previous_pos = (previous_pos[0], previous_pos[1] + GRID_HEIGHT)
                else:
                    previous_pos = (previous_pos[0], previous_pos[1] - GRID_HEIGHT)
            
            # Linear interpolation
            interp_x = previous_pos[0] + (current_pos[0] - previous_pos[0]) * progress
            interp_y = previous_pos[1] + (current_pos[1] - previous_pos[1]) * progress
            interpolated_positions.append((interp_x, interp_y))
        
        # Get player-specific graphics
        # Check if this is a boss minion or enemy snake
        is_boss_minion = hasattr(snake, 'is_boss_minion') and snake.is_boss_minion
        is_enemy_snake = hasattr(snake, 'is_enemy_snake') and snake.is_enemy_snake
        
        if is_boss_minion:
            # Use bad snake graphics for boss minions
            body_img = self.bad_snake_body_img
            head_img_static = self.bad_snake_head_img  # Static image for minions
            head_frames = None
        elif is_enemy_snake:
            # Use enemy snake graphics for enemy snakes
            body_img = self.enemy_snake_body_img
            head_img_static = self.enemy_snake_head_img  # Static image for enemy snakes
            head_frames = None
        elif player_id < len(self.player_graphics):
            body_img, head_frames = self.player_graphics[player_id]
            head_img_static = None
        else:
            body_img = self.snake_body_img
            head_frames = self.snake_head_frames
            head_img_static = None
        
        # Create a list of (index, x, y) tuples and sort by y-coordinate for proper z-ordering
        segments_with_indices = [(i, x, y) for i, (x, y) in enumerate(interpolated_positions)]
        segments_with_indices.sort(key=lambda seg: seg[2])  # Sort by y coordinate
        
        # Check if snake has shooting ability for pulsing effect
        has_isotope_ability = hasattr(snake, 'can_shoot') and snake.can_shoot
        
        for i, x, y in segments_with_indices:
            # Convert interpolated grid coordinates to pixel coordinates
            pixel_x = x * GRID_SIZE + self.snake_offset
            pixel_y = y * GRID_SIZE + self.snake_offset + GAME_OFFSET_Y
            
            if i == 0:
                # Draw head with animation or static image
                if head_img_static:
                    # Boss minion - use static bad snake head
                    dx, dy = snake.direction.value
                    if dx == 1:  # Right
                        rotated_head = pygame.transform.rotate(head_img_static, -90)
                    elif dx == -1:  # Left
                        rotated_head = pygame.transform.rotate(head_img_static, 90)
                    elif dy == -1:  # Up
                        rotated_head = head_img_static
                    else:  # Down
                        rotated_head = pygame.transform.rotate(head_img_static, 180)
                    
                    self.screen.blit(rotated_head, (int(pixel_x), int(pixel_y)))
                elif head_frames:
                    # Regular player - use animated head
                    head_img = head_frames[self.head_frame_index]
                    # Rotate head based on direction
                    dx, dy = snake.direction.value
                    if dx == 1:  # Right
                        rotated_head = pygame.transform.rotate(head_img, 90)
                    elif dx == -1:  # Left
                        rotated_head = pygame.transform.rotate(head_img, -90)
                    elif dy == -1:  # Up
                        rotated_head = pygame.transform.rotate(head_img, 180)
                    else:  # Down
                        rotated_head = head_img
                    
                    self.screen.blit(rotated_head, (int(pixel_x), int(pixel_y)))
                else:
                    # Fallback to drawing head with eyes
                    color = self.player_colors[player_id] if player_id < len(self.player_colors) else NEON_GREEN
                    rect = pygame.Rect(int(pixel_x), int(pixel_y), GRID_SIZE - 2, GRID_SIZE - 2)
                    pygame.draw.rect(self.screen, color, rect, border_radius=2)
                    
                    dx, dy = snake.direction.value
                    if dx == 1:
                        eye1 = (int(pixel_x + GRID_SIZE - 5), int(pixel_y + 3))
                        eye2 = (int(pixel_x + GRID_SIZE - 5), int(pixel_y + GRID_SIZE - 5))
                    elif dx == -1:
                        eye1 = (int(pixel_x + 3), int(pixel_y + 3))
                        eye2 = (int(pixel_x + 3), int(pixel_y + GRID_SIZE - 5))
                    elif dy == -1:
                        eye1 = (int(pixel_x + 3), int(pixel_y + 3))
                        eye2 = (int(pixel_x + GRID_SIZE - 5), int(pixel_y + 3))
                    else:
                        eye1 = (int(pixel_x + 3), int(pixel_y + GRID_SIZE - 5))
                        eye2 = (int(pixel_x + GRID_SIZE - 5), int(pixel_y + GRID_SIZE - 5))
                    
                    pygame.draw.circle(self.screen, NEON_CYAN, eye1, 2)
                    pygame.draw.circle(self.screen, NEON_CYAN, eye2, 2)
            else:
                # Draw body segments
                # Use glowing body image if snake has isotope ability in adventure mode
                current_body_img = body_img
                if has_isotope_ability and self.game_mode == 'adventure' and self.snake_body_glow_img:
                    current_body_img = self.snake_body_glow_img
                
                if current_body_img:
                    self.screen.blit(current_body_img, (int(pixel_x), int(pixel_y)))
                else:
                    # Fallback to gradient rendering with player color
                    color = self.player_colors[player_id] if player_id < len(self.player_colors) else NEON_GREEN
                    ratio = i / max(len(snake.body) - 1, 1)
                    darker_color = tuple(int(c * 0.7) for c in color)
                    final_color = tuple(
                        int(darker_color[j] + (color[j] - darker_color[j]) * ratio)
                        for j in range(3)
                    )
                    
                    rect = pygame.Rect(int(pixel_x), int(pixel_y), GRID_SIZE - 2, GRID_SIZE - 2)
                    pygame.draw.rect(self.screen, final_color, rect, border_radius=2)
    
    def draw_game(self):
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # # Draw grid with subtle neon glow
        # for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        #     pygame.draw.line(self.screen, GRID_COLOR, (x, GAME_OFFSET_Y), (x, SCREEN_HEIGHT), 1)
        # for y in range(GAME_OFFSET_Y, SCREEN_HEIGHT, GRID_SIZE):
        #     pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
        
        # Draw food
        if self.is_multiplayer:
            # Draw all food items in multiplayer
            for food_pos, food_type in self.food_items:
                fx, fy = food_pos
                
                if food_type == 'worm':
                    # Draw worm (animated if available)
                    if self.worm_frames:
                        worm_img = self.worm_frames[self.worm_frame_index]
                        self.screen.blit(worm_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                    else:
                        # Fallback to red rectangle
                        food_rect = pygame.Rect(fx * GRID_SIZE + 2, fy * GRID_SIZE + 2 + GAME_OFFSET_Y,
                                               GRID_SIZE - 4, GRID_SIZE - 4)
                        pygame.draw.rect(self.screen, (255, 0, 0), food_rect, border_radius=GRID_SIZE // 4)
                
                elif food_type == 'apple':
                    # Draw speed boost apple (bonus.png)
                    if self.bonus_img:
                        self.screen.blit(self.bonus_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                    else:
                        # Fallback to circle
                        center_x = fx * GRID_SIZE + GRID_SIZE // 2
                        center_y = fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                        pygame.draw.circle(self.screen, (200, 30, 30), (center_x, center_y), GRID_SIZE // 3)
                        pygame.draw.circle(self.screen, (255, 100, 100), (center_x - 2, center_y - 2), GRID_SIZE // 6)
                
                elif food_type == 'black_apple':
                    # Draw bad apple (badApple.png)
                    if self.bad_apple_img:
                        self.screen.blit(self.bad_apple_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                    else:
                        # Fallback to circle
                        center_x = fx * GRID_SIZE + GRID_SIZE // 2
                        center_y = fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                        pygame.draw.circle(self.screen, (40, 20, 50), (center_x, center_y), GRID_SIZE // 3)
                        pygame.draw.circle(self.screen, (80, 50, 90), (center_x - 2, center_y - 2), GRID_SIZE // 6)
        else:
            # Single player - draw regular food with animated worm (Endless mode only)
            if self.game_mode == "endless" and self.food_pos:
                fx, fy = self.food_pos
                if self.worm_frames:
                    # Draw animated worm
                    worm_img = self.worm_frames[self.worm_frame_index]
                    self.screen.blit(worm_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                else:
                    # Fallback to pulsing red rectangle
                    pulse = abs((pygame.time.get_ticks() % 1000) - 500) / 500  # 0 to 1 and back
                    size_offset = int(pulse * 2)  # Pulse between 0 and 2 pixels
                    
                    food_rect = pygame.Rect(fx * GRID_SIZE + 2 - size_offset, 
                                           fy * GRID_SIZE + 2 - size_offset + GAME_OFFSET_Y,
                                           GRID_SIZE - 4 + size_offset * 2, 
                                           GRID_SIZE - 4 + size_offset * 2)
                    # Use pure red color (255, 0, 0) instead of NEON_PINK
                    pygame.draw.rect(self.screen, (255, 0, 0), food_rect, border_radius=GRID_SIZE // 4)
        
        # Draw walls in Adventure mode
        if self.game_mode == "adventure" and self.level_walls:
            for wx, wy in self.level_walls:
                if self.wall_img:
                    self.screen.blit(self.wall_img, (wx * GRID_SIZE, wy * GRID_SIZE + GAME_OFFSET_Y))
                else:
                    # Fallback to colored rectangles
                    wall_rect = pygame.Rect(wx * GRID_SIZE, wy * GRID_SIZE + GAME_OFFSET_Y, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(self.screen, NEON_PURPLE, wall_rect)
                    pygame.draw.rect(self.screen, (100, 50, 150), wall_rect, 2)
        
        # Draw walls in Multiplayer mode
        if self.is_multiplayer and self.walls:
            for wx, wy in self.walls:
                if self.wall_img:
                    self.screen.blit(self.wall_img, (wx * GRID_SIZE, wy * GRID_SIZE + GAME_OFFSET_Y))
                else:
                    # Fallback to colored rectangles
                    wall_rect = pygame.Rect(wx * GRID_SIZE, wy * GRID_SIZE + GAME_OFFSET_Y, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(self.screen, NEON_CYAN, wall_rect)
                    pygame.draw.rect(self.screen, NEON_BLUE, wall_rect, 2)
        
        # Draw worms and bonus fruits in Adventure mode (from food_items list)
        if self.game_mode == "adventure" and self.food_items:
            for food_pos, food_type in self.food_items:
                fx, fy = food_pos
                if food_type == 'worm':
                    if self.worm_frames:
                        worm_img = self.worm_frames[self.worm_frame_index]
                        self.screen.blit(worm_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                    else:
                        food_rect = pygame.Rect(fx * GRID_SIZE + 2, fy * GRID_SIZE + 2 + GAME_OFFSET_Y,
                                               GRID_SIZE - 4, GRID_SIZE - 4)
                        pygame.draw.rect(self.screen, (255, 0, 0), food_rect, border_radius=GRID_SIZE // 4)
                elif food_type == 'bonus':
                    if self.bonus_img:
                        self.screen.blit(self.bonus_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                    else:
                        # Fallback to yellow circle
                        pygame.draw.circle(self.screen, NEON_YELLOW, 
                                         (fx * GRID_SIZE + GRID_SIZE // 2, fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y),
                                         GRID_SIZE // 3)
                elif food_type == 'coin':
                    # Draw coin as a golden circle
                    center_x = fx * GRID_SIZE + GRID_SIZE // 2
                    center_y = fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                    pygame.draw.circle(self.screen, YELLOW, (center_x, center_y), GRID_SIZE // 4)
                    pygame.draw.circle(self.screen, (255, 165, 0), (center_x, center_y), GRID_SIZE // 4, 2)
                    # Add inner circle for detail
                    pygame.draw.circle(self.screen, (255, 165, 0), (center_x, center_y), GRID_SIZE // 6, 2)
                elif food_type == 'diamond':
                    # Draw diamond as a cyan diamond shape
                    center_x = fx * GRID_SIZE + GRID_SIZE // 2
                    center_y = fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                    size = GRID_SIZE // 3
                    points = [
                        (center_x, center_y - size),  # Top
                        (center_x + size, center_y),  # Right
                        (center_x, center_y + size),  # Bottom
                        (center_x - size, center_y)   # Left
                    ]
                    pygame.draw.polygon(self.screen, NEON_CYAN, points)
                    pygame.draw.polygon(self.screen, (0, 0, 255), points, 2)
                    # Add inner diamond for sparkle
                    inner_size = size // 2
                    inner_points = [
                        (center_x, center_y - inner_size),
                        (center_x + inner_size, center_y),
                        (center_x, center_y + inner_size),
                        (center_x - inner_size, center_y)
                    ]
                    pygame.draw.polygon(self.screen, WHITE, inner_points, 1)
                elif food_type == 'isotope':
                    # Draw isotope image
                    if self.isotope_img:
                        self.screen.blit(self.isotope_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                    else:
                        # Fallback to rendered graphic
                        center_x = fx * GRID_SIZE + GRID_SIZE // 2
                        center_y = fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                        # Draw nucleus (central circle)
                        pygame.draw.circle(self.screen, NEON_PURPLE, (center_x, center_y), GRID_SIZE // 6)
                        pygame.draw.circle(self.screen, WHITE, (center_x, center_y), GRID_SIZE // 6, 2)
                        # Draw orbiting electrons (3 circles)
                        import math
                        radius = GRID_SIZE // 3
                        for i in range(3):
                            angle = (self.move_timer * 3 + i * 120) % 360  # Rotating animation
                            electron_x = center_x + int(radius * math.cos(math.radians(angle)))
                            electron_y = center_y + int(radius * math.sin(math.radians(angle)))
                            pygame.draw.circle(self.screen, NEON_CYAN, (electron_x, electron_y), 3)
        
        # Draw bullets
        for bullet in self.bullets:
            # Draw bullet as a glowing projectile
            bullet_x = int(bullet.pixel_x + GRID_SIZE // 2)
            bullet_y = int(bullet.pixel_y + GRID_SIZE // 2 + GAME_OFFSET_Y)
            # Draw outer glow
            pygame.draw.circle(self.screen, NEON_YELLOW, (bullet_x, bullet_y), 6)
            # Draw inner bright core
            pygame.draw.circle(self.screen, WHITE, (bullet_x, bullet_y), 3)
        
        # Draw scorpion stingers
        for stinger in self.scorpion_stingers:
            stinger.draw(self.screen, GAME_OFFSET_Y)
        
        # Draw beetle larvae
        for larvae in self.beetle_larvae:
            larvae.draw(self.screen, GAME_OFFSET_Y)
        
        # Draw spewtum projectiles
        for spewtum in self.spewtums:
            spewtum.draw(self.screen, GAME_OFFSET_Y)
        
        # Draw enemies in Adventure mode during PLAYING state
        if self.game_mode == "adventure" and hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.alive:
                    render_x, render_y = enemy.get_render_position()
                    
                    # Skip wasps here - they're drawn on top later
                    if enemy.enemy_type.startswith('enemy_wasp'):
                        continue
                    
                    # Draw enemies (ants, spiders, wasps, walls)
                    if enemy.enemy_type == 'enemy_wall':
                        # Draw enemy wall with visual indicator of health
                        wall_x = enemy.grid_x * GRID_SIZE
                        wall_y = enemy.grid_y * GRID_SIZE + GAME_OFFSET_Y
                        
                        if self.wall_img:
                            # Draw the wall image
                            self.screen.blit(self.wall_img, (wall_x, wall_y))
                            
                            # Add health indicator - draw small dots to show remaining health
                            health_color = RED if enemy.health == 1 else YELLOW if enemy.health == 2 else GREEN
                            for i in range(enemy.health):
                                dot_x = wall_x + 2 + i * 4
                                dot_y = wall_y + 2
                                pygame.draw.circle(self.screen, health_color, (dot_x, dot_y), 2)
                        else:
                            # Fallback: draw colored rectangle
                            health_color = RED if enemy.health == 1 else YELLOW if enemy.health == 2 else GREEN
                            pygame.draw.rect(self.screen, health_color, 
                                           (wall_x, wall_y, GRID_SIZE, GRID_SIZE))
                    else:
                        # Draw enemy using sprite if available
                        enemy_frames = None
                        is_scorpion = False
                        if enemy.enemy_type.startswith('enemy_ant') and self.ant_frames:
                            enemy_frames = self.ant_frames
                        elif enemy.enemy_type.startswith('enemy_spider') and self.spider_frames:
                            enemy_frames = self.spider_frames
                        elif enemy.enemy_type.startswith('enemy_scorpion') and self.scorpion_frames:
                            # Scorpion is 2x2 grid (64x64 pixels), use attack animation if attacking
                            if enemy.is_attacking:
                                enemy_frames = self.scorpion_frames  # Can switch to attack frames later if desired
                            else:
                                enemy_frames = self.scorpion_frames
                            is_scorpion = True
                        elif enemy.enemy_type.startswith('enemy_beetle'):
                            # Beetle uses different animations based on state
                            if enemy.is_attacking and self.beetle_attack_frames:
                                # Use attack animation when launching larvae
                                enemy_frames = self.beetle_attack_frames
                            elif enemy.is_attacking and enemy.attack_charge_time > 30 and self.beetle_open_frames:
                                # Use vulnerable/open animation after launching larvae
                                enemy_frames = self.beetle_open_frames
                            elif self.beetle_frames:
                                # Normal idle animation
                                enemy_frames = self.beetle_frames
                        
                        if enemy_frames:
                            enemy_img = enemy_frames[enemy.animation_frame]
                            # Rotate sprite to match direction (angle: 0=right, 90=down, 180=left, 270=up)
                            # pygame.transform.rotate rotates counter-clockwise, so negate the angle
                            rotated_img = pygame.transform.rotate(enemy_img, -enemy.angle)
                            
                            # Get rect to center the rotated image on the grid position
                            # Scorpions are 2x2 grid (64x64), so center at (x+1, y+1)
                            if is_scorpion:
                                img_rect = rotated_img.get_rect(center=(int(render_x * GRID_SIZE + GRID_SIZE), 
                                                                         int(render_y * GRID_SIZE + GRID_SIZE + GAME_OFFSET_Y)))
                            else:
                                img_rect = rotated_img.get_rect(center=(int(render_x * GRID_SIZE + GRID_SIZE // 2), 
                                                                         int(render_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y)))
                            self.screen.blit(rotated_img, img_rect)
                        else:
                            # Fallback to circle rendering if no sprite
                            center_x = int(render_x * GRID_SIZE + GRID_SIZE // 2)
                            center_y = int(render_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y)
                            radius = GRID_SIZE // 3
                            
                            # Get color based on enemy type
                            if enemy.enemy_type.startswith('enemy_spider'):
                                enemy_color = (139, 69, 19)  # Brown for spiders
                            else:
                                enemy_color = (165, 42, 42)  # Default ant brown
                            
                            # Draw enemy body
                            pygame.draw.circle(self.screen, enemy_color, (center_x, center_y), radius)
                            pygame.draw.circle(self.screen, BLACK, (center_x, center_y), radius, 2)
                            
                            # Draw angry face
                            eye_offset = radius // 3
                            eye_size = 3
                            pygame.draw.circle(self.screen, BLACK, (center_x - eye_offset, center_y - eye_offset), eye_size)
                            pygame.draw.circle(self.screen, BLACK, (center_x + eye_offset, center_y - eye_offset), eye_size)
                            pygame.draw.line(self.screen, BLACK, 
                                           (center_x - eye_offset, center_y + eye_offset),
                                           (center_x + eye_offset, center_y + eye_offset), 2)
        
        # Draw bonus food
        if self.bonus_food_pos:
            bx, by = self.bonus_food_pos
            if self.bonus_img:
                # Draw bonus image
                self.screen.blit(self.bonus_img, (bx * GRID_SIZE, by * GRID_SIZE + GAME_OFFSET_Y))
            else:
                # Fallback to pulsing yellow circle
                pulse = abs((self.bonus_food_timer % 60) - 30) / 30
                size = int(GRID_SIZE // 2 + pulse * 2)
                center_x = bx * GRID_SIZE + GRID_SIZE // 2
                center_y = by * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                pygame.draw.circle(self.screen, NEON_YELLOW, (center_x, center_y), size)
        
        # Draw respawn eggs in multiplayer
        if self.is_multiplayer:
            for player_id, egg_data in self.respawning_players.items():
                ex, ey = egg_data['pos']
                pixel_x = ex * GRID_SIZE
                pixel_y = ey * GRID_SIZE + GAME_OFFSET_Y
                
                # Get player color directly
                egg_color = self.player_colors[player_id] if player_id < len(self.player_colors) else NEON_CYAN
                
                # Draw egg using player-specific graphics
                if player_id < len(self.player_egg_imgs) and self.player_egg_imgs[player_id]:
                    # Center the 2x2 egg image on the grid cell
                    egg_img = self.player_egg_imgs[player_id]
                    egg_x = pixel_x - GRID_SIZE // 2
                    egg_y = pixel_y - GRID_SIZE // 2
                    self.screen.blit(egg_img, (egg_x, egg_y))
                else:
                    # Fallback to colored ellipse
                    pulse = abs((pygame.time.get_ticks() % 1000) - 500) / 500
                    size = int(GRID_SIZE * 0.4 + pulse * 3)
                    pygame.draw.ellipse(self.screen, egg_color, 
                                       pygame.Rect(pixel_x + (GRID_SIZE - size) // 2,
                                                 pixel_y + (GRID_SIZE - size) // 2,
                                                 size, size))
                
                # Draw timer below egg
                seconds_left = max(0, egg_data['timer'] // 60 + 1)
                timer_text = self.font_small.render(str(seconds_left), True, BLACK)
                timer_rect = timer_text.get_rect(center=(pixel_x + GRID_SIZE // 2 + 2, pixel_y + GRID_SIZE + 8))
                self.screen.blit(timer_text, timer_rect)
                timer_text = self.font_small.render(str(seconds_left), True, egg_color)
                timer_rect = timer_text.get_rect(center=(pixel_x + GRID_SIZE // 2, pixel_y + GRID_SIZE + 6))
                self.screen.blit(timer_text, timer_rect)
        
        # Draw boss minions FIRST (so they render behind the boss)
        if self.boss_minions:
            for minion in self.boss_minions:
                if minion.alive:
                    # Use draw_snake for smooth interpolation
                    self.draw_snake(minion, minion.player_id)
        
        # Draw enemy snakes (non-boss)
        if self.enemy_snakes:
            for enemy_snake in self.enemy_snakes:
                if enemy_snake.alive:
                    # Use draw_snake for smooth interpolation
                    self.draw_snake(enemy_snake, enemy_snake.player_id)
        
        # Draw Frog Boss if active
        if self.boss_active and self.boss_data == 'frog' and self.boss_spawned:
            # Draw shadow (visible during airborne and falling states)
            if self.frog_state in ['airborne', 'falling', 'jumping']:
                shadow_x = int(self.frog_shadow_position[0] * GRID_SIZE)
                shadow_y = int(self.frog_shadow_position[1] * GRID_SIZE + GAME_OFFSET_Y)
                # Draw semi-transparent dark circle for shadow (4x4 to match frog size)
                shadow_surface = pygame.Surface((GRID_SIZE * 4, GRID_SIZE * 4), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surface, (0, 0, 0, 100), shadow_surface.get_rect())
                self.screen.blit(shadow_surface, (shadow_x, shadow_y))
            
            # Draw frog (when not fully off-screen)
            if self.frog_state in ['falling', 'landed', 'jumping'] and self.frog_boss_img:
                frog_pixel_x = int(self.frog_position[0] * GRID_SIZE)
                frog_pixel_y = int(self.frog_position[1] * GRID_SIZE + GAME_OFFSET_Y)
                
                # Rotate frog sprite to face tongue direction
                rotated_frog = pygame.transform.rotate(self.frog_boss_img, -self.frog_rotation_angle)
                # Get rect for centered rotation (frog is 4x4 = 128 pixels, center at +64)
                rotated_rect = rotated_frog.get_rect(center=(frog_pixel_x + GRID_SIZE * 2, frog_pixel_y + GRID_SIZE * 2))
                
                # Apply red flash if damaged
                if self.boss_damage_flash > 0 and not self.boss_defeated:
                    red_overlay = pygame.Surface(rotated_frog.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 128))
                    rotated_frog.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.screen.blit(rotated_frog, rotated_rect)
            
            # Draw tongue segments
            if len(self.frog_tongue_segments) > 0 and self.frog_tongue_img:
                for segment_pos in self.frog_tongue_segments:
                    seg_x = int(segment_pos[0] * GRID_SIZE)
                    seg_y = int(segment_pos[1] * GRID_SIZE + GAME_OFFSET_Y)
                    self.screen.blit(self.frog_tongue_img, (seg_x, seg_y))
            
            # Draw frog boss top layer (renders above tongue)
            if self.frog_state in ['falling', 'landed', 'jumping'] and self.frog_boss_top_img:
                frog_pixel_x = int(self.frog_position[0] * GRID_SIZE)
                frog_pixel_y = int(self.frog_position[1] * GRID_SIZE + GAME_OFFSET_Y)
                
                # Rotate top layer to match frog sprite rotation
                rotated_top = pygame.transform.rotate(self.frog_boss_top_img, -self.frog_rotation_angle)
                # Get rect for centered rotation (same as main frog sprite)
                rotated_rect = rotated_top.get_rect(center=(frog_pixel_x + GRID_SIZE * 2, frog_pixel_y + GRID_SIZE * 2))
                
                # Apply red flash if damaged (same as main frog sprite)
                if self.boss_damage_flash > 0 and not self.boss_defeated:
                    red_overlay = pygame.Surface(rotated_top.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 128))
                    rotated_top.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.screen.blit(rotated_top, rotated_rect)
        
        # Draw boss on top of minions (even when defeated, for death animation)
        if self.boss_spawned and self.boss_current_animation and self.boss_data == 'wormBoss':
            anim_frames = self.boss_animations.get(self.boss_current_animation, [])
            if anim_frames:
                # Clamp frame index to valid range
                frame_index = min(self.boss_animation_frame, len(anim_frames) - 1)
                boss_frame = anim_frames[frame_index]
                
                # Calculate render position (apply slide offset during death phase 2)
                render_x = self.boss_position[0]
                render_y = self.boss_position[1]
                if self.boss_defeated and self.boss_death_phase == 2:
                    render_y += self.boss_slide_offset_y
                
                # Apply red flash if boss was recently damaged (not during death)
                if self.boss_damage_flash > 0 and not self.boss_defeated:
                    # Create a copy of the frame with red tint
                    flash_frame = boss_frame.copy()
                    # Create a red overlay surface
                    red_overlay = pygame.Surface(flash_frame.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 128))  # Semi-transparent red
                    flash_frame.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.screen.blit(flash_frame, (render_x, render_y))
                else:
                    self.screen.blit(boss_frame, (render_x, render_y))
        
        # Draw boss health bar (top-right corner) - for ALL boss types
        # Hidden during egg hatching and final death phase
        if self.boss_active and self.boss_spawned:
            show_health_bar = self.state != GameState.EGG_HATCHING
            if self.boss_defeated and self.boss_death_phase >= 2:
                show_health_bar = False  # Hide during slide and completion phases
            
            if hasattr(self, 'boss_health') and hasattr(self, 'boss_max_health') and show_health_bar:
                # Health bar dimensions and position
                bar_width = 100  # Halved from 200
                bar_height = 10  # Halved from 20
                bar_x = SCREEN_WIDTH - bar_width - 5  # Halved from 10
                bar_y = 5  # Halved from 10
                
                # Background (dark gray)
                bg_rect = pygame.Rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4)
                pygame.draw.rect(self.screen, DARK_GRAY, bg_rect)
                pygame.draw.rect(self.screen, BLACK, bg_rect, 2)
                
                # Health bar fill (changes color based on health percentage)
                health_percent = max(0, self.boss_health / self.boss_max_health)
                fill_width = int(bar_width * health_percent)
                
                # Color changes: green -> yellow -> red
                if health_percent > 0.5:
                    bar_color = GREEN
                elif health_percent > 0.25:
                    bar_color = YELLOW
                else:
                    bar_color = RED
                
                if fill_width > 0:
                    fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
                    pygame.draw.rect(self.screen, bar_color, fill_rect)
                
                # Health bar outline
                outline_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
                pygame.draw.rect(self.screen, WHITE, outline_rect, 2)
                
                # Boss health text
                health_text = self.font_small.render("BOSS: {}/{}".format(max(0, self.boss_health), self.boss_max_health), True, WHITE)
                text_rect = health_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
                # Draw text shadow
                shadow_text = self.font_small.render("BOSS: {}/{}".format(max(0, self.boss_health), self.boss_max_health), True, BLACK)
                shadow_rect = shadow_text.get_rect(center=(bar_x + bar_width // 2 + 1, bar_y + bar_height // 2 + 1))
                self.screen.blit(shadow_text, shadow_rect)
                self.screen.blit(health_text, text_rect)
        
        # Draw snakes
        if self.is_multiplayer:
            # Draw all snakes with their individual colors
            for snake in self.snakes:
                if not snake.alive:
                    continue
                
                self.draw_snake(snake, snake.player_id)
        else:
            # Single player - draw the main snake (but not during initial egg hatching)
            # Don't draw snake at start of level when egg hasn't hatched yet
            if self.state != GameState.EGG_HATCHING or len(self.snake.body) > 1:
                self.draw_snake(self.snake, 0)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw egg pieces (if any are still flying)
        for piece in self.egg_pieces:
            piece.draw(self.screen)
        
        # Draw wasps on top of everything (they fly over the snake)
        if self.game_mode == "adventure" and hasattr(self, 'enemies'):
            for enemy in self.enemies:
                if enemy.alive and enemy.enemy_type.startswith('enemy_wasp'):
                    render_x, render_y = enemy.get_render_position()
                    
                    # Draw wasp using sprite if available
                    if self.wasp_frames:
                        wasp_img = self.wasp_frames[enemy.animation_frame]
                        # Rotate sprite to match direction
                        rotated_img = pygame.transform.rotate(wasp_img, -enemy.angle)
                        # Get rect to center the rotated image on the grid position
                        img_rect = rotated_img.get_rect(center=(int(render_x * GRID_SIZE + GRID_SIZE // 2), 
                                                                 int(render_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y)))
                        self.screen.blit(rotated_img, img_rect)
                    else:
                        # Fallback to circle rendering if no sprite
                        center_x = int(render_x * GRID_SIZE + GRID_SIZE // 2)
                        center_y = int(render_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y)
                        radius = GRID_SIZE // 3
                        
                        # Yellow color for wasps
                        enemy_color = (255, 215, 0)
                        
                        # Draw enemy body
                        pygame.draw.circle(self.screen, enemy_color, (center_x, center_y), radius)
                        pygame.draw.circle(self.screen, BLACK, (center_x, center_y), radius, 2)
                        
                        # Draw angry face
                        eye_offset = radius // 3
                        eye_size = 3
                        pygame.draw.circle(self.screen, BLACK, (center_x - eye_offset, center_y - eye_offset), eye_size)
                        pygame.draw.circle(self.screen, BLACK, (center_x + eye_offset, center_y - eye_offset), eye_size)
                        pygame.draw.line(self.screen, BLACK, 
                                       (center_x - eye_offset, center_y + eye_offset),
                                       (center_x + eye_offset, center_y + eye_offset), 2)
        
        # Draw HUD text (background now part of bg.png)
        if self.is_multiplayer:
            # Draw multiplayer player info in corners: P1 🥚: 10
            # P1: top-left, P2: top-right, P3: bottom-left, P4: bottom-right
            for snake in self.snakes:
                player_color = self.player_colors[snake.player_id] if snake.player_id < len(self.player_colors) else WHITE
                
                # Determine position based on player ID
                if snake.player_id == 0:  # P1: top-left
                    x_pos = 2
                    y_pos = 1
                elif snake.player_id == 1:  # P2: top-right
                    x_pos = SCREEN_WIDTH - 80  # Right-aligned, adjusted for larger font
                    y_pos = 1
                elif snake.player_id == 2:  # P3: bottom-left
                    x_pos = 2
                    y_pos = SCREEN_HEIGHT - 20  # Adjusted for larger font
                else:  # P4: bottom-right
                    x_pos = SCREEN_WIDTH - 80
                    y_pos = SCREEN_HEIGHT - 20  # Adjusted for larger font
                
                # Player name (e.g., "P1")
                player_text = "P{}".format(snake.player_id + 1)
                
                # Shadow
                text = self.font_medium.render(player_text, True, BLACK)
                self.screen.blit(text, (x_pos + 1, y_pos + 1))
                # Main text with player color
                text = self.font_medium.render(player_text, True, player_color)
                self.screen.blit(text, (x_pos, y_pos))
                
                # Draw single egg icon (slightly larger to match font)
                text_width = text.get_width()
                egg_x = x_pos + text_width + 3
                egg_icon = self.player_egg_icons[snake.player_id] if snake.player_id < len(self.player_egg_icons) else None
                
                if egg_icon:
                    # Scale egg slightly larger to match bigger font
                    egg_scaled = pygame.transform.scale(egg_icon, (18, 18))
                    self.screen.blit(egg_scaled, (egg_x, y_pos))
                    
                    # Lives count after colon
                    count_x = egg_x + 18 + 2
                    if snake.lives > 0:
                        lives_text = ": {}".format(snake.lives)
                        # Shadow
                        lives_shadow = self.font_medium.render(lives_text, True, BLACK)
                        self.screen.blit(lives_shadow, (count_x + 1, y_pos + 1))
                        # Main text
                        lives_label = self.font_medium.render(lives_text, True, player_color)
                        self.screen.blit(lives_label, (count_x, y_pos))
                    else:
                        # Draw X for eliminated players
                        x_text = self.font_medium.render(": X", True, BLACK)
                        self.screen.blit(x_text, (count_x + 1, y_pos + 1))
                        x_text = self.font_medium.render(": X", True, RED)
                        self.screen.blit(x_text, (count_x, y_pos))
        else:
            # Single player score - Left side: Score with label (hidden during boss battles)
            if not (hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned):
                score_label = self.font_small.render("SCORE:", True, BLACK)
                self.screen.blit(score_label, (5, 4))
                score_label = self.font_small.render("SCORE:", True, NEON_YELLOW)
                self.screen.blit(score_label, (4, 3))
                score_value = self.font_small.render("{}".format(self.score), True, BLACK)
                self.screen.blit(score_value, (50, 4))
                score_value = self.font_small.render("{}".format(self.score), True, WHITE)
                self.screen.blit(score_value, (49, 3))
        
        # Single player HUD elements (level, worms counter) - hidden during boss battles
        if not self.is_multiplayer and not (hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned):
            # Bottom right: Level
            level_value_text = "{}".format(self.level)
            level_value = self.font_small.render(level_value_text, True, BLACK)
            level_value_rect = level_value.get_rect(right=SCREEN_WIDTH - 4, bottom=SCREEN_HEIGHT )
            self.screen.blit(level_value, level_value_rect)
            level_value = self.font_small.render(level_value_text, True, WHITE)
            level_value_rect = level_value.get_rect(right=SCREEN_WIDTH - 5, bottom=SCREEN_HEIGHT - 1)
            self.screen.blit(level_value, level_value_rect)
            
            level_label = self.font_small.render("LEVEL:", True, BLACK)
            level_label_rect = level_label.get_rect(right=level_value_rect.left - 3, bottom=SCREEN_HEIGHT )
            self.screen.blit(level_label, level_label_rect)
            level_label = self.font_small.render("LEVEL:", True, NEON_YELLOW)
            level_label_rect = level_label.get_rect(right=level_value_rect.left - 4, bottom=SCREEN_HEIGHT - 1)
            self.screen.blit(level_label, level_label_rect)
            
            # Only show worms counter in endless mode (visible on screen in adventure mode)
            if self.game_mode != "adventure":
                # Endless mode: show fruits eaten / 12
                worm_count_text = "{}/12".format(self.fruits_eaten_this_level)
                # Draw full text centered
                worms_text = self.font_small.render("WORMS:", True, BLACK)
                worms_text_rect = worms_text.get_rect(right=level_value_rect.left - 19, top=4)
                self.screen.blit(worms_text, worms_text_rect)
                worms_text = self.font_small.render("WORMS:", True, NEON_YELLOW)
                worms_text_rect = worms_text.get_rect(right=level_value_rect.left - 20, top=3)
                self.screen.blit(worms_text, worms_text_rect)

                fruits_text = self.font_small.render(worm_count_text, True, BLACK)
                fruits_text_rect = fruits_text.get_rect(right=SCREEN_WIDTH - 4, top=4)
                self.screen.blit(fruits_text, fruits_text_rect)
                fruits_text = self.font_small.render(worm_count_text, True, WHITE)
                fruits_text_rect = fruits_text.get_rect(right=SCREEN_WIDTH - 5, top=3)
                self.screen.blit(fruits_text, fruits_text_rect)
            
            # Show coins in adventure mode (right side of top bar)
            if self.game_mode == "adventure":
                coins_value_text = "{}".format(getattr(self, 'total_coins', 0))
                coins_value = self.font_small.render(coins_value_text, True, BLACK)
                coins_value_rect = coins_value.get_rect(right=SCREEN_WIDTH - 4, top=4)
                self.screen.blit(coins_value, coins_value_rect)
                coins_value = self.font_small.render(coins_value_text, True, WHITE)
                coins_value_rect = coins_value.get_rect(right=SCREEN_WIDTH - 5, top=3)
                self.screen.blit(coins_value, coins_value_rect)
                
                coins_label = self.font_small.render("COINS:", True, BLACK)
                coins_label_rect = coins_label.get_rect(right=coins_value_rect.left - 2, top=4)
                self.screen.blit(coins_label, coins_label_rect)
                coins_label = self.font_small.render("COINS:", True, YELLOW)
                coins_label_rect = coins_label.get_rect(right=coins_value_rect.left - 3, top=3)
                self.screen.blit(coins_label, coins_label_rect)
        
        # Lives with label (only in single player) - hidden during egg hatching in boss mode
        if not self.is_multiplayer:
            # Hide lives HUD during egg hatching in boss battles
            show_lives = True
            if hasattr(self, 'boss_active') and self.boss_active and self.state == GameState.EGG_HATCHING:
                show_lives = False
            
            if show_lives:
                lives_label = self.font_small.render("LIVES:", True, BLACK)
                self.screen.blit(lives_label, (5, SCREEN_HEIGHT - 12))
                lives_label = self.font_small.render("LIVES:", True, NEON_YELLOW)
                self.screen.blit(lives_label, (4, SCREEN_HEIGHT - 13))
                lives_value = self.font_small.render("{}".format(self.lives), True, BLACK)
                self.screen.blit(lives_value, (42, SCREEN_HEIGHT - 12))  # Increased from 38 to add spacing
                lives_value = self.font_small.render("{}".format(self.lives), True, WHITE)
                self.screen.blit(lives_value, (41, SCREEN_HEIGHT - 13))  # Increased from 37 to add spacing
        
        # Draw "Press A to Fire" message when isotope is collected
        if hasattr(self, 'isotope_message_timer') and self.isotope_message_timer > 0:
            # Draw at bottom center of screen
            message_text = "Press A to Fire"
            # Shadow
            text = self.font_medium.render(message_text, True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2 + 1, SCREEN_HEIGHT - 9))
            self.screen.blit(text, text_rect)
            # Main text with pulsing effect
            pulse = abs((self.isotope_message_timer % 60) - 30) / 30.0  # Pulse between 0 and 1
            alpha = int(200 + pulse * 55)  # Alpha between 200 and 255
            text = self.font_medium.render(message_text, True, NEON_YELLOW)
            text.set_alpha(alpha)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10))
            self.screen.blit(text, text_rect)
            
            # Decrement timer
            self.isotope_message_timer -= 1
        
        # Draw achievement notification if active
        if self.achievement_notification_active:
            # Position at bottom of screen
            notification_y = SCREEN_HEIGHT - 30  # Halved from 60
            
            # Calculate fade effect for first and last 30 frames
            fade_duration = 30
            if self.achievement_notification_timer > 270:  # First 30 frames (300-270)
                fade_progress = (300 - self.achievement_notification_timer) / fade_duration
                alpha = int(255 * fade_progress)
            elif self.achievement_notification_timer < 30:  # Last 30 frames
                fade_progress = self.achievement_notification_timer / fade_duration
                alpha = int(255 * fade_progress)
            else:
                alpha = 255
            
            # Draw "Achievement Unlocked!" text
            achievement_text = "Achievement Unlocked!"
            text_shadow = self.font_small.render(achievement_text, True, BLACK)
            text_shadow.set_alpha(alpha)
            text_shadow_rect = text_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, notification_y - 18))
            self.screen.blit(text_shadow, text_shadow_rect)
            
            text_main = self.font_small.render(achievement_text, True, NEON_YELLOW)
            text_main.set_alpha(alpha)
            text_main_rect = text_main.get_rect(center=(SCREEN_WIDTH // 2, notification_y - 20))
            self.screen.blit(text_main, text_main_rect)
            
            # Draw trophy icon next to achievement name
            trophy_x = SCREEN_WIDTH // 2 - 80
            if self.trophy_icon:
                trophy_copy = self.trophy_icon.copy()
                trophy_copy.set_alpha(alpha)
                self.screen.blit(trophy_copy, (trophy_x, notification_y - 2))
            
            # Draw achievement name
            name_shadow = self.font_medium.render(self.achievement_notification_name, True, BLACK)
            name_shadow.set_alpha(alpha)
            name_shadow_rect = name_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, notification_y + 12))
            self.screen.blit(name_shadow, name_shadow_rect)
            
            name_main = self.font_medium.render(self.achievement_notification_name, True, NEON_CYAN)
            name_main.set_alpha(alpha)
            name_main_rect = name_main.get_rect(center=(SCREEN_WIDTH // 2, notification_y + 10))
            self.screen.blit(name_main, name_main_rect)

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(DARK_BG)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, NEON_YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 15))
        self.screen.blit(pause_text, pause_rect)
        
        hint_text = self.font_small.render("Start to resume", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(hint_text, hint_rect)
        
        # Show exit option
        if self.is_network_game:
            exit_text = self.font_small.render("B/Esc to leave game", True, NEON_PINK)
        else:
            exit_text = self.font_small.render("B/Esc to quit", True, NEON_PINK)
        exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(exit_text, exit_rect)
    
    def draw_game_over(self):
        # Draw game over screen - use multiBG.png for all modes
        if self.multi_bg:
            self.screen.blit(self.multi_bg, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Draw "GAME OVER" text
        if self.game_over_timer > 0:
            # During the 3-second timer, center the text
            over_text = self.font_large.render("GAME OVER", True, BLACK)
            over_rect = over_text.get_rect(center=((SCREEN_WIDTH // 2) + 3, (SCREEN_HEIGHT // 2) + 3))
            self.screen.blit(over_text, over_rect)
            over_text = self.font_large.render("GAME OVER", True, NEON_PINK)
            over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(over_text, over_rect)
        else:
            # After timer expires, show "GAME OVER" at top and score/level info
            over_text = self.font_large.render("GAME OVER", True, BLACK)
            over_rect = over_text.get_rect(center=((SCREEN_WIDTH // 2) + 3, 63))
            self.screen.blit(over_text, over_rect)
            over_text = self.font_large.render("GAME OVER", True, NEON_PINK)
            over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
            self.screen.blit(over_text, over_rect)
            
            if self.is_multiplayer:
                # Show winner (player with lives remaining)
                winners = [s for s in self.snakes if s.lives > 0]
                
                if len(winners) == 1:
                    winner = winners[0]
                    winner_text = "Player {} Wins!".format(winner.player_id + 1)
                    color = self.player_colors[winner.player_id]
                elif len(winners) > 1:
                    winner_text = "Draw!"
                    color = NEON_YELLOW
                else:
                    # All eliminated (shouldn't happen in normal gameplay)
                    winner_text = "No Winner"
                    color = GRAY
                
                # Center the winner text
                text = self.font_large.render(winner_text, True, BLACK)
                rect = text.get_rect(center=((SCREEN_WIDTH // 2) + 3, (SCREEN_HEIGHT // 2) + 3))
                self.screen.blit(text, rect)
                text = self.font_large.render(winner_text, True, color)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(text, rect)
            else:
                # Single player results
                score_text = self.font_medium.render("Score: {}".format(self.score), True, NEON_CYAN)
                score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 110))
                self.screen.blit(score_text, score_rect)
                
                level_text = self.font_medium.render("Level: {}".format(self.level), True, NEON_GREEN)
                level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 145))
                self.screen.blit(level_text, level_rect)
            
            # Show appropriate hint based on game type
            if self.is_network_game:
                if self.network_manager.is_host():
                    hint_text = self.font_small.render("Start to return to lobby", True, NEON_YELLOW)
                else:
                    hint_text = self.font_small.render("Waiting for host...", True, NEON_YELLOW)
                hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 210))
                self.screen.blit(hint_text, hint_rect)
                
                # Show auto-progress countdown
                if hasattr(self, 'network_game_over_auto_timer') and self.network_game_over_auto_timer > 0:
                    seconds_left = (self.network_game_over_auto_timer + 59) // 60  # Round up
                    timer_text = self.font_small.render(f"Auto-continue in {seconds_left}s", True, GRAY)
                    timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, 235))
                    self.screen.blit(timer_text, timer_rect)
            else:
                hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
                hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
                self.screen.blit(hint_text, hint_rect)
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(DARK_BG)
        self.screen.blit(overlay, (0, 0))
        
        if self.game_mode == "adventure" and not self.is_multiplayer:
            # Adventure mode victory screen with completion percentage
            complete_text = self.font_large.render("VICTORY!", True, BLACK)
            complete_rect = complete_text.get_rect(center=((SCREEN_WIDTH // 2)+3, 43))
            self.screen.blit(complete_text, complete_rect)
            complete_text = self.font_large.render("VICTORY!", True, NEON_YELLOW)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
            self.screen.blit(complete_text, complete_rect)
            
            # Show completion percentage
            if hasattr(self, 'completion_percentage'):
                percent_text = "{}% Complete".format(self.completion_percentage)
                percent_label = self.font_large.render(percent_text, True, BLACK)
                percent_rect = percent_label.get_rect(center=((SCREEN_WIDTH // 2)+2, 77))
                self.screen.blit(percent_label, percent_rect)
                percent_label = self.font_large.render(percent_text, True, NEON_GREEN)
                percent_rect = percent_label.get_rect(center=(SCREEN_WIDTH // 2, 75))
                self.screen.blit(percent_label, percent_rect)
            
            # Show breakdown
            y_pos = 115
            
            # Segments
            if hasattr(self, 'final_segments'):
                segments_text = "Segments: {}".format(self.final_segments)
                segments_label = self.font_medium.render(segments_text, True, BLACK)
                segments_rect = segments_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
                self.screen.blit(segments_label, segments_rect)
                segments_label = self.font_medium.render(segments_text, True, NEON_CYAN)
                segments_rect = segments_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(segments_label, segments_rect)
                y_pos += 30
            
            # Worms collected
            worms_text = "Worms: {}/{}".format(self.worms_collected, self.worms_required)
            worms_label = self.font_medium.render(worms_text, True, BLACK)
            worms_rect = worms_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
            self.screen.blit(worms_label, worms_rect)
            worms_label = self.font_medium.render(worms_text, True, WHITE)
            worms_rect = worms_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.screen.blit(worms_label, worms_rect)
            y_pos += 30
            
            # Bonus fruits collected
            if hasattr(self, 'total_bonus_fruits') and self.total_bonus_fruits > 0:
                bonus_text = "Bonus: {}/{}".format(self.bonus_fruits_collected, self.total_bonus_fruits)
                bonus_label = self.font_medium.render(bonus_text, True, BLACK)
                bonus_rect = bonus_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
                self.screen.blit(bonus_label, bonus_rect)
                bonus_label = self.font_medium.render(bonus_text, True, NEON_ORANGE)
                bonus_rect = bonus_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(bonus_label, bonus_rect)
                y_pos += 30
            
            # Show best completion for this level
            level_high = self.get_level_high_score(self.current_adventure_level)
            high_text = "Best: {}%".format(level_high)
            high_label = self.font_small.render(high_text, True, BLACK)
            high_rect = high_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
            self.screen.blit(high_label, high_rect)
            high_label = self.font_small.render(high_text, True, NEON_YELLOW)
            high_rect = high_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.screen.blit(high_label, high_rect)
            y_pos += 25
            
            # Check if new high score - show on separate line
            if hasattr(self, 'is_new_level_high_score') and self.is_new_level_high_score:
                new_high_text = self.font_small.render("NEW BEST!", True, BLACK)
                new_high_rect = new_high_text.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
                self.screen.blit(new_high_text, new_high_rect)
                new_high_text = self.font_small.render("NEW BEST!", True, NEON_GREEN)
                new_high_rect = new_high_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(new_high_text, new_high_rect)
            
            hint_text = self.font_small.render("Start to continue", True, BLACK)
            hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 222))
            self.screen.blit(hint_text, hint_rect)
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
            self.screen.blit(hint_text, hint_rect)
        elif self.is_multiplayer:
            # Show round results
            # Find winner of this round
            winner_id = None
            for i in range(self.num_players):
                if self.snakes[i].alive:
                    winner_id = i
                    break
            
            if winner_id is not None:
                winner_text = "Player {} wins round {}!".format(winner_id + 1, self.current_round)
                color = self.player_colors[winner_id]
            else:
                winner_text = "Round {} - Draw!".format(self.current_round)
                color = WHITE
            
            complete_text = self.font_large.render(winner_text, True, BLACK)
            complete_rect = complete_text.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT // 2 - 40+3))
            self.screen.blit(complete_text, complete_rect)
            complete_text = self.font_large.render(winner_text, True, color)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(complete_text, complete_rect)
            
            # Show round scores
            y_offset = SCREEN_HEIGHT // 2
            for i in range(self.num_players):
                score_text = "{}: {} wins".format(self.player_names[i], self.round_wins[i])
                text = self.font_small.render(score_text, True, BLACK)
                rect = text.get_rect(center=((SCREEN_WIDTH // 2)+2, y_offset+2))
                self.screen.blit(text, rect)
                text = self.font_small.render(score_text, True, self.player_colors[i])
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                self.screen.blit(text, rect)
                y_offset += 13  # Halved from 25 (rounded)
            
            hint_text = self.font_small.render("Start to continue", True, BLACK)
            hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, SCREEN_HEIGHT - 30+2))
            self.screen.blit(hint_text, hint_rect)
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            self.screen.blit(hint_text, hint_rect)
        else:
            # Single player level complete
            complete_text = self.font_large.render("LEVEL UP!", True, BLACK)
            complete_rect = complete_text.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT // 2 - 20+3))
            self.screen.blit(complete_text, complete_rect)

            complete_text = self.font_large.render("LEVEL UP!", True, NEON_YELLOW)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            self.screen.blit(complete_text, complete_rect)
            
            bonus_text = self.font_medium.render("Bonus Life!", True, BLACK)
            bonus_rect = bonus_text.get_rect(center=((SCREEN_WIDTH // 2)+2, SCREEN_HEIGHT // 2 + 15+2))
            self.screen.blit(bonus_text, bonus_rect)
            bonus_text = self.font_medium.render("Bonus Life!", True, NEON_YELLOW)
            bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 15))
            self.screen.blit(bonus_text, bonus_rect)
            
            hint_text = self.font_small.render("Start to continue", True, BLACK)
            hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT // 2 + 53))
            self.screen.blit(hint_text, hint_rect)
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(hint_text, hint_rect)
    
    def draw_achievements(self):
        """Draw the achievements screen."""
        # Use background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("ACHIEVEMENTS", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 53))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("ACHIEVEMENTS", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Get achievements list
        achievements = self.get_achievement_list()
        
        if not achievements:
            # No achievements defined
            msg = self.font_medium.render("No achievements defined", True, BLACK)
            msg_rect = msg.get_rect(center=((SCREEN_WIDTH // 2)+2, 242))
            self.screen.blit(msg, msg_rect)
            msg = self.font_medium.render("No achievements defined", True, NEON_CYAN)
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, 240))
            self.screen.blit(msg, msg_rect)
        else:
            # Draw achievements list
            start_y = 45  # Halved from 90
            line_height = 14  # Halved from 28
            
            for i, achievement in enumerate(achievements):
                y_pos = start_y + i * line_height
                
                # Determine color based on unlocked status
                if achievement['unlocked']:
                    color = NEON_CYAN
                    # Draw trophy icon
                    if self.trophy_icon:
                        trophy_scaled = pygame.transform.scale(self.trophy_icon, (5, 5))  # Halved from 10
                        self.screen.blit(trophy_scaled, (15, y_pos - 1))  # Halved from 30
                else:
                    color = GRAY
                
                # Highlight selected achievement
                if i == self.achievement_selection:
                    # Draw selection indicator
                    indicator = self.font_small.render(">", True, NEON_YELLOW)
                    self.screen.blit(indicator, (8, y_pos))  # Halved from 15
                
                # Draw achievement name with shadow
                name_shadow = self.font_small.render(achievement['name'], True, BLACK)
                self.screen.blit(name_shadow, (29, y_pos + 1))  # Halved from 57
                
                name_text = self.font_small.render(achievement['name'], True, color)
                self.screen.blit(name_text, (28, y_pos))  # Halved from 55
            
            # Draw description box at bottom for selected achievement
            if 0 <= self.achievement_selection < len(achievements):
                selected = achievements[self.achievement_selection]
                
                # Description box background
                desc_box_y = 160  # Halved from 320
                desc_box_height = 50  # Halved from 100
                desc_box = pygame.Surface((SCREEN_WIDTH - 20, desc_box_height))  # Halved from 40
                desc_box.fill(BLACK)
                desc_box.set_alpha(180)
                self.screen.blit(desc_box, (10, desc_box_y))  # Halved from 20
                
                # Description title
                desc_title = "Description:"
                title_shadow = self.font_small.render(desc_title, True, BLACK)
                self.screen.blit(title_shadow, (16, desc_box_y + 6))  # Halved from 32, 12
                title_text = self.font_small.render(desc_title, True, NEON_YELLOW)
                self.screen.blit(title_text, (15, desc_box_y + 5))  # Halved from 30, 10
                
                # Description text (word wrap if needed)
                description = selected['description']
                desc_shadow = self.font_small.render(description, True, BLACK)
                self.screen.blit(desc_shadow, (16, desc_box_y + 21))  # Halved from 32, 42
                desc_text = self.font_small.render(description, True, WHITE)
                self.screen.blit(desc_text, (15, desc_box_y + 20))  # Halved from 30, 40
                
                # Status
                if selected['unlocked']:
                    status = "UNLOCKED"
                    status_color = NEON_GREEN
                else:
                    status = "LOCKED"
                    status_color = RED
                
                status_shadow = self.font_small.render(status, True, BLACK)
                self.screen.blit(status_shadow, (16, desc_box_y + 36))  # Halved from 32, 72
                status_text = self.font_small.render(status, True, status_color)
                self.screen.blit(status_text, (15, desc_box_y + 35))  # Halved from 30, 70
        
        # Hint text
        hint_text = self.font_small.render("Press Start to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))  # Halved from 452
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press Start to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Halved from 450)
        self.screen.blit(hint_text, hint_rect)
    
    def draw_music_player(self):
        """Draw the music player screen."""
        # Use background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("MUSIC PLAYER", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 13))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("MUSIC PLAYER", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 10))
        self.screen.blit(title, title_rect)
        
        # Display total coins below title (centered)
        coin_display_x = SCREEN_WIDTH // 2
        coin_display_y = 30
        
        # Draw coin icon
        coin_radius = 8
        pygame.draw.circle(self.screen, YELLOW, (coin_display_x - 25, coin_display_y), coin_radius)
        pygame.draw.circle(self.screen, (255, 165, 0), (coin_display_x - 25, coin_display_y), coin_radius, 2)
        pygame.draw.circle(self.screen, (255, 165, 0), (coin_display_x - 25, coin_display_y), coin_radius - 3, 1)
        
        # Draw coin count with medium font
        coins_text = self.font_medium.render(str(getattr(self, 'total_coins', 0)), True, BLACK)
        coins_rect = coins_text.get_rect(left=coin_display_x - 14, centery=coin_display_y + 1)
        self.screen.blit(coins_text, coins_rect)
        
        coins_text = self.font_medium.render(str(getattr(self, 'total_coins', 0)), True, YELLOW)
        coins_rect = coins_text.get_rect(left=coin_display_x - 15, centery=coin_display_y)
        self.screen.blit(coins_text, coins_rect)
        
        # Track list
        if len(self.music_player_tracks) == 0:
            no_tracks = self.font_medium.render("No tracks found", True, NEON_CYAN)
            no_tracks_rect = no_tracks.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(no_tracks, no_tracks_rect)
        else:
            # Display up to 8 tracks at a time (larger font = fewer visible)
            start_y = 52  # Start below coin display
            spacing = 22  # Spacing between tracks (larger for bigger font)
            visible_tracks = 8
            
            # Calculate which tracks to show (center the selection)
            start_idx = max(0, self.music_player_selection - visible_tracks // 2)
            end_idx = min(len(self.music_player_tracks), start_idx + visible_tracks)
            
            # Adjust start_idx if we're near the end
            if end_idx - start_idx < visible_tracks:
                start_idx = max(0, end_idx - visible_tracks)
            
            for i in range(start_idx, end_idx):
                track_name, track_path, filename = self.music_player_tracks[i]
                y = start_y + (i - start_idx) * spacing
                is_unlocked = self.is_music_unlocked(filename)
                cost = self.get_music_cost(filename)
                
                # Determine color based on state
                if not is_unlocked:
                    # Locked track - gray
                    color = DARK_GRAY if i != self.music_player_selection else GRAY
                    prefix = "  "
                elif i == self.music_player_current_track and self.music_player_playing:
                    # Currently playing - bright green with play indicator
                    color = NEON_GREEN
                    prefix = "► "
                elif i == self.music_player_current_track and not self.music_player_playing:
                    # Paused track - orange with pause indicator
                    color = NEON_ORANGE
                    prefix = "❚❚ "
                elif i == self.music_player_selection:
                    # Selected but not playing - yellow
                    color = NEON_YELLOW
                    prefix = "  "
                else:
                    # Not selected - cyan
                    color = NEON_CYAN
                    prefix = "  "
                
                # Draw lock icon for locked tracks (doubled size)
                if not is_unlocked and self.lock_icon:
                    scaled_lock = pygame.transform.scale(self.lock_icon, (28, 28))  # Double from 14x14
                    self.screen.blit(scaled_lock, (20, y))
                # Draw hatchling head icon for selected track (doubled size)
                elif i == self.music_player_selection and self.hatchling_head_icon:
                    scaled_head = pygame.transform.scale(self.hatchling_head_icon, (28, 28))  # Double from 14x14
                    self.screen.blit(scaled_head, (20, y))
                
                # Truncate long track names to make room for cost
                display_name = track_name
                max_length = 12 if not is_unlocked else 16
                if len(display_name) > max_length:
                    display_name = display_name[:max_length-3] + "..."
                
                text = self.font_medium.render(prefix + display_name, True, BLACK)
                text_rect = text.get_rect(left=52, top=y+2)
                self.screen.blit(text, text_rect)
                
                text = self.font_medium.render(prefix + display_name, True, color)
                text_rect = text.get_rect(left=50, top=y)
                self.screen.blit(text, text_rect)
                
                # Draw coin cost for locked tracks
                if not is_unlocked:
                    # Draw coin icon
                    coin_x = SCREEN_WIDTH - 60
                    coin_y = y + 12
                    coin_radius = 8
                    pygame.draw.circle(self.screen, YELLOW, (coin_x, coin_y), coin_radius)
                    pygame.draw.circle(self.screen, (255, 165, 0), (coin_x, coin_y), coin_radius, 2)
                    pygame.draw.circle(self.screen, (255, 165, 0), (coin_x, coin_y), coin_radius - 3, 1)
                    
                    # Draw cost with medium font
                    cost_text = self.font_medium.render(str(cost), True, BLACK)
                    cost_rect = cost_text.get_rect(left=coin_x + 12, centery=coin_y + 1)
                    self.screen.blit(cost_text, cost_rect)
                    
                    cost_text = self.font_medium.render(str(cost), True, YELLOW)
                    cost_rect = cost_text.get_rect(left=coin_x + 11, centery=coin_y)
                    self.screen.blit(cost_text, cost_rect)
        
        # Control section at bottom
        # Removed "Playing:" status text to avoid overlap with hints
        # The selected track is already highlighted in the list
        
        # Control buttons (hidden - using text controls instead)
        button_y = -100  # Off-screen
        button_size = 15  # Halved from 30
        center_x = SCREEN_WIDTH // 2
        
        # Previous button (◄)
        prev_x = center_x - 40  # Halved from 80
        pygame.draw.polygon(self.screen, BLACK, [
            (prev_x + 3, button_y + button_size // 2 + 3),
            (prev_x + button_size - 7, button_y + 3),
            (prev_x + button_size - 7, button_y + button_size + 3)
        ])
        pygame.draw.rect(self.screen, NEON_CYAN, (prev_x, button_y, 3, button_size))
        pygame.draw.polygon(self.screen, NEON_CYAN, [
            (prev_x + 3, button_y + button_size // 2),
            (prev_x + button_size - 7, button_y ),
            (prev_x + button_size - 7, button_y + button_size)
        ])
        
        # Play/Pause button (center)
        if self.music_player_playing:
            # Pause button (❚❚)
            bar_width = 8
            bar_spacing = 6
            bar_height = button_size
            pygame.draw.rect(self.screen, BLACK, (center_x - bar_spacing // 2 - bar_width + 3, button_y + 3, bar_width, bar_height))
            pygame.draw.rect(self.screen, BLACK, (center_x + bar_spacing // 2 + 3, button_y + 3, bar_width, bar_height))
            pygame.draw.rect(self.screen, NEON_YELLOW, (center_x - bar_spacing // 2 - bar_width, button_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, NEON_YELLOW, (center_x + bar_spacing // 2, button_y, bar_width, bar_height))
        else:
            # Play button (►)
            pygame.draw.polygon(self.screen, BLACK, [
                (center_x - 10 + 3, button_y + 3),
                (center_x + 15 + 3, button_y + button_size // 2 + 3),
                (center_x - 10 + 3, button_y + button_size + 3)
            ])
            pygame.draw.polygon(self.screen, NEON_GREEN, [
                (center_x - 10, button_y),
                (center_x + 15, button_y + button_size // 2),
                (center_x - 10, button_y + button_size)
            ])
        
        # Next button (►)
        next_x = center_x + 25  # Halved from 50
        pygame.draw.polygon(self.screen, BLACK, [
            (next_x + button_size - 7, button_y + button_size // 2 + 3),
            (next_x + 3, button_y + 3),
            (next_x + 3, button_y + button_size + 3)
        ])
        pygame.draw.polygon(self.screen, NEON_CYAN, [
            (next_x + button_size - 7, button_y + button_size // 2),
            (next_x + 3, button_y),
            (next_x + 3, button_y + button_size)
        ])
        pygame.draw.rect(self.screen, NEON_CYAN, (next_x + button_size - 7, button_y, 3, button_size))
        
        # Control hints
        hint_y = SCREEN_HEIGHT - 12
        hint_text = self.font_small.render("A: Play/Pause  |  L/R: Skip", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, hint_y+1))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("A: Play/Pause  |  L/R: Skip", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, hint_y))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_level_editor_menu(self):
        """Draw the level editor menu screen."""
        # Use background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("LEVEL EDITOR", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 53))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("LEVEL EDITOR", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Info message
        msg1 = self.font_medium.render("Use runEditor.sh to", True, BLACK)
        msg1_rect = msg1.get_rect(center=((SCREEN_WIDTH // 2)+2, 212))
        self.screen.blit(msg1, msg1_rect)
        msg1 = self.font_medium.render("Use runEditor.sh to", True, NEON_CYAN)
        msg1_rect = msg1.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(msg1, msg1_rect)
        
        msg2 = self.font_medium.render("launch the Level Editor", True, BLACK)
        msg2_rect = msg2.get_rect(center=((SCREEN_WIDTH // 2)+2, 262))
        self.screen.blit(msg2, msg2_rect)
        msg2 = self.font_medium.render("launch the Level Editor", True, NEON_CYAN)
        msg2_rect = msg2.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self.screen.blit(msg2, msg2_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press Start to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+1, 226))  # Halved from 452
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press Start to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Halved from 450)
        self.screen.blit(hint_text, hint_rect)
    
    def draw_credits(self):
        """Draw the credits screen after boss battle victory."""
        # Fill screen with dark background
        self.screen.fill(BLACK)

        # Credits
        y_pos = 50
        credits_lines = [
            ("Game Designed By", NEON_CYAN),
            ("", WHITE),
            ("Austin Morgan", NEON_PINK),
            ("", WHITE),
            ("Coding: Claude Sonnet 4.5 Thinking", WHITE),
            ("Graphics: GPT 5", WHITE),
            ("Animations: Austin Morgan", WHITE),
            ("Music: Suno AI Music", WHITE),
            ("Sound Effects: Austin Morgan", WHITE),
            ("", WHITE),
            ("Bonus Level unlocked!", NEON_PINK),
        ]
        
        for line_text, color in credits_lines:
            if line_text:  # Skip empty lines for spacing
                text = self.font_small.render(line_text, True, BLACK)
                text_rect = text.get_rect(center=((SCREEN_WIDTH // 2) + 2, y_pos + 2))
                self.screen.blit(text, text_rect)
                text = self.font_small.render(line_text, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(text, text_rect)
            y_pos += 15  # Halved from 30
        
        # Bottom hint
        hint_text = self.font_small.render("Press Start to return to menu", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2) + 1, SCREEN_HEIGHT - 21))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press Start to return to menu", True, NEON_YELLOW)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_high_score_entry(self):
        # Draw high score screen image as background
        if self.highscore_screen:
            self.screen.blit(self.highscore_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title at top with more space
        title = self.font_large.render("NEW HIGH SCORE!", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 23))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("NEW HIGH SCORE!", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(title, title_rect)
        

        # Score below title with proper spacing
        score_text = self.font_medium.render("Score: {}".format(self.score), True, BLACK)
        score_rect = score_text.get_rect(center=((SCREEN_WIDTH // 2)+3, 46))
        self.screen.blit(score_text, score_rect)
        # Score below title with proper spacing
        score_text = self.font_medium.render("Score: {}".format(self.score), True, NEON_CYAN)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 43))
        self.screen.blit(score_text, score_rect)

        
        # Name entry with better spacing
        name_y = 67
        for i, char in enumerate(self.player_name):
            x = SCREEN_WIDTH // 2 - 40 + i * 30
            color = WHITE if i == self.name_index else NEON_YELLOW
            char_text = self.font_large.render(char, True, BLACK)
            char_rect = char_text.get_rect(center=((x+3, name_y+3)))
            self.screen.blit(char_text, char_rect)
            char_text = self.font_large.render(char, True, color)
            char_rect = char_text.get_rect(center=(x, name_y))
            self.screen.blit(char_text, char_rect)
            
        
        # Keyboard layout with better spacing - centered
        key_y_start = 85
        key_spacing_x = 20  # Horizontal spacing between keys
        key_spacing_y = 28  # Vertical spacing between rows
        keyboard_width = len(self.keyboard_layout[0]) * key_spacing_x
        start_x = (SCREEN_WIDTH - keyboard_width) // 2 + key_spacing_x // 2
        
        for row_idx, row in enumerate(self.keyboard_layout):
            for col_idx, char in enumerate(row):
                x = start_x + col_idx * key_spacing_x
                y = key_y_start + row_idx * key_spacing_y
                
                is_selected = (row_idx == self.keyboard_selection[0] and 
                             col_idx == self.keyboard_selection[1])
                
                # Draw shadow first
                key_text = self.font_medium.render(char, True, BLACK)
                key_rect = key_text.get_rect(center=(x+2, y+2))
                self.screen.blit(key_text, key_rect)
                
                # Draw main text in white (or yellow if selected)
                color = NEON_YELLOW if is_selected else WHITE
                key_text = self.font_medium.render(char, True, color)
                key_rect = key_text.get_rect(center=(x, y))
                self.screen.blit(key_text, key_rect)
                
                if is_selected:
                    pygame.draw.rect(self.screen, NEON_PINK,
                                   (key_rect.left - 5, key_rect.top - 3,
                                    key_rect.width + 10, key_rect.height + 6), 2)
        # Use the pre-selected hint for this session
        # Legend at bottom
        hint_text = self.current_hint
        legend_text = self.font_small.render(hint_text, True, BLACK)
        legend_rect = legend_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 207))
        self.screen.blit(legend_text, legend_rect)
        legend_text = self.font_small.render(hint_text, True, NEON_CYAN)
        legend_rect = legend_text.get_rect(center=(SCREEN_WIDTH // 2, 205))
        self.screen.blit(legend_text, legend_rect)
        hint_text = self.font_small.render("Start to continue", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 227))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Start to continue", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_high_scores(self):
        # Draw high score screen image as background
        if self.highscore_screen:
            self.screen.blit(self.highscore_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        # Title at top
        title = self.font_large.render("HIGH SCORES", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 17))
        self.screen.blit(title, title_rect)

        # Title at top
        title = self.font_large.render("HIGH SCORES", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 15))
        self.screen.blit(title, title_rect)
        
        if not self.high_scores:
            no_scores = self.font_medium.render("No scores yet!", True, BLACK)
            no_scores_rect = no_scores.get_rect(center=((SCREEN_WIDTH // 2)+3, 153))
            self.screen.blit(no_scores, no_scores_rect)
            no_scores = self.font_medium.render("No scores yet!", True, NEON_CYAN)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, 150))
            self.screen.blit(no_scores, no_scores_rect)
        else:
            # Score list with better spacing to fill the screen
            start_y = 28
            spacing = 19
            for i, entry in enumerate(self.high_scores[:10]):
                name = entry['name']
                score = entry['score']
                y = start_y + i * spacing
                
                # Rank number with shadow
                rank_text = self.font_medium.render("{}".format(i+1), True, BLACK)
                self.screen.blit(rank_text, (32, y+2))
                rank_text = self.font_medium.render("{}".format(i+1), True, WHITE)
                self.screen.blit(rank_text, (30, y))
                
                # Name with shadow
                name_text = self.font_medium.render(name, True, BLACK)
                self.screen.blit(name_text, (82, y+2))
                name_text = self.font_medium.render(name, True, NEON_GREEN)
                self.screen.blit(name_text, (80, y))
                
                # Score with shadow
                score_text = self.font_medium.render(str(score), True, BLACK)
                score_rect = score_text.get_rect(right=(SCREEN_WIDTH - 28), top=y + 2)
                self.screen.blit(score_text, score_rect)
                score_text = self.font_medium.render(str(score), True, NEON_CYAN)
                score_rect = score_text.get_rect(right=SCREEN_WIDTH - 30, top=y)
                self.screen.blit(score_text, score_rect)
        
        # Hint text at bottom
        hint_text = self.font_small.render("Start to continue", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 227))  # Halved from 452 + 1
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Start to continue", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Halved from 450
        self.screen.blit(hint_text, hint_rect)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
