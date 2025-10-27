#!/usr/bin/env python3
import pygame
import json
import os
import random
from game_core import Snake, GameState, Difficulty, Direction, Particle, GifParticle, EggPiece, MusicManager, SoundManager, Enemy, Bullet, Spewtum, hue_shift_surface, hue_shift_frames, hue_shift_color
from game_core import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, HUD_HEIGHT, GAME_OFFSET_Y
from game_core import BLACK, WHITE, GREEN, DARK_GREEN, RED, YELLOW, ORANGE, GRAY, DARK_GRAY
from game_core import NEON_GREEN, NEON_LIME, NEON_PINK, NEON_CYAN, NEON_ORANGE, NEON_PURPLE, NEON_YELLOW, NEON_BLUE
from game_core import GRID_COLOR, HUD_BG, DARK_BG

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

pygame.init()
pygame.mixer.init()

FPS = 60

class SnakeGame:
    def __init__(self):
        # Scaling factor
        self.scale = 1
        
        # Create the actual display window (scaled up)
        self.display = pygame.display.set_mode((SCREEN_WIDTH * self.scale, SCREEN_HEIGHT * self.scale))
        
        # Create the render surface (native resolution)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption("Snake Game")
        pygame.mouse.set_visible(False)  # Hide mouse cursor
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 32)  # 2x larger (was 16)
        self.font_medium = pygame.font.Font(None, 48)  # 2x larger (was 24)
        self.font_large = pygame.font.Font(None, 66)  # 2x larger (was 36)
        
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
            difficulty_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'difficulty.png')
            self.difficulty_screen = pygame.image.load(difficulty_path).convert()
            self.difficulty_screen = pygame.transform.scale(self.difficulty_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.difficulty_screen = None
            print("Warning: difficulty.png not found, using default difficulty screen")
        
        # Load splash screen image
        try:
            splash_path = os.path.join(SCRIPT_DIR, 'img', 'bg', 'splashAMS.png')
            self.splash_screen = pygame.image.load(splash_path).convert()
            self.splash_screen = pygame.transform.scale(self.splash_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.splash_screen = None
            print("Warning: splashAMS.png not found, skipping splash screen")
        
        # Load Tweetrix logo
        try:
            tweetrix_path = os.path.join(SCRIPT_DIR, 'img', 'Tweetrix.png')
            self.tweetrix_logo = pygame.image.load(tweetrix_path).convert_alpha()
            # Scale logo to reasonable size (e.g., 100px wide, maintain aspect ratio)
            logo_width = 50
            aspect_ratio = self.tweetrix_logo.get_height() / self.tweetrix_logo.get_width()
            logo_height = int(logo_width * aspect_ratio)
            self.tweetrix_logo = pygame.transform.scale(self.tweetrix_logo, (logo_width, logo_height))
        except:
            self.tweetrix_logo = None
            print("Warning: Tweetrix.png not found")
        
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
        
        for player_num in range(1, 5):  # Players 1-4
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
        
        # Keep original for backwards compatibility
        self.snake_body_img = self.snake_body_imgs[0] if self.snake_body_imgs else None
        
        # Load snake head animations (GIF) for all 4 players
        self.snake_head_frames_all = []  # List of frame lists for each player
        
        for player_num in range(1, 5):  # Players 1-4
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
                    self.particle_rainbow_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass
            
            print("Loaded {} frames for rainbow particle animation".format(len(self.particle_rainbow_frames)))
        except Exception as e:
            self.particle_rainbow_frames = []
            print("Warning: particlesRainbow.gif not found or could not be loaded: {}".format(e))
        
        # Load worm (food) animation (GIF)
        try:
            from PIL import Image
            worm_path = os.path.join(SCRIPT_DIR, 'img', 'worm.gif')
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
            print("Warning: worm.gif not found or could not be loaded: {}".format(e))
        
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
        
        # Load boss animations
        self.boss_animations = {}
        boss_anim_names = ['wormBossEmerges', 'wormBossIdle', 'wormBossAttack', 'bossWormDeath1', 'bossWormDeath3']
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
                        # Keep original 256x256 size for boss
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
        self.boss_minion_respawn_timers = {}  # Dict of minion_id -> respawn_timer
        self.boss_attack_timer = 0  # Timer for periodic boss attacks
        self.boss_attack_interval = 1200  # Start at 20 seconds (1200 frames at 60 FPS)
        self.boss_attack_interval_min = 180  # Fastest attack speed: 3 seconds
        self.boss_attack_interval_max = 1200  # Slowest attack speed: 20 seconds
        self.boss_is_attacking = False  # Whether boss is currently in attack animation
        self.spewtums = []  # List of active spewtum projectiles
        self.boss_health = 1  # Boss health
        self.boss_max_health = 1  # Boss maximum health
        self.boss_damage_flash = 0  # Timer for red flash when boss is hit
        self.boss_damage_sound_cooldown = 0  # Cooldown to prevent damage sounds from overlapping
        self.boss_super_attack_thresholds = [0.75, 0.5, 0.25]  # Health % thresholds for super attacks
        self.boss_super_attacks_used = set()  # Track which thresholds have been used
        self.boss_defeated = False  # Whether boss has been defeated
        self.boss_death_delay = 0  # Delay before level completion after death animation
        self.boss_death_phase = 0  # Current death animation phase (0=not started, 1-4=phases)
        self.boss_death_timer = 0  # Timer for death phase 2 (static image hold)
        self.boss_death_particle_timer = 0  # Timer for spawning particles during phase 3
        
        # Load UI icons for multiplayer lobby
        # Star rating icons for difficulty
        self.icon_size = 48  # Standard icon size (2x for better visibility)
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
        
        # Multiplayer support
        self.is_multiplayer = False
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
        self.multiplayer_menu_options = ["Same Screen", "Local Network (Coming Soon)", "Back"]
        
        # Multiplayer lobby settings
        self.lobby_selection = 0  # Which setting is selected
        self.lobby_settings = {
            'rounds': 3,
            'lives': 3,
            'item_frequency': 1,  # 0=Low, 1=Normal, 2=High
            'cpu_difficulty': 1,  # 0=Easy, 1=Medium, 2=Hard, 3=Brutal
        }
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
        self.game_over_timer = 0
        self.game_over_delay = 180  # 3 seconds at 60 FPS
        self.multiplayer_end_timer = 0  # Timer for delay after last player dies in multiplayer
        
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
        self.menu_options = ["Single Player", "Multiplayer", "High Scores", "Quit"]
        
        # Single player submenu
        self.single_player_selection = 0
        self.single_player_options = ["Adventure", "Endless", "Back"]
        
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
    
    def load_high_scores(self):
        try:
            highscores_path = os.path.join(SCRIPT_DIR, 'highscores.json')
            if os.path.exists(highscores_path):
                with open(highscores_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_high_scores(self):
        try:
            highscores_path = os.path.join(SCRIPT_DIR, 'highscores.json')
            with open(highscores_path, 'w') as f:
                json.dump(self.high_scores, f)
        except:
            pass
    
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
            level_scores_path = os.path.join(SCRIPT_DIR, 'level_scores.json')
            if os.path.exists(level_scores_path):
                with open(level_scores_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}  # Dictionary: level_number -> best_score
    
    def save_level_scores(self):
        """Save level-specific high scores"""
        try:
            level_scores_path = os.path.join(SCRIPT_DIR, 'level_scores.json')
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
        """Load which levels are unlocked and total coins"""
        try:
            unlock_path = os.path.join(SCRIPT_DIR, 'level_unlocks.json')
            if os.path.exists(unlock_path):
                with open(unlock_path, 'r') as f:
                    data = json.load(f)
                    self.total_coins = data.get('total_coins', 0)
                    return set(data.get('unlocked', [1]))  # Default to level 1 unlocked
        except:
            pass
        self.total_coins = 0
        return {1}  # Only level 1 unlocked by default
    
    def save_unlocked_levels(self):
        """Save which levels are unlocked and total coins"""
        try:
            unlock_path = os.path.join(SCRIPT_DIR, 'level_unlocks.json')
            with open(unlock_path, 'w') as f:
                data = {
                    'unlocked': sorted(list(self.unlocked_levels)),
                    'total_coins': getattr(self, 'total_coins', 0)
                }
                json.dump(data, f, indent=2)
        except:
            pass
    
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
        
        # Boss position is in bottom right (256x256 sprite)
        boss_center_x = self.boss_position[0] + 128  # Center of 256px boss
        boss_center_y = self.boss_position[1] + 128  # Center of 256px boss
        
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
            if (x, y) not in occupied_positions:
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
            # Set a delay before transitioning to game over screen
            self.multiplayer_end_timer = 120  # 2 seconds at 60 FPS
        elif len(players_with_lives) == 0:
            # Everyone ran out of lives - draw
            print("Draw - all players eliminated!")
            self.sound_manager.play('no_lives')
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
                score -= 10000  # Wall collision
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
            if (x, y) not in occupied_positions:
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
        # particle_type can be 'red', 'white', or 'rainbow'
        if particle_type == 'white' and self.particle_white_frames:
            self.particles.append(GifParticle(x, y, self.particle_white_frames))
        elif particle_type == 'rainbow' and self.particle_rainbow_frames:
            self.particles.append(GifParticle(x, y, self.particle_rainbow_frames))
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
                # Boss is 256x256, screen is 480 wide, 480 tall
                # Place it so it's in the bottom right corner
                boss_x = SCREEN_WIDTH - 256  # Right edge at screen edge
                boss_y = SCREEN_HEIGHT - 256  # Bottom edge at screen edge
                self.boss_position = (boss_x, boss_y)
                
                # Spawn 2 boss minions (hard AI CPU snakes)
                self.spawn_boss_minions()
                
                print("Boss spawning at {} seconds at position {}".format(self.boss_spawn_timer, self.boss_position))
            
            # Update boss animation
            if self.boss_spawned and self.boss_current_animation:
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
                            elif self.boss_current_animation == 'bossWormDeath1':
                                # Phase 1 finished - move to phase 2 (static image)
                                print("Death phase 1 complete, moving to phase 2 (static hold)")
                                self.boss_death_phase = 2
                                # Try to use bossWormDeath2, fallback to keeping current frame if not available
                                if 'bossWormDeath2' in self.boss_animations and self.boss_animations['bossWormDeath2']:
                                    self.boss_current_animation = 'bossWormDeath2'
                                    self.boss_animation_frame = 0
                                    self.boss_animation_counter = 0
                                else:
                                    # Fallback: keep last frame of phase 1
                                    self.boss_animation_frame = len(anim_frames) - 1
                                self.boss_death_timer = 180  # Hold for 3 seconds at 60 FPS
                            elif self.boss_current_animation == 'bossWormDeath3':
                                # Phase 3 finished - move to phase 4 (final static image)
                                print("Death phase 3 complete, moving to phase 4 (final freeze)")
                                self.boss_death_phase = 4
                                # Try to use bossWormDeath4, fallback to keeping current frame if not available
                                if 'bossWormDeath4' in self.boss_animations and self.boss_animations['bossWormDeath4']:
                                    self.boss_current_animation = 'bossWormDeath4'
                                    self.boss_animation_frame = 0
                                else:
                                    # Fallback: keep last frame of phase 3
                                    self.boss_animation_frame = len(anim_frames) - 1
                                # Start delay before level completion
                                self.boss_death_delay = 60  # Wait 1 second before victory
                            elif self.boss_current_animation == 'bossWormDeath2' or self.boss_current_animation == 'bossWormDeath4':
                                # Static images - stay on frame 0
                                self.boss_animation_frame = 0
                            else:
                                # Stay on last frame
                                self.boss_animation_frame = len(anim_frames) - 1
            
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
                            
                            # Check collision with player snake
                            if minion.body[0] == self.snake.body[0]:
                                # Minion head hit player head - player dies
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
                            elif minion.body[0] in self.snake.body[1:]:
                                # Minion head hit player's body - minion dies
                                minion.alive = False
                                self.boss_minion_respawn_timers[minion_idx] = 300  # 5 seconds at 60 FPS
                                self.sound_manager.play('eat')
                                print("Boss minion {} killed, will respawn in 5 seconds".format(minion_idx + 1))
                            
                            # Check if minion ate food
                            minion_head = minion.body[0]
                            for food_idx, (food_pos, food_type) in enumerate(self.food_items):
                                if minion_head == food_pos:
                                    # Minion ate the food!
                                    if food_type == 'worm':
                                        minion.grow()  # Grow the minion
                                        self.sound_manager.play('eat')
                                        # Remove eaten food
                                        self.food_items.pop(food_idx)
                                        # Spawn new worm
                                        self.spawn_adventure_food()
                                        print("Boss minion {} ate a worm and grew!".format(minion_idx + 1))
                                    elif food_type == 'bonus':
                                        minion.grow()
                                        self.sound_manager.play('bonus')
                                        self.food_items.pop(food_idx)
                                        self.bonus_fruits_collected += 1
                                        print("Boss minion {} ate a bonus fruit!".format(minion_idx + 1))
                                    break
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
                # Phase 1: If death animation 1 doesn't exist, auto-advance after short delay
                if self.boss_death_phase == 1:
                    if not ('bossWormDeath1' in self.boss_animations and self.boss_animations['bossWormDeath1']):
                        # No phase 1 animation, use a timer instead
                        if not hasattr(self, 'boss_death_phase1_timer'):
                            self.boss_death_phase1_timer = 60  # 1 second
                        if self.boss_death_phase1_timer > 0:
                            self.boss_death_phase1_timer -= 1
                        else:
                            # Auto-advance to phase 2
                            print("Phase 1 fallback timer complete, moving to phase 2")
                            self.boss_death_phase = 2
                            if 'bossWormDeath2' in self.boss_animations and self.boss_animations['bossWormDeath2']:
                                self.boss_current_animation = 'bossWormDeath2'
                                self.boss_animation_frame = 0
                            self.boss_death_timer = 180
                
                # Phase 2: Hold static image for 3 seconds
                if self.boss_death_phase == 2 and self.boss_death_timer > 0:
                    self.boss_death_timer -= 1
                    if self.boss_death_timer == 0:
                        # Move to phase 3
                        print("Death phase 2 complete, moving to phase 3 (particle effects)")
                        self.boss_death_phase = 3
                        # Try to use phase 3 animation, fallback to keeping current if not available
                        if 'bossWormDeath3' in self.boss_animations and self.boss_animations['bossWormDeath3']:
                            self.boss_current_animation = 'bossWormDeath3'
                            self.boss_animation_frame = 0
                            self.boss_animation_counter = 0
                            self.boss_animation_loop = False
                        else:
                            print("Warning: bossWormDeath3 not found, skipping to phase 4")
                            # Skip directly to phase 4
                            self.boss_death_phase = 4
                            if 'bossWormDeath4' in self.boss_animations and self.boss_animations['bossWormDeath4']:
                                self.boss_current_animation = 'bossWormDeath4'
                                self.boss_animation_frame = 0
                                self.boss_animation_counter = 0
                            self.boss_death_delay = 60
                
                # Phase 3: Spawn particles during animation
                if self.boss_death_phase == 3:
                    self.boss_death_particle_timer += 1
                    # Spawn particles every 3 frames
                    if self.boss_death_particle_timer % 3 == 0:
                        # Spawn white and red particles randomly on boss sprite
                        boss_x = self.boss_position[0]
                        boss_y = self.boss_position[1]
                        # Random position within boss sprite (256x256)
                        rand_x = boss_x + random.randint(20, 236)
                        rand_y = boss_y + random.randint(20, 236)
                        # Alternate between white and red particles
                        if random.random() < 0.5:
                            self.create_particles(rand_x, rand_y, None, None, particle_type='white')
                        else:
                            self.create_particles(rand_x, rand_y, RED, 8)
                
                # Phase 4: Wait before level completion
                if self.boss_death_phase == 4 and self.boss_death_delay > 0:
                    self.boss_death_delay -= 1
                    # Play victory jingle at 1 second mark (just before completion)
                    if self.boss_death_delay == 1:
                        print("Playing victory jingle...")
                        self.music_manager.play_victory_jingle()
                    if self.boss_death_delay == 0:
                        # Trigger level completion
                        print("Boss battle complete! Transitioning to level complete screen")
                        self.sound_manager.play('level_up')
                        self.state = GameState.LEVEL_COMPLETE
            
            # Update spewtum projectiles
            self.spewtums = [s for s in self.spewtums if s.alive]
            for spewtum in self.spewtums:
                spewtum.update()
                
                # Check collision with player snake
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
            
            # Periodic isotope spawning for boss battles
            if self.boss_spawned and hasattr(self, 'isotope_spawn_timer'):
                self.isotope_spawn_timer += 1
                if self.isotope_spawn_timer >= self.isotope_spawn_interval:
                    # Check if there's already an isotope on the field
                    has_isotope = any(food_type == 'isotope' for _, food_type in self.food_items)
                    if not has_isotope:
                        # Spawn a new isotope
                        self.spawn_isotope()
                    # Reset timer
                    self.isotope_spawn_timer = 0
        
        # Handle multiplayer end timer (delay after last player dies)
        if hasattr(self, 'multiplayer_end_timer') and self.multiplayer_end_timer > 0:
            self.multiplayer_end_timer -= 1
            if self.multiplayer_end_timer == 0:
                # Timer expired, transition to game over
                self.music_manager.play_game_over_music()
                self.state = GameState.GAME_OVER
                self.game_over_timer = self.game_over_delay
        
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
        
        # Handle game over timer countdown
        if self.state == GameState.GAME_OVER and self.game_over_timer > 0:
            self.game_over_timer -= 1
            if self.game_over_timer == 0:
                # Timer expired, transition to appropriate screen
                # Only check for high score in endless mode, not adventure mode
                if self.game_mode != "adventure" and self.is_high_score(self.score):
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
                        self.boss_minion_respawn_timers[minion_idx] = 300  # 5 seconds respawn
                        self.sound_manager.play('die')
                        # Create particles at hit location
                        hit_x = bullet_pos[0] * GRID_SIZE + GRID_SIZE // 2
                        hit_y = bullet_pos[1] * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
                        self.create_particles(hit_x, hit_y, RED, 15)
                        print("Boss minion {} headshot! Respawning in 5 seconds.".format(minion_idx + 1))
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
                            self.boss_minion_respawn_timers[minion_idx] = 300
                            self.sound_manager.play('die')
                            print("Boss minion {} destroyed! Respawning in 5 seconds.".format(minion_idx + 1))
                        break
        
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
                
                # Check if bullet hit the boss sprite area (256x256 at boss_position)
                bullet_pixel_x = bullet.pixel_x
                bullet_pixel_y = bullet.pixel_y - GAME_OFFSET_Y  # Adjust for HUD offset
                
                boss_left = self.boss_position[0]
                boss_right = self.boss_position[0] + 256
                boss_top = self.boss_position[1]
                boss_bottom = self.boss_position[1] + 256
                
                if (boss_left <= bullet_pixel_x <= boss_right and
                    boss_top <= bullet_pixel_y <= boss_bottom):
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
                        # Start death animation phase 1
                        self.boss_death_phase = 1
                        # Try to use death animation, fallback to idle if not available
                        if 'bossWormDeath1' in self.boss_animations and self.boss_animations['bossWormDeath1']:
                            self.boss_current_animation = 'bossWormDeath1'
                            self.boss_animation_loop = False  # Play once
                        else:
                            # Fallback: keep showing idle animation frozen on last frame
                            print("Warning: bossWormDeath1 not found, using fallback")
                            # Don't change animation, just freeze current one
                            self.boss_animation_loop = False
                        self.boss_animation_frame = 0
                        self.boss_animation_counter = 0  # Reset animation counter for smooth playback
                        # Stop attacking
                        self.boss_is_attacking = False
                        # Fade out music over 2 seconds
                        pygame.mixer.music.fadeout(2000)  # 2000ms = 2 seconds
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
                        # Play both death sounds simultaneously
                        self.sound_manager.play('bossWormDeath')
                        self.sound_manager.play('bossWormDeath2')
                    
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
                        for enemy in self.enemies:
                            if enemy.alive and enemy.enemy_type == 'enemy_wall':
                                if head == (enemy.grid_x, enemy.grid_y):
                                    hit_wall = True
                                    break
                        # Check self-collision
                        if snake.body[0] in snake.body[1:]:
                            hit_wall = True
                    else:
                        # Endless/multiplayer mode - check boundary walls
                        hit_wall = snake.check_collision(wrap_around=False)
                    
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
            # Single player mode - speed based on level
            move_interval = max(1, 16 - self.level // 2)
            
            if self.move_timer >= move_interval:
                self.move_timer = 0
                self.snake.move()
                
                # Check collision (wall collision and self-collision) - single player
                head = self.snake.body[0]
                hit_wall = False
                
                # Check if player entered the boss zone (lower right quadrant)
                if hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned:
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
                    # In endless mode, check boundary walls and self-collision
                    hit_wall = self.snake.check_collision(wrap_around=False)
                
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
                            enemy.update(self.snake.body, self.level_walls, self.food_items)
                            
                            # Update enemy animation
                            if enemy.enemy_type.startswith('enemy_ant') and self.ant_frames:
                                # Ants only animate when moving
                                enemy.update_animation(len(self.ant_frames), self.ant_animation_speed)
                            elif enemy.enemy_type.startswith('enemy_spider') and self.spider_frames:
                                # Spiders only animate when moving
                                enemy.update_animation(len(self.spider_frames), self.spider_animation_speed)
                            elif enemy.enemy_type.startswith('enemy_wasp') and self.wasp_frames:
                                # Wasps animate freely every frame (rapid wing flapping)
                                enemy.animation_frame = (enemy.animation_frame + 1) % len(self.wasp_frames)
                            
                            # Check collision with snake
                            collision_type = enemy.check_collision_with_snake(self.snake.body[0], self.snake.body)
                            
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
                                self.create_particles(enemy.grid_x * GRID_SIZE + GRID_SIZE // 2,
                                                    enemy.grid_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    None, None, particle_type='white')
        
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
                            self.sound_manager.play('die')
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
            if self.move_timer == 0:  # Only check after movement
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
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    YELLOW, 8)
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
                                                    NEON_CYAN, 12)
                                # Remove diamond from list
                                self.food_items.pop(i)
                                # Diamonds don't grow snake or count toward completion
                            elif food_type == 'isotope':
                                # Isotope collectible - grants shooting ability and 10 segments
                                self.sound_manager.play('powerup')
                                self.snake.can_shoot = True
                                self.snake.grow(10)  # Grant 10 segments
                                fx, fy = food_pos
                                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                                    NEON_PURPLE, 15)
                                # Remove isotope from list
                                self.food_items.pop(i)
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
                        # Play victory jingle
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
                pygame.quit()
                exit()
        
        keys = pygame.key.get_pressed()
        
        if self.state == GameState.EGG_HATCHING:
            # Wait for player to choose a direction to hatch
            if keys[pygame.K_UP]:
                self.hatch_egg(Direction.UP)
            elif keys[pygame.K_DOWN]:
                self.hatch_egg(Direction.DOWN)
            elif keys[pygame.K_LEFT]:
                self.hatch_egg(Direction.LEFT)
            elif keys[pygame.K_RIGHT]:
                self.hatch_egg(Direction.RIGHT)
        elif self.state == GameState.PLAYING:
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
                            # Play shoot sound (using blip_select as placeholder)
                            self.sound_manager.play('blip_select')
                            # If segments are now 3 or less, lose shooting ability
                            if len(self.snake.body) <= 3:
                                self.snake.can_shoot = False
            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                # Only allow input after the 3-second timer expires
                if self.game_over_timer == 0 and event.key == pygame.K_RETURN:
                    if self.is_multiplayer:
                        # Go back to multiplayer lobby
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
                        # Returning to level select menu - ensure theme music is playing
                        if not self.music_manager.theme_mode and not pygame.mixer.music.get_busy():
                            self.music_manager.play_theme()
                    else:
                        self.next_level()
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
                        # Same Screen - Go to player lobby
                        self.sound_manager.play('blip_select')
                        self.is_multiplayer = True
                        self.state = GameState.MULTIPLAYER_LOBBY
                        self.setup_multiplayer_game()
                    elif self.multiplayer_menu_selection == 1:
                        # Local Network - Coming soon
                        pass
                    elif self.multiplayer_menu_selection == 2:
                        # Back to main menu
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MENU
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.MULTIPLAYER_LOBBY:
                if event.key == pygame.K_UP:
                    self.lobby_selection = (self.lobby_selection - 1) % 7  # 3 settings + 4 players
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.lobby_selection = (self.lobby_selection + 1) % 7
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    direction = 1 if event.key == pygame.K_RIGHT else -1
                    self.change_lobby_setting(self.lobby_selection, direction)
                elif event.key == pygame.K_RETURN:
                    # Start the multiplayer game directly (no difficulty select)
                    self.sound_manager.play('start_game')
                    self.music_manager.stop_game_over_music()
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play('blip_select')
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
            if self.state == GameState.MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    self.select_menu_option()
            elif self.state == GameState.SINGLE_PLAYER_MENU:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    self.select_single_player_option()
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.ADVENTURE_LEVEL_SELECT:
                if button == GamepadButton.BTN_START or button == GamepadButton.BTN_A:
                    level_num = self.adventure_level_selection + 1
                    # Only allow playing unlocked levels
                    if self.is_level_unlocked(level_num):
                        if self.load_level(level_num):
                            self.reset_game()
                            self.state = GameState.EGG_HATCHING
                    else:
                        # Play error sound or do nothing if level is locked
                        self.sound_manager.play('blip_select')
                        self.score = 0
                        self.level = level_num
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.SINGLE_PLAYER_MENU
            elif self.state == GameState.PLAYING:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                # Only allow input after the 3-second timer expires
                if self.game_over_timer == 0 and button == GamepadButton.BTN_START:
                    if self.is_multiplayer:
                        # Go back to multiplayer lobby
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
                    else:
                        self.next_level()
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
                        # Same Screen - Go to player lobby
                        self.sound_manager.play('blip_select')
                        self.is_multiplayer = True
                        self.state = GameState.MULTIPLAYER_LOBBY
                        self.setup_multiplayer_game()
                    elif self.multiplayer_menu_selection == 1:
                        # Local Network - Coming soon
                        pass
                    elif self.multiplayer_menu_selection == 2:
                        # Back to main menu
                        self.sound_manager.play('blip_select')
                        self.state = GameState.MENU
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
                    self.state = GameState.MENU
            elif self.state == GameState.MULTIPLAYER_LOBBY:
                if button == GamepadButton.BTN_START:
                    # Start the multiplayer game
                    self.sound_manager.play('start_game')
                    self.state = GameState.DIFFICULTY_SELECT
                elif button == GamepadButton.BTN_B:
                    self.sound_manager.play('blip_select')
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
            # High Scores
            self.state = GameState.HIGH_SCORES
        elif self.menu_selection == 3:
            # Quit
            pygame.quit()
            exit()
    
    def select_single_player_option(self):
        """Handle single player submenu selection"""
        if self.single_player_selection == 0:
            # Adventure Mode - Go to level selection
            self.sound_manager.play('blip_select')
            self.game_mode = "adventure"
            self.is_multiplayer = False
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
            if 'enemies' in self.current_level_data:
                for enemy_data in self.current_level_data['enemies']:
                    enemy = Enemy(enemy_data['x'], enemy_data['y'], enemy_data['type'])
                    self.enemies.append(enemy)
            
            # Clear all boss-related entities from previous attempts
            self.boss_minions = []
            self.boss_minion_respawn_timers = {}
            self.spewtums = []
            self.bullets = []
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
                self.boss_death_delay = 0
                self.boss_death_phase = 0
                self.boss_death_timer = 0
                self.boss_death_particle_timer = 0
                if hasattr(self, 'boss_death_phase1_timer'):
                    del self.boss_death_phase1_timer
                # Reset super attack tracking
                self.boss_super_attacks_used = set()
                
                # If it's a wormBoss, play FinalBoss music instead of normal music
                if self.boss_data == 'wormBoss':
                    try:
                        boss_music_path = os.path.join(SCRIPT_DIR, 'sound', 'music', 'FinalBoss.mp3')
                        pygame.mixer.music.load(boss_music_path)
                        pygame.mixer.music.set_volume(0.9)
                        pygame.mixer.music.play(-1)  # Loop
                        self.music_manager.theme_mode = False
                        print("Playing FinalBoss music for boss battle")
                    except Exception as e:
                        print("Warning: Could not load FinalBoss.mp3: {}".format(e))
            else:
                self.boss_data = None
                self.boss_active = False
            
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
        elif selection >= 3 and selection <= 6:
            # Player slots
            player_idx = selection - 3
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
        
        self.level = 1
        self.lives = 3
        self.fruits_eaten_this_level = 0
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.particles = []
        self.egg_pieces = []
        
        # In multiplayer, skip egg hatching and go straight to playing
        if self.is_multiplayer:
            self.state = GameState.PLAYING
        else:
            # Don't reset snake yet - wait for egg hatching
            self.state = GameState.EGG_HATCHING
    
    def hatch_egg(self, direction):
        """Hatch the egg and spawn the snake in the chosen direction"""
        self.sound_manager.play('crack')
        
        # Reset snake with chosen direction
        # In adventure mode, use the level's starting position
        if self.game_mode == "adventure" and hasattr(self, 'current_level_data'):
            start_pos = tuple(self.current_level_data['starting_position'])
            self.snake.reset(spawn_pos=start_pos, direction=direction)
        else:
            self.snake.reset()
            self.snake.direction = direction
            self.snake.next_direction = direction
        
        # Create flying egg pieces
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
        
        # Reset boss egg respawn flag and timer
        if hasattr(self, 'boss_egg_is_respawn'):
            self.boss_egg_is_respawn = False
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
        self.state = GameState.PLAYING
        # If theme music was playing, switch to gameplay music
        if self.music_manager.theme_mode:
            pygame.mixer.music.stop()
            self.music_manager.play_next()
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            
            self.handle_input()
            
            # Handle splash screen timer
            if self.state == GameState.SPLASH:
                current_time = pygame.time.get_ticks()
                if current_time - self.splash_start_time >= self.splash_duration:
                    # Transition to menu after 3 seconds
                    self.state = GameState.MENU
            
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
                        # Only check for high score in endless mode, not adventure mode
                        if self.game_mode != "adventure" and self.is_high_score(self.score):
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
        
        pygame.quit()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.SPLASH:
            self.draw_splash()
        elif self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.SINGLE_PLAYER_MENU:
            self.draw_single_player_menu()
        elif self.state == GameState.ADVENTURE_LEVEL_SELECT:
            self.draw_adventure_level_select()
        elif self.state == GameState.MULTIPLAYER_MENU:
            self.draw_multiplayer_menu()
        elif self.state == GameState.MULTIPLAYER_LOBBY:
            self.draw_multiplayer_lobby()
        elif self.state == GameState.EGG_HATCHING:
            self.draw_egg_hatching()
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
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+3, 323 + i * 60))
            
            # Draw text
            self.screen.blit(text, text_rect)
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 320 + i * 60))
            
            # Draw text
            self.screen.blit(text, text_rect)
        
        # Draw Tweetrix logo at bottom left
        if self.tweetrix_logo:
            logo_x = 10  # 10 pixels from left edge
            logo_y = SCREEN_HEIGHT - self.tweetrix_logo.get_height() - 10  # 10 pixels from bottom
            self.screen.blit(self.tweetrix_logo, (logo_x, logo_y))
    
    def draw_single_player_menu(self):
        """Draw the single player mode selection menu."""
        # Use title screen or background
        if self.title_screen:
            self.screen.blit(self.title_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title
        title = self.font_large.render("SINGLE PLAYER", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 103))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("SINGLE PLAYER", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.single_player_options):
            color = NEON_YELLOW if i == self.single_player_selection else NEON_CYAN
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+3, 253 + i * 60))
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 60))
            self.screen.blit(text, text_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press B to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 452))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press B to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
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
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 33))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("LEVEL SELECT", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Draw level grid (8 columns x 4 rows for 32 levels)
        cols = 8
        rows = 4
        cell_size = 50
        spacing = 10
        start_x = (SCREEN_WIDTH - (cols * cell_size + (cols - 1) * spacing)) // 2
        start_y = 80
        
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
        info_y = start_y + rows * (cell_size + spacing) + 20
        
        info_text = self.font_medium.render("Level {}".format(selected_level), True, BLACK)
        info_rect = info_text.get_rect(center=((SCREEN_WIDTH // 2)+2, info_y + 2))
        self.screen.blit(info_text, info_rect)
        info_text = self.font_medium.render("Level {}".format(selected_level), True, NEON_GREEN)
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, info_y))
        self.screen.blit(info_text, info_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press Start to begin", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 452))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press Start to begin", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(hint_text, hint_rect)
    
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
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 78))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("MULTIPLAYER", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 75))
        self.screen.blit(title, title_rect)
        
        # Render menu options
        for i, option in enumerate(self.multiplayer_menu_options):
            if i == 1:  # "Coming Soon" option
                color = DARK_GRAY if i == self.multiplayer_menu_selection else DARK_GRAY
            else:
                color = NEON_YELLOW if i == self.multiplayer_menu_selection else NEON_CYAN
            
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+3, 280 + i * 55))
            self.screen.blit(text, text_rect)
            
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 277 + i * 55))
            self.screen.blit(text, text_rect)
        
        # Hint text
        hint_text = self.font_small.render("Press B to go back", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 452))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Press B to go back", True, NEON_PURPLE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
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
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 34))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("SETUP", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 32))
        self.screen.blit(title, title_rect)
        
        y = 80  # Start higher to fit everything
        center_x = SCREEN_WIDTH // 2
        
        # Settings section with visual icons
        # Lives setting with egg icons
        is_selected = (self.lobby_selection == 0)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "Lives" label
        label = self.font_small.render("Lives:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 100 + 2, y + 2))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("Lives:", True, color)
        label_rect = label.get_rect(midright=(center_x - 100, y))
        self.screen.blit(label, label_rect)
        
        # Draw egg icons for lives (show all eggs, not capped at 5)
        lives = self.lobby_settings['lives']
        egg_size = 28  # Slightly smaller to fit better
        egg_spacing = 32
        start_x = center_x - 80
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
        
        y += 40  # Reduced spacing
        
        # Item Spawn setting with apple icons (1-3 apples)
        is_selected = (self.lobby_selection == 1)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "Item Spawn" label
        label = self.font_small.render("Item Spawn:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 100 + 2, y + 2))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("Item Spawn:", True, color)
        label_rect = label.get_rect(midright=(center_x - 100, y))
        self.screen.blit(label, label_rect)
        
        # Draw apple icons (1=Low, 2=Normal, 3=High) using bonus.png
        item_freq = self.lobby_settings['item_frequency']
        num_apples = item_freq + 1  # 0→1, 1→2, 2→3
        apple_size = 28  # Smaller to match eggs
        apple_spacing = 32
        start_x = center_x - 80
        
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
        
        y += 40  # Reduced spacing
        
        # CPU Difficulty with star rating
        is_selected = (self.lobby_selection == 2)
        color = NEON_YELLOW if is_selected else NEON_GREEN
        
        # Draw "CPU Difficulty" label
        label = self.font_small.render("CPU Level:", True, BLACK)
        label_rect = label.get_rect(midright=(center_x - 100 + 2, y + 2))
        self.screen.blit(label, label_rect)
        label = self.font_small.render("CPU Level:", True, color)
        label_rect = label.get_rect(midright=(center_x - 100, y))
        self.screen.blit(label, label_rect)
        
        # Draw star rating (4 stars total: easy, medium, hard, brutal)
        difficulty_level = self.lobby_settings['cpu_difficulty']
        star_spacing = 38  # Adjusted for smaller icons
        start_x = center_x - 80
        star_names = ['easy', 'medium', 'hard', 'brutal']
        
        for i, star_name in enumerate(star_names):
            # Show filled star up to difficulty level, empty after
            if i <= difficulty_level:
                star_img = self.star_icons.get(star_name)
            else:
                star_img = self.star_icons.get('starEmpty')
            
            if star_img:
                # Scale star down slightly for better fit
                star_scaled = pygame.transform.scale(star_img, (36, 36))
                self.screen.blit(star_scaled, (start_x + i * star_spacing, y - 18))
        
        y += 45  # Reduced spacing
        
        # Player slots (starting at selection index 3)
        # Use hatchling heads with input icons
        head_size = 48  # Reduced from 64 to fit better
        for i in range(4):
            player_name = self.player_names[i]
            player_color = self.player_colors[i]
            slot_type = self.player_slots[i]
            
            is_selected = (self.lobby_selection == 3 + i)
            
            # Draw player hatchling head
            if self.snake_head_frames_all and len(self.snake_head_frames_all) > i:
                if self.snake_head_frames_all[i]:
                    head = self.snake_head_frames_all[i][0]  # First frame
                    head_scaled = pygame.transform.scale(head, (head_size, head_size))
                    
                    # Dim if OFF
                    if slot_type == 'off':
                        head_scaled = head_scaled.copy()
                        head_scaled.set_alpha(80)
                    
                    head_x = center_x - 130
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
            rect = text.get_rect(left=center_x - 50 + 2, centery=y + 2)
            self.screen.blit(text, rect)
            text = self.font_small.render(player_name, True, name_color)
            rect = text.get_rect(left=center_x - 50, centery=y)
            self.screen.blit(text, rect)
            
            # Draw input icon (keyboard/gamepad/robot/off)
            icon = None
            if slot_type == 'player':
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
                icon_x = center_x + 70
                icon_y = y - 18  # Adjusted for smaller icons
                # Scale icon down to match other elements
                icon_scaled = pygame.transform.scale(icon, (36, 36))
                self.screen.blit(icon_scaled, (icon_x, icon_y))
            
            y += 58  # Increased spacing to prevent overlap (head_size is 48)
        
        # Instructions - positioned at bottom
        y = SCREEN_HEIGHT - 60  # Start from bottom up
        hints = [
            "UP/DOWN: Navigate | LEFT/RIGHT: Change",
            "START: Begin Game",
            "B: Back to Menu"
        ]
        for hint in hints:
            text = self.font_small.render(hint, True, BLACK)
            rect = text.get_rect(center=((SCREEN_WIDTH // 2)+2, y+2))
            self.screen.blit(text, rect)
            text = self.font_small.render(hint, True, NEON_CYAN)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, rect)
            y += 22  # Slightly tighter spacing for instructions
    
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
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 78))
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
        start_y = 280
        spacing = 40  # Increased spacing between options
        
        for i, option in enumerate(self.difficulty_options):
            color = NEON_YELLOW if i == self.difficulty_selection else NEON_GREEN
            
            # draw shadow
            text = self.font_medium.render(option, True, BLACK)
            text_rect = text.get_rect(center=((SCREEN_WIDTH // 2)+3, start_y + i * spacing+3))
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
        desc_rect = desc_text.get_rect(center=((SCREEN_WIDTH // 2)+2, 452))
        self.screen.blit(desc_text, desc_rect)
        # Draw description text based on difficulty selected
        desc_text = self.font_small.render(descriptions[self.difficulty_selection], True, NEON_PURPLE)
        desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(desc_text, desc_rect)


    
    def draw_egg_hatching(self):
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
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
        
        # Draw food
        if self.game_mode == "adventure" and self.food_items:
            # Draw worms and bonus fruits from food_items in Adventure mode
            for food_pos, food_type in self.food_items:
                fx, fy = food_pos
                if food_type == 'worm' and self.worm_frames:
                    worm_img = self.worm_frames[self.worm_frame_index]
                    self.screen.blit(worm_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
                elif food_type == 'bonus' and self.bonus_img:
                    self.screen.blit(self.bonus_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
            
            # Draw enemies in Adventure mode
            if hasattr(self, 'enemies'):
                for enemy in self.enemies:
                    if enemy.alive:
                        render_x, render_y = enemy.get_render_position()
                        
                        # Skip wasps here - they're drawn on top later
                        if enemy.enemy_type.startswith('enemy_wasp'):
                            continue
                        
                        # Draw enemy using sprite if available
                        enemy_frames = None
                        if enemy.enemy_type.startswith('enemy_ant') and self.ant_frames:
                            enemy_frames = self.ant_frames
                        elif enemy.enemy_type.startswith('enemy_spider') and self.spider_frames:
                            enemy_frames = self.spider_frames
                        
                        if enemy_frames:
                            enemy_img = enemy_frames[enemy.animation_frame]
                            # Rotate sprite to match direction (angle: 0=right, 90=down, 180=left, 270=up)
                            # pygame.transform.rotate rotates counter-clockwise, so negate the angle
                            rotated_img = pygame.transform.rotate(enemy_img, -enemy.angle)
                            # Get rect to center the rotated image on the grid position
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
        elif self.food_pos:
            # Draw single food in Endless mode
            fx, fy = self.food_pos
            if self.worm_frames:
                worm_img = self.worm_frames[self.worm_frame_index]
                self.screen.blit(worm_img, (fx * GRID_SIZE, fy * GRID_SIZE + GAME_OFFSET_Y))
        
        # Draw bonus food if present
        if self.bonus_food_pos:
            bx, by = self.bonus_food_pos
            if self.bonus_img:
                self.screen.blit(self.bonus_img, (bx * GRID_SIZE, by * GRID_SIZE + GAME_OFFSET_Y))
        
        # Draw death particles (from previous life)
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw flying egg pieces
        for piece in self.egg_pieces:
            piece.draw(self.screen)
        
        # Draw egg at starting position (adventure mode) or center (endless mode)
        if self.egg_img:
            if self.game_mode == "adventure" and hasattr(self, 'current_level_data'):
                # Use level's starting position
                egg_x, egg_y = self.current_level_data['starting_position']
                egg_pixel_x = egg_x * GRID_SIZE
                egg_pixel_y = egg_y * GRID_SIZE + GAME_OFFSET_Y
            else:
                # Default to center for endless mode
                egg_pixel_x = SCREEN_WIDTH // 2 - GRID_SIZE
                egg_pixel_y = SCREEN_HEIGHT // 2 - GRID_SIZE
            self.screen.blit(self.egg_img, (egg_pixel_x, egg_pixel_y))
        
        # Draw HUD
        # Draw HUD text (background now part of bg.png)
        # Left side: Score with label
        score_label = self.font_small.render("SCORE:", True, BLACK)
        self.screen.blit(score_label, (10, 4))
        score_label = self.font_small.render("SCORE:", True, NEON_YELLOW)
        self.screen.blit(score_label, (8, 2))
        score_value = self.font_small.render("{}".format(self.score), True, BLACK)
        self.screen.blit(score_value, (100, 4))
        score_value = self.font_small.render("{}".format(self.score), True, WHITE)
        self.screen.blit(score_value, (98, 2))
        
        level_label = self.font_small.render("LEVEL:", True, BLACK)
        level_value = self.font_small.render("{}".format(self.level), True, BLACK)
        level_label_rect = level_label.get_rect(center=(SCREEN_WIDTH // 2 + 62, SCREEN_HEIGHT - 7))
        level_value_rect = level_value.get_rect(center=(SCREEN_WIDTH // 2 + 125, SCREEN_HEIGHT - 6))
        self.screen.blit(level_label, level_label_rect)
        self.screen.blit(level_value, level_value_rect)
        level_label = self.font_small.render("LEVEL:", True, NEON_YELLOW)
        level_value = self.font_small.render("{}".format(self.level), True, WHITE)
        level_label_rect = level_label.get_rect(center=(SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT - 9))
        level_value_rect = level_value.get_rect(center=(SCREEN_WIDTH // 2 + 123, SCREEN_HEIGHT - 8))
        self.screen.blit(level_label, level_label_rect)
        self.screen.blit(level_value, level_value_rect)
        
        fruits_label = self.font_small.render("WORMS:", True, BLACK)
        fruits_label_rect = fruits_label.get_rect(center=(SCREEN_WIDTH // 2 + 62, 16))
        self.screen.blit(fruits_label, fruits_label_rect)
        fruits_label = self.font_small.render("WORMS:", True, NEON_YELLOW)
        fruits_label_rect = fruits_label.get_rect(center=(SCREEN_WIDTH // 2 + 60, 14))
        self.screen.blit(fruits_label, fruits_label_rect)

        # Show correct count based on game mode
        if self.game_mode == "adventure":
            worm_count_text = "{}/{}".format(self.worms_collected, self.worms_required)
        else:
            worm_count_text = "{}/12".format(self.fruits_eaten_this_level)
        
        fruits_value = self.font_small.render(worm_count_text, True, BLACK)
        fruits_value_rect = fruits_value.get_rect(center=(SCREEN_WIDTH // 2 + 135, 16))
        self.screen.blit(fruits_value, fruits_value_rect)
        fruits_value = self.font_small.render(worm_count_text, True, WHITE)
        fruits_value_rect = fruits_value.get_rect(center=(SCREEN_WIDTH // 2 + 133, 14))
        self.screen.blit(fruits_value, fruits_value_rect)
        
        
        # Lives with label
        lives_label = self.font_medium.render("LIVES", True, BLACK)
        lives_label_rect = lives_label.get_rect(center=((SCREEN_WIDTH // 2)+3, 63))
        self.screen.blit(lives_label, lives_label_rect)
        lives_label = self.font_medium.render("LIVES", True, NEON_YELLOW)
        lives_label_rect = lives_label.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(lives_label, lives_label_rect)
        lives_value = self.font_medium.render("{}".format(self.lives), True, BLACK)
        lives_value_rect = lives_value.get_rect(center=((SCREEN_WIDTH // 2)+3, 99))
        self.screen.blit(lives_value, lives_value_rect)
        lives_value = self.font_medium.render("{}".format(self.lives), True, WHITE)
        lives_value_rect = lives_value.get_rect(center=(SCREEN_WIDTH // 2, 96))
        self.screen.blit(lives_value, lives_value_rect)
        
        # Lives with label
        lives_label = self.font_small.render("LIVES:", True, BLACK)
        self.screen.blit(lives_label, (10, SCREEN_HEIGHT - 19))
        lives_label = self.font_small.render("LIVES:", True, NEON_YELLOW)
        self.screen.blit(lives_label, (8, SCREEN_HEIGHT - 21))
        lives_value = self.font_small.render("{}".format(self.lives), True, BLACK)
        self.screen.blit(lives_value, (85, SCREEN_HEIGHT - 19))
        lives_value = self.font_small.render("{}".format(self.lives), True, WHITE)
        self.screen.blit(lives_value, (83, SCREEN_HEIGHT - 21))

        # Draw instruction text (with timer if in boss mode respawn)
        instruction_text = "Press a direction to hatch!"
        if hasattr(self, 'boss_active') and self.boss_active and hasattr(self, 'boss_egg_is_respawn') and self.boss_egg_is_respawn:
            # Show countdown timer (5 seconds = 300 frames)
            time_left = max(0, (300 - getattr(self, 'egg_timer', 0)) // 60)
            instruction_text = "Choose direction! Auto-hatch in {}s".format(time_left)
        
        instruction = self.font_medium.render(instruction_text, True, BLACK)
        instruction_rect = instruction.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT - 37))
        self.screen.blit(instruction, instruction_rect)
        instruction = self.font_medium.render(instruction_text, True, NEON_YELLOW)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(instruction, instruction_rect)
    
    def draw_snake(self, snake, player_id):
        """Draw a single snake with its color-shifted graphics."""
        # Get interpolated positions for smooth movement
        # Calculate progress between frames for interpolation
        is_boss_minion = hasattr(snake, 'is_boss_minion') and snake.is_boss_minion
        
        if self.is_multiplayer or is_boss_minion:
            # Use snake's individual timer and interval (for multiplayer or boss minions)
            move_interval = max(1, snake.last_move_interval)
            progress = min(1.0, snake.move_timer / move_interval)
        else:
            # Single player - use global timer and level-based speed
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
        # Check if this is a boss minion
        is_boss_minion = hasattr(snake, 'is_boss_minion') and snake.is_boss_minion
        
        if is_boss_minion:
            # Use bad snake graphics for boss minions
            body_img = self.bad_snake_body_img
            head_img_static = self.bad_snake_head_img  # Static image for minions
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
                if body_img:
                    self.screen.blit(body_img, (int(pixel_x), int(pixel_y)))
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
                    # Draw isotope as a glowing purple atom symbol
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
                        if enemy.enemy_type.startswith('enemy_ant') and self.ant_frames:
                            enemy_frames = self.ant_frames
                        elif enemy.enemy_type.startswith('enemy_spider') and self.spider_frames:
                            enemy_frames = self.spider_frames
                        
                        if enemy_frames:
                            enemy_img = enemy_frames[enemy.animation_frame]
                            # Rotate sprite to match direction (angle: 0=right, 90=down, 180=left, 270=up)
                            # pygame.transform.rotate rotates counter-clockwise, so negate the angle
                            rotated_img = pygame.transform.rotate(enemy_img, -enemy.angle)
                            # Get rect to center the rotated image on the grid position
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
        
        # Draw boss on top of minions (even when defeated, for death animation)
        if self.boss_spawned and self.boss_current_animation:
            anim_frames = self.boss_animations.get(self.boss_current_animation, [])
            if anim_frames:
                # Clamp frame index to valid range
                frame_index = min(self.boss_animation_frame, len(anim_frames) - 1)
                boss_frame = anim_frames[frame_index]
                
                # Apply red flash if boss was recently damaged (not during death)
                if self.boss_damage_flash > 0 and not self.boss_defeated:
                    # Create a copy of the frame with red tint
                    flash_frame = boss_frame.copy()
                    # Create a red overlay surface
                    red_overlay = pygame.Surface(flash_frame.get_size(), pygame.SRCALPHA)
                    red_overlay.fill((255, 0, 0, 128))  # Semi-transparent red
                    flash_frame.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    self.screen.blit(flash_frame, self.boss_position)
                else:
                    self.screen.blit(boss_frame, self.boss_position)
            
            # Draw boss health bar (top-right corner) - hidden during egg hatching and final death phase
            show_health_bar = self.state != GameState.EGG_HATCHING
            if self.boss_defeated and self.boss_death_phase >= 4:
                show_health_bar = False  # Hide in final death phase
            
            if hasattr(self, 'boss_health') and hasattr(self, 'boss_max_health') and show_health_bar:
                # Health bar dimensions and position
                bar_width = 200
                bar_height = 20
                bar_x = SCREEN_WIDTH - bar_width - 10  # 10px from right edge
                bar_y = 10  # 10px from top
                
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
            # Single player - draw the main snake
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
            # Draw multiplayer player info - show each player's lives
            y_start = 2
            for snake in self.snakes:
                player_color = self.player_colors[snake.player_id] if snake.player_id < len(self.player_colors) else WHITE
                
                # Determine status
                if snake.player_id in self.respawning_players:
                    status_text = " (RESPAWNING)"
                elif not snake.alive and snake.lives <= 0:
                    status_text = " (OUT)"
                elif not snake.alive:
                    status_text = " (DEAD)"
                else:
                    status_text = ""
                
                # Player name and lives with hearts
                hearts = "♥" * snake.lives if snake.lives > 0 else "X"
                player_text = "P{}: {}{}".format(snake.player_id + 1, hearts, status_text)
                
                # Shadow
                text = self.font_small.render(player_text, True, BLACK)
                self.screen.blit(text, (10, y_start + 2))
                # Main text with player color
                text = self.font_small.render(player_text, True, player_color)
                self.screen.blit(text, (8, y_start))
                
                y_start += 22
        else:
            # Single player score - Left side: Score with label (hidden during boss battles)
            if not (hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned):
                score_label = self.font_small.render("SCORE:", True, BLACK)
                self.screen.blit(score_label, (10, 4))
                score_label = self.font_small.render("SCORE:", True, NEON_YELLOW)
                self.screen.blit(score_label, (8, 2))
                score_value = self.font_small.render("{}".format(self.score), True, BLACK)
                self.screen.blit(score_value, (100, 4))
                score_value = self.font_small.render("{}".format(self.score), True, WHITE)
                self.screen.blit(score_value, (98, 2))
        
        # Single player HUD elements (level, worms counter) - hidden during boss battles
        if not self.is_multiplayer and not (hasattr(self, 'boss_active') and self.boss_active and self.boss_spawned):
            # Center-left: Level
            level_label = self.font_small.render("LEVEL:", True, BLACK)
            level_value = self.font_small.render("{}".format(self.level), True, BLACK)
            level_label_rect = level_label.get_rect(center=(SCREEN_WIDTH // 2 + 62, SCREEN_HEIGHT - 7))
            level_value_rect = level_value.get_rect(center=(SCREEN_WIDTH // 2 + 125, SCREEN_HEIGHT - 6))
            self.screen.blit(level_label, level_label_rect)
            self.screen.blit(level_value, level_value_rect)
            level_label = self.font_small.render("LEVEL:", True, NEON_YELLOW)
            level_value = self.font_small.render("{}".format(self.level), True, WHITE)
            level_label_rect = level_label.get_rect(center=(SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT - 9))
            level_value_rect = level_value.get_rect(center=(SCREEN_WIDTH // 2 + 123, SCREEN_HEIGHT - 8))
            self.screen.blit(level_label, level_label_rect)
            self.screen.blit(level_value, level_value_rect)
            
            fruits_label = self.font_small.render("WORMS:", True, BLACK)
            fruits_label_rect = fruits_label.get_rect(center=(SCREEN_WIDTH // 2 + 62, 16))
            self.screen.blit(fruits_label, fruits_label_rect)
            fruits_label = self.font_small.render("WORMS:", True, NEON_YELLOW)
            fruits_label_rect = fruits_label.get_rect(center=(SCREEN_WIDTH // 2 + 60, 14))
            self.screen.blit(fruits_label, fruits_label_rect)

            # Show correct count based on game mode
            if self.game_mode == "adventure":
                worm_count_text = "{}/{}".format(self.worms_collected, self.worms_required)
            else:
                worm_count_text = "{}/12".format(self.fruits_eaten_this_level)
            
            fruits_value = self.font_small.render(worm_count_text, True, BLACK)
            fruits_value_rect = fruits_value.get_rect(center=(SCREEN_WIDTH // 2 + 135, 16))
            self.screen.blit(fruits_value, fruits_value_rect)
            fruits_value = self.font_small.render(worm_count_text, True, WHITE)
            fruits_value_rect = fruits_value.get_rect(center=(SCREEN_WIDTH // 2 + 133, 14))
            self.screen.blit(fruits_value, fruits_value_rect)
            
            # Show coins in adventure mode
            if self.game_mode == "adventure":
                coins_label = self.font_small.render("COINS:", True, BLACK)
                coins_label_rect = coins_label.get_rect(center=(SCREEN_WIDTH - 60, 16))
                self.screen.blit(coins_label, coins_label_rect)
                coins_label = self.font_small.render("COINS:", True, YELLOW)
                coins_label_rect = coins_label.get_rect(center=(SCREEN_WIDTH - 62, 14))
                self.screen.blit(coins_label, coins_label_rect)
                
                coins_value = self.font_small.render("{}".format(getattr(self, 'total_coins', 0)), True, BLACK)
                coins_value_rect = coins_value.get_rect(center=(SCREEN_WIDTH - 10, 16))
                self.screen.blit(coins_value, coins_value_rect)
                coins_value = self.font_small.render("{}".format(getattr(self, 'total_coins', 0)), True, WHITE)
                coins_value_rect = coins_value.get_rect(center=(SCREEN_WIDTH - 12, 14))
                self.screen.blit(coins_value, coins_value_rect)
        
        # Lives with label (only in single player) - hidden during egg hatching in boss mode
        if not self.is_multiplayer:
            # Hide lives HUD during egg hatching in boss battles
            show_lives = True
            if hasattr(self, 'boss_active') and self.boss_active and self.state == GameState.EGG_HATCHING:
                show_lives = False
            
            if show_lives:
                lives_label = self.font_small.render("LIVES:", True, BLACK)
                self.screen.blit(lives_label, (10, SCREEN_HEIGHT - 19))
                lives_label = self.font_small.render("LIVES:", True, NEON_YELLOW)
                self.screen.blit(lives_label, (8, SCREEN_HEIGHT - 21))
                lives_value = self.font_small.render("{}".format(self.lives), True, BLACK)
                self.screen.blit(lives_value, (85, SCREEN_HEIGHT - 19))
                lives_value = self.font_small.render("{}".format(self.lives), True, WHITE)
                self.screen.blit(lives_value, (83, SCREEN_HEIGHT - 21))

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(DARK_BG)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, NEON_YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)
        
        hint_text = self.font_small.render("Start to resume", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_game_over(self):
        # Draw game over screen image (includes "GAME OVER" text)
        if self.gameover_screen:
            self.screen.blit(self.gameover_screen, (0, 0))
        elif self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # During the 3-second timer, only show the game over image
        if self.game_over_timer > 0:
            # Just show the image, no additional text needed during timer
            if not self.gameover_screen:
                # Fallback if image not loaded
                over_text = self.font_large.render("GAME OVER", True, NEON_PINK)
                over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(over_text, over_rect)
        else:
            # After timer expires, show score and level info
            # No "GAME OVER" text needed - it's in the background image
            if not self.gameover_screen:
                # Fallback if image not loaded
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
                else:
                    winner_text = "Draw!"
                    color = NEON_YELLOW
                
                text = self.font_large.render(winner_text, True, BLACK)
                rect = text.get_rect(center=((SCREEN_WIDTH // 2) + 3, 180 + 3))
                self.screen.blit(text, rect)
                text = self.font_large.render(winner_text, True, color)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, 180))
                self.screen.blit(text, rect)
                
                # Show final player status
                y_offset = 230
                for snake in self.snakes:
                    if snake.lives > 0:
                        status = "WINNER ({} lives)".format(snake.lives)
                    else:
                        status = "ELIMINATED"
                    score_text = "{}: {}".format(self.player_names[snake.player_id], status)
                    text = self.font_medium.render(score_text, True, BLACK)
                    rect = text.get_rect(center=((SCREEN_WIDTH // 2) + 2, y_offset + 2))
                    self.screen.blit(text, rect)
                    text = self.font_medium.render(score_text, True, self.player_colors[snake.player_id])
                    rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                    self.screen.blit(text, rect)
                    y_offset += 40
            else:
                # Single player results
                score_text = self.font_medium.render("Score: {}".format(self.score), True, NEON_CYAN)
                score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
                self.screen.blit(score_text, score_rect)
                
                level_text = self.font_medium.render("Level: {}".format(self.level), True, NEON_GREEN)
                level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 240))
                self.screen.blit(level_text, level_rect)
            
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
            self.screen.blit(hint_text, hint_rect)
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(DARK_BG)
        self.screen.blit(overlay, (0, 0))
        
        if self.game_mode == "adventure" and not self.is_multiplayer:
            # Adventure mode victory screen with completion percentage
            complete_text = self.font_large.render("VICTORY!", True, BLACK)
            complete_rect = complete_text.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT // 2 - 90+3))
            self.screen.blit(complete_text, complete_rect)
            complete_text = self.font_large.render("VICTORY!", True, NEON_YELLOW)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 90))
            self.screen.blit(complete_text, complete_rect)
            
            # Show completion percentage
            if hasattr(self, 'completion_percentage'):
                percent_text = "{}% Complete".format(self.completion_percentage)
                percent_label = self.font_large.render(percent_text, True, BLACK)
                percent_rect = percent_label.get_rect(center=((SCREEN_WIDTH // 2)+2, SCREEN_HEIGHT // 2 - 35+2))
                self.screen.blit(percent_label, percent_rect)
                percent_label = self.font_large.render(percent_text, True, NEON_GREEN)
                percent_rect = percent_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 35))
                self.screen.blit(percent_label, percent_rect)
            
            # Show breakdown
            y_pos = SCREEN_HEIGHT // 2 + 10
            
            # Segments
            if hasattr(self, 'final_segments'):
                segments_text = "Segments: {}".format(self.final_segments)
                segments_label = self.font_medium.render(segments_text, True, BLACK)
                segments_rect = segments_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
                self.screen.blit(segments_label, segments_rect)
                segments_label = self.font_medium.render(segments_text, True, NEON_CYAN)
                segments_rect = segments_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(segments_label, segments_rect)
                y_pos += 35
            
            # Worms collected
            worms_text = "Worms: {}/{}".format(self.worms_collected, self.worms_required)
            worms_label = self.font_medium.render(worms_text, True, BLACK)
            worms_rect = worms_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
            self.screen.blit(worms_label, worms_rect)
            worms_label = self.font_medium.render(worms_text, True, WHITE)
            worms_rect = worms_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.screen.blit(worms_label, worms_rect)
            y_pos += 35
            
            # Bonus fruits collected
            if hasattr(self, 'total_bonus_fruits') and self.total_bonus_fruits > 0:
                bonus_text = "Bonus: {}/{}".format(self.bonus_fruits_collected, self.total_bonus_fruits)
                bonus_label = self.font_medium.render(bonus_text, True, BLACK)
                bonus_rect = bonus_label.get_rect(center=((SCREEN_WIDTH // 2)+2, y_pos+2))
                self.screen.blit(bonus_label, bonus_rect)
                bonus_label = self.font_medium.render(bonus_text, True, NEON_ORANGE)
                bonus_rect = bonus_label.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(bonus_label, bonus_rect)
                y_pos += 35
            
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
            hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT - 60+3))
            self.screen.blit(hint_text, hint_rect)
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
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
                y_offset += 25
            
            hint_text = self.font_small.render("Start to continue", True, BLACK)
            hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+3, SCREEN_HEIGHT - 60+3))
            self.screen.blit(hint_text, hint_rect)
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
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
    
    def draw_high_score_entry(self):
        # Draw high score screen image as background
        if self.highscore_screen:
            self.screen.blit(self.highscore_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title at top with more space
        title = self.font_large.render("NEW HIGH SCORE!", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 48))
        self.screen.blit(title, title_rect)
        title = self.font_large.render("NEW HIGH SCORE!", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 45))
        self.screen.blit(title, title_rect)
        

        # Score below title with proper spacing
        score_text = self.font_medium.render("Score: {}".format(self.score), True, BLACK)
        score_rect = score_text.get_rect(center=((SCREEN_WIDTH // 2)+3, 93))
        self.screen.blit(score_text, score_rect)
        # Score below title with proper spacing
        score_text = self.font_medium.render("Score: {}".format(self.score), True, NEON_CYAN)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(score_text, score_rect)

        
        # Name entry with better spacing
        name_y = 135
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
        key_y_start = 190
        key_spacing_x = 45  # Horizontal spacing between keys
        key_spacing_y = 40  # Vertical spacing between rows
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
        legend_rect = legend_text.get_rect(center=((SCREEN_WIDTH // 2)+3, 360+3))
        self.screen.blit(legend_text, legend_rect)
        legend_text = self.font_small.render(hint_text, True, NEON_CYAN)
        legend_rect = legend_text.get_rect(center=(SCREEN_WIDTH // 2, 360))
        self.screen.blit(legend_text, legend_rect)
        hint_text = self.font_small.render("Start to continue", True, BLACK)
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+3, 452+3))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Start to continue", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 452))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_high_scores(self):
        # Draw high score screen image as background
        if self.highscore_screen:
            self.screen.blit(self.highscore_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        # Title shifted down
        title = self.font_large.render("HIGH SCORES", True, BLACK)
        title_rect = title.get_rect(center=((SCREEN_WIDTH // 2)+3, 43))
        self.screen.blit(title, title_rect)

        # Title shifted down
        title = self.font_large.render("HIGH SCORES", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
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
            start_y = 60
            spacing = 38  # Increased spacing for medium font
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
        hint_rect = hint_text.get_rect(center=((SCREEN_WIDTH // 2)+3, 452))
        self.screen.blit(hint_text, hint_rect)
        hint_text = self.font_small.render("Start to continue", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(hint_text, hint_rect)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
