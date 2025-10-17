#!/usr/bin/env python3
import pygame
import json
import os
import random
from game_core import *

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
            bg_path = os.path.join(SCRIPT_DIR, 'bg.png')
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background = None
            print("Warning: bg.png not found, using default background")
        
        # Load title screen image
        try:
            title_path = os.path.join(SCRIPT_DIR, 'title.png')
            self.title_screen = pygame.image.load(title_path).convert()
            self.title_screen = pygame.transform.scale(self.title_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.title_screen = None
            print("Warning: title.png not found, using default title screen")
        
        # Load bonus food image
        try:
            bonus_path = os.path.join(SCRIPT_DIR, 'bonus.png')
            self.bonus_img = pygame.image.load(bonus_path).convert_alpha()
            self.bonus_img = pygame.transform.scale(self.bonus_img, (GRID_SIZE, GRID_SIZE))
        except:
            self.bonus_img = None
            print("Warning: bonus.png not found, using default bonus graphic")
        
        # Load game over screen image
        try:
            gameover_path = os.path.join(SCRIPT_DIR, 'gameOver.png')
            self.gameover_screen = pygame.image.load(gameover_path).convert()
            self.gameover_screen = pygame.transform.scale(self.gameover_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.gameover_screen = None
            print("Warning: gameOver.png not found, using default game over screen")
        
        # Load high score screen image
        try:
            highscore_path = os.path.join(SCRIPT_DIR, 'highScore.png')
            self.highscore_screen = pygame.image.load(highscore_path).convert()
            self.highscore_screen = pygame.transform.scale(self.highscore_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.highscore_screen = None
            print("Warning: highScore.png not found, using default high score screen")
        
        # Load difficulty selection screen image
        try:
            difficulty_path = os.path.join(SCRIPT_DIR, 'difficulty.png')
            self.difficulty_screen = pygame.image.load(difficulty_path).convert()
            self.difficulty_screen = pygame.transform.scale(self.difficulty_screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.difficulty_screen = None
            print("Warning: difficulty.png not found, using default difficulty screen")
        
        # Load snake graphics (scaled larger than grid for visual overlap)
        self.snake_scale_factor = 1.25  # Scale up by 25% for overlap effect
        self.snake_sprite_size = int(GRID_SIZE * self.snake_scale_factor)
        self.snake_offset = (GRID_SIZE - self.snake_sprite_size) // 2  # Center the sprite
        
        try:
            body_path = os.path.join(SCRIPT_DIR, 'HatchlingBody.png')
            self.snake_body_img = pygame.image.load(body_path).convert_alpha()
            self.snake_body_img = pygame.transform.scale(self.snake_body_img, (self.snake_sprite_size, self.snake_sprite_size))
        except Exception as e:
            self.snake_body_img = None
            print("Warning: HatchlingBody.png not found, using default body graphic: {}".format(e))
        
        # Load snake head animation (GIF)
        try:
            from PIL import Image
            head_path = os.path.join(SCRIPT_DIR, 'HatchlingHead1.gif')
            self.snake_head_frames = []
            
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
                    self.snake_head_frames.append(pygame_frame)
                    frame_count += 1
                    gif.seek(frame_count)
            except EOFError:
                pass  # End of frames
            
            self.head_frame_index = 0
            self.head_animation_speed = 5  # Change frame every N game frames
            self.head_animation_counter = 0
            print("Loaded {} frames for snake head animation".format(len(self.snake_head_frames)))
        except Exception as e:
            self.snake_head_frames = []
            print("Warning: HatchlingHead1.gif not found or could not be loaded: {}".format(e))
        
        # Load particle effect animation (GIF)
        try:
            from PIL import Image
            particle_path = os.path.join(SCRIPT_DIR, 'particlesRed.gif')
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
            particle_white_path = os.path.join(SCRIPT_DIR, 'particlesWhite.gif')
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
            particle_rainbow_path = os.path.join(SCRIPT_DIR, 'particlesRainbow.gif')
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
            worm_path = os.path.join(SCRIPT_DIR, 'worm.gif')
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
        
        self.state = GameState.MENU
        self.snake = Snake()
        self.food_pos = None
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.score = 0
        self.level = 1
        self.lives = 3
        self.fruits_eaten_this_level = 0  # Track fruits eaten for leveling up
        self.move_timer = 0
        self.particles = []
        self.game_over_timer = 0
        self.game_over_delay = 180  # 3 seconds at 60 FPS
        
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
        self.music_manager.play_next()
        
        self.sound_manager = SoundManager()
        
        self.high_scores = self.load_high_scores()
        self.player_name = ['A', 'A', 'A']
        self.name_index = 0
        self.keyboard_selection = [0, 0]
        self.keyboard_layout = [
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T'],
            ['U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3'],
            ['4', '5', '6', '7', '8', '9', '<', ' ', ' ', '>']
        ]
        
        self.menu_selection = 0
        self.menu_options = ["Start Game", "High Scores", "Quit"]
        
        self.difficulty = Difficulty.MEDIUM  # Default difficulty
        self.difficulty_selection = 1  # Start on Medium
        self.difficulty_options = ["Easy", "Medium", "Hard"]
        
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
        self.high_scores = self.high_scores[:10]
        self.save_high_scores()
    
    def is_high_score(self, score):
        return len(self.high_scores) < 10 or score > self.high_scores[-1]['score']
    
    def spawn_food(self):
        while True:
            # Spawn food within playable area (avoid 1-grid-cell border)
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if (x, y) not in self.snake.body:
                self.food_pos = (x, y)
                break
    
    def spawn_bonus_food(self):
        while True:
            # Spawn bonus food within playable area (avoid 1-grid-cell border)
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(1, GRID_HEIGHT - 2)
            if (x, y) not in self.snake.body and (x, y) != self.food_pos:
                self.bonus_food_pos = (x, y)
                self.bonus_food_timer = 300
                break
    
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
        if self.difficulty == Difficulty.EASY:
            return 1
        elif self.difficulty == Difficulty.MEDIUM:
            return 2
        elif self.difficulty == Difficulty.HARD:
            return 3
        return 1
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
        self.music_manager.update()
        
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
                if self.is_high_score(self.score):
                    self.state = GameState.HIGH_SCORE_ENTRY
                    self.player_name = ['A', 'A', 'A']
                    self.name_index = 0
                # Otherwise stay in GAME_OVER state for player to press button
        
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update()
        
        if self.bonus_food_timer > 0:
            self.bonus_food_timer -= 1
            if self.bonus_food_timer == 0:
                self.bonus_food_pos = None
        
        self.move_timer += 1
        # Speed formula: starts at 15 frames (good pace), max speed at level 25
        move_interval = max(1, 16 - self.level // 2)
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.snake.move()
            
            # Check collision (wall collision and self-collision)
            if self.snake.check_collision(wrap_around=False):
                self.sound_manager.play('die')
                self.lives -= 1
                
                # Spawn white particles on all body segments including head
                for segment_x, segment_y in self.snake.body:
                    self.create_particles(segment_x * GRID_SIZE + GRID_SIZE // 2,
                                        segment_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                        None, None, particle_type='white')
                
                if self.lives <= 0:
                    self.sound_manager.play('no_lives')
                    self.music_manager.play_game_over_music()
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = self.game_over_delay  # Start 3-second timer
                else:
                    self.snake.reset()
                return
            
            if self.snake.body[0] == self.food_pos:
                self.sound_manager.play('eat_fruit')
                self.snake.grow(self.get_difficulty_length_modifier())
                base_points = (7 + len(self.snake.body)) *  self.level
                self.score += int(base_points * self.get_score_multiplier())
                fx, fy = self.food_pos
                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, RED, 10)
                self.spawn_food()
                
                # Check if snake filled the entire grid (GRID_WIDTH * GRID_HEIGHT = 225 cells)
                max_snake_length = GRID_WIDTH * GRID_HEIGHT
                if len(self.snake.body) >= max_snake_length:
                    self.sound_manager.play('powerup')
                    self.score += int(1000 * self.level * self.get_score_multiplier())
                    self.lives = min(99, self.lives + 10)  # Award 10 extra lives
                    # Create massive particle explosion
                    center_x = SCREEN_WIDTH // 2
                    center_y = (SCREEN_HEIGHT + GAME_OFFSET_Y) // 2
                    self.create_particles(center_x, center_y, NEON_YELLOW, 20)
                    self.create_particles(center_x, center_y, NEON_CYAN, 20)
                    # Reset snake after this incredible achievement
                    self.snake.reset()
                    self.spawn_food()
                
                # Increment fruit counter and check if player leveled up (20 fruits per level)
                self.fruits_eaten_this_level += 1
                if self.fruits_eaten_this_level >= 20:
                    self.sound_manager.play('level_up')
                    self.state = GameState.LEVEL_COMPLETE
                
                if random.random() < 0.3:
                    self.spawn_bonus_food()
            
            if self.bonus_food_pos and self.snake.body[0] == self.bonus_food_pos:
                self.sound_manager.play('powerup')
                self.snake.grow(1)
                base_points = (47 + len(self.snake.body)) * self.level
                self.score += int(base_points * self.get_score_multiplier())
                bx, by = self.bonus_food_pos
                self.create_particles(bx * GRID_SIZE + GRID_SIZE // 2,
                                    by * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, 
                                    None, None, particle_type='rainbow')
                self.bonus_food_pos = None
                self.bonus_food_timer = 0
                
                # Check if snake filled the entire grid (GRID_WIDTH * GRID_HEIGHT = 225 cells)
                max_snake_length = GRID_WIDTH * GRID_HEIGHT
                if len(self.snake.body) >= max_snake_length:
                    self.sound_manager.play('powerup')
                    self.score += int(1000 * self.level * self.get_score_multiplier())
                    self.lives = min(99, self.lives + 10)  # Award 10 extra lives
                    # Create massive particle explosion
                    center_x = SCREEN_WIDTH // 2
                    center_y = (SCREEN_HEIGHT + GAME_OFFSET_Y) // 2
                    self.create_particles(center_x, center_y, NEON_YELLOW, 20)
                    self.create_particles(center_x, center_y, NEON_CYAN, 20)
                    # Reset snake after this incredible achievement
                    self.snake.reset()
                    self.spawn_food()
                
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
        
        if self.state == GameState.PLAYING:
            if keys[pygame.K_UP]:
                self.snake.change_direction(Direction.UP)
            elif keys[pygame.K_DOWN]:
                self.snake.change_direction(Direction.DOWN)
            elif keys[pygame.K_LEFT]:
                self.snake.change_direction(Direction.LEFT)
            elif keys[pygame.K_RIGHT]:
                self.snake.change_direction(Direction.RIGHT)
        
        # Only poll hat if joystick has one (otherwise rely on JOYHATMOTION events or axes)
        if self.joystick and self.joystick_has_hat:
            hat = self.joystick.get_hat(0)
            if self.state == GameState.PLAYING:
                if hat[1] == 1:
                    self.snake.change_direction(Direction.UP)
                elif hat[1] == -1:
                    self.snake.change_direction(Direction.DOWN)
                elif hat[0] == -1:
                    self.snake.change_direction(Direction.LEFT)
                elif hat[0] == 1:
                    self.snake.change_direction(Direction.RIGHT)
        
        # For joysticks without hats, use axes (analog stick)
        elif self.joystick and not self.joystick_has_hat:
            if self.joystick.get_numaxes() >= 2:
                axis_x = self.joystick.get_axis(0)
                axis_y = self.joystick.get_axis(1)
                
                # Use a threshold to avoid drift
                threshold = 0.5
                
                # Check if axis is in neutral position
                is_neutral = abs(axis_x) < threshold and abs(axis_y) < threshold
                
                if self.state == GameState.PLAYING:
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
            if self.state == GameState.MENU:
                if event.key == pygame.K_UP:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_DOWN:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
                elif event.key == pygame.K_RETURN:
                    self.select_menu_option()
            elif self.state == GameState.PLAYING:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                # Only allow input after the 3-second timer expires
                if self.game_over_timer == 0 and event.key == pygame.K_RETURN:
                    self.reset_game()
                    self.state = GameState.MENU
            elif self.state == GameState.LEVEL_COMPLETE:
                if event.key == pygame.K_RETURN:
                    self.next_level()
            elif self.state == GameState.HIGH_SCORE_ENTRY:
                self.handle_high_score_keyboard(event)
            elif self.state == GameState.HIGH_SCORES:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.MENU
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
                    self.state = GameState.PLAYING
        
        if event.type == pygame.JOYBUTTONDOWN and self.joystick:
            button = event.button
            if self.state == GameState.MENU:
                if button == GamepadButton.BTN_START:
                    self.select_menu_option()
            elif self.state == GameState.PLAYING:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                if button == GamepadButton.BTN_START:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                # Only allow input after the 3-second timer expires
                if self.game_over_timer == 0 and button == GamepadButton.BTN_START:
                    self.reset_game()
                    self.state = GameState.MENU
            elif self.state == GameState.LEVEL_COMPLETE:
                if button == GamepadButton.BTN_START:
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
                    self.state = GameState.PLAYING
        
        if event.type == pygame.JOYHATMOTION and self.joystick:
            hat = event.value
            if self.state == GameState.MENU:
                if hat[1] == 1:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                    self.sound_manager.play('blip_select')
                elif hat[1] == -1:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
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
            # Go to difficulty selection instead of starting directly
            self.sound_manager.play('blip_select')
            self.state = GameState.DIFFICULTY_SELECT
        elif self.menu_selection == 1:
            self.state = GameState.HIGH_SCORES
        elif self.menu_selection == 2:
            pygame.quit()
            exit()
    

    def reset_game(self):
        self.snake.reset()
        self.score = 0
        self.level = 1
        self.lives = 3
        self.fruits_eaten_this_level = 0
        self.spawn_food()
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.particles = []
    
    def next_level(self):
        self.level += 1
        self.lives = min(5, self.lives + 1)
        self.fruits_eaten_this_level = 0  # Reset fruit counter for new level
        # Don't reset snake - size persists across levels!
        self.spawn_food()
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.state = GameState.PLAYING
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
            
            self.handle_input()
            
            if self.state == GameState.PLAYING:
                self.update_game()
            elif self.state == GameState.GAME_OVER:
                # Update game over timer and music even when not playing
                self.music_manager.update()
                if self.game_over_timer > 0:
                    self.game_over_timer -= 1
                    if self.game_over_timer == 0:
                        # Timer expired, transition to appropriate screen
                        if self.is_high_score(self.score):
                            self.state = GameState.HIGH_SCORE_ENTRY
                            self.player_name = ['A', 'A', 'A']
                            self.name_index = 0
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        if self.state == GameState.MENU:
            self.draw_menu()
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
        self.display.blit(pygame.transform.scale(self.screen, (SCREEN_WIDTH * self.scale, SCREEN_HEIGHT * self.scale)), (0, 0))
        pygame.display.flip()
    
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
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 60))
            
            # Draw selection box
            if i == self.menu_selection:
                glow_rect = pygame.Rect(text_rect.left - 20, text_rect.top, 
                                       text_rect.width + 40, text_rect.height)
                pygame.draw.rect(self.screen, NEON_PINK, glow_rect, 2)
            
            # Draw text
            self.screen.blit(text, text_rect)
    
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
        title = self.font_large.render("SELECT DIFFICULTY", True, NEON_CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)
        
        # Difficulty descriptions
        descriptions = [
            "Chill mode, 0.5x score",
            "Normal mode, 1x score",
            "Enemies, 2x score"
        ]
        
        # Render difficulty options with better spacing
        start_y = 120
        spacing = 70  # Increased spacing between options
        
        for i, option in enumerate(self.difficulty_options):
            color = NEON_YELLOW if i == self.difficulty_selection else NEON_GREEN
            
            # Draw option text
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * spacing))
            
            # Draw selection box
            if i == self.difficulty_selection:
                glow_rect = pygame.Rect(text_rect.left - 10, text_rect.top - 2, 
                                       text_rect.width + 20, text_rect.height + 4)
                pygame.draw.rect(self.screen, NEON_PINK, glow_rect, 2)
            
            self.screen.blit(text, text_rect)
            
            # Draw description below with proper spacing
            desc_text = self.font_small.render(descriptions[i], True, NEON_PURPLE)
            desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * spacing + 25))
            self.screen.blit(desc_text, desc_rect)
        
        # Draw hint at bottom with more space
        hint_text = self.font_small.render("Start to confirm", True, NEON_CYAN)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 340))
        self.screen.blit(hint_text, hint_rect)
    
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
        
        # Draw food with animated worm
        if self.food_pos:
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
        
        # Draw snake with graphics or gradient fallback - using interpolated positions for smooth movement
        interpolated_positions = self.get_interpolated_snake_positions()
        
        # Create a list of (index, x, y) tuples and sort by y-coordinate for proper z-ordering
        # Segments with lower y values (higher on screen) are drawn first
        # Segments with higher y values (lower on screen, closer to viewer) are drawn last
        segments_with_indices = [(i, x, y) for i, (x, y) in enumerate(interpolated_positions)]
        segments_with_indices.sort(key=lambda seg: seg[2])  # Sort by y coordinate
        
        for i, x, y in segments_with_indices:
            # Convert interpolated grid coordinates to pixel coordinates
            # Apply offset to center the larger sprites on their grid positions
            pixel_x = x * GRID_SIZE + self.snake_offset
            pixel_y = y * GRID_SIZE + self.snake_offset + GAME_OFFSET_Y
            
            if i == 0:
                # Draw head with animation
                if self.snake_head_frames:
                    head_img = self.snake_head_frames[self.head_frame_index]
                    # Rotate head based on direction
                    dx, dy = self.snake.direction.value
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
                    rect = pygame.Rect(int(pixel_x), int(pixel_y), GRID_SIZE - 2, GRID_SIZE - 2)
                    pygame.draw.rect(self.screen, NEON_GREEN, rect, border_radius=2)
                    
                    dx, dy = self.snake.direction.value
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
                if self.snake_body_img:
                    self.screen.blit(self.snake_body_img, (int(pixel_x), int(pixel_y)))
                else:
                    # Fallback to gradient rendering
                    ratio = i / max(len(self.snake.body) - 1, 1)
                    color = (int(NEON_GREEN[0] + (NEON_LIME[0] - NEON_GREEN[0]) * ratio),
                            int(NEON_GREEN[1] + (NEON_LIME[1] - NEON_GREEN[1]) * ratio),
                            int(NEON_GREEN[2] + (NEON_LIME[2] - NEON_GREEN[2]) * ratio))
                    
                    rect = pygame.Rect(int(pixel_x), int(pixel_y), GRID_SIZE - 2, GRID_SIZE - 2)
                    pygame.draw.rect(self.screen, color, rect, border_radius=2)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw HUD text (background now part of bg.png)
        # Left side: Score with label
        score_label = self.font_small.render("SCORE", True, NEON_CYAN)
        score_value = self.font_small.render("{}".format(self.score), True, WHITE)
        self.screen.blit(score_label, (8, 2))
        self.screen.blit(score_value, (8, 16))
        
        # Center-left: Level
        level_label = self.font_small.render("LVL", True, NEON_PURPLE)
        level_value = self.font_small.render("{}".format(self.level), True, WHITE)
        level_label_rect = level_label.get_rect(center=(SCREEN_WIDTH // 2 - 60, 8))
        level_value_rect = level_value.get_rect(center=(SCREEN_WIDTH // 2 - 60, 22))
        self.screen.blit(level_label, level_label_rect)
        self.screen.blit(level_value, level_value_rect)
        
        # Center-right: Fruit counter progress toward next level
        fruits_label = self.font_small.render("FRUITS", True, NEON_YELLOW)
        fruits_value = self.font_small.render("{}/20".format(self.fruits_eaten_this_level), True, WHITE)
        fruits_label_rect = fruits_label.get_rect(center=(SCREEN_WIDTH // 2 + 60, 8))
        fruits_value_rect = fruits_value.get_rect(center=(SCREEN_WIDTH // 2 + 60, 22))
        self.screen.blit(fruits_label, fruits_label_rect)
        self.screen.blit(fruits_value, fruits_value_rect)
        
        # Right side: Lives with label
        lives_label = self.font_small.render("LIVES", True, NEON_PINK)
        lives_value = self.font_small.render("{}".format(self.lives), True, WHITE)
        lives_label_rect = lives_label.get_rect(right=SCREEN_WIDTH - 8, top=2)
        lives_value_rect = lives_value.get_rect(right=SCREEN_WIDTH - 8, top=16)
        self.screen.blit(lives_label, lives_label_rect)
        self.screen.blit(lives_value, lives_value_rect)
    
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
            
            score_text = self.font_medium.render("Score: {}".format(self.score), True, NEON_CYAN)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(score_text, score_rect)
            
            level_text = self.font_medium.render("Level: {}".format(self.level), True, NEON_GREEN)
            level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 240))
            self.screen.blit(level_text, level_rect)
            
            hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 290))
            self.screen.blit(hint_text, hint_rect)
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(DARK_BG)
        self.screen.blit(overlay, (0, 0))
        
        complete_text = self.font_large.render("LEVEL UP!", True, NEON_GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(complete_text, complete_rect)
        
        bonus_text = self.font_medium.render("Bonus Life!", True, NEON_PINK)
        bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(bonus_text, bonus_rect)
        
        hint_text = self.font_small.render("Start to continue", True, NEON_YELLOW)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_high_score_entry(self):
        # Draw high score screen image as background
        if self.highscore_screen:
            self.screen.blit(self.highscore_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title at top with more space
        title = self.font_large.render("NEW HIGH SCORE!", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 45))
        self.screen.blit(title, title_rect)
        
        # Score below title with proper spacing
        score_text = self.font_medium.render("Score: {}".format(self.score), True, NEON_CYAN)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(score_text, score_rect)
        
        # Name entry with better spacing
        name_y = 130
        for i, char in enumerate(self.player_name):
            x = SCREEN_WIDTH // 2 - 40 + i * 30
            color = NEON_PINK if i == self.name_index else NEON_CYAN
            char_text = self.font_large.render(char, True, color)
            char_rect = char_text.get_rect(center=(x, name_y))
            self.screen.blit(char_text, char_rect)
            
            if i == self.name_index:
                pygame.draw.rect(self.screen, YELLOW,
                               (char_rect.left - 5, char_rect.top - 2,
                                char_rect.width + 10, char_rect.height + 4), 2)
        
        # Keyboard layout with better spacing
        key_y_start = 190
        for row_idx, row in enumerate(self.keyboard_layout):
            for col_idx, char in enumerate(row):
                x = 20 + col_idx * 26
                y = key_y_start + row_idx * 28
                
                is_selected = (row_idx == self.keyboard_selection[0] and 
                             col_idx == self.keyboard_selection[1])
                color = NEON_YELLOW if is_selected else NEON_PURPLE
                
                key_text = self.font_small.render(char, True, color)
                key_rect = key_text.get_rect(center=(x, y))
                self.screen.blit(key_text, key_rect)
                
                if is_selected:
                    pygame.draw.rect(self.screen, NEON_PINK,
                                   (key_rect.left - 3, key_rect.top - 2,
                                    key_rect.width + 6, key_rect.height + 4), 1)
        
        # Legend at bottom
        legend_text = self.font_small.render("Better luck next time!", True, NEON_GREEN)
        legend_rect = legend_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
        self.screen.blit(legend_text, legend_rect)
    
    def draw_high_scores(self):
        # Draw high score screen image as background
        if self.highscore_screen:
            self.screen.blit(self.highscore_screen, (0, 0))
        else:
            self.screen.fill(DARK_BG)
        
        # Title shifted down
        title = self.font_large.render("HIGH SCORES", True, NEON_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        if not self.high_scores:
            no_scores = self.font_medium.render("No scores yet!", True, NEON_CYAN)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, 150))
            self.screen.blit(no_scores, no_scores_rect)
        else:
            # Score list shifted down with better spacing
            start_y = 100
            spacing = 22
            for i, entry in enumerate(self.high_scores[:10]):
                name = entry['name']
                score = entry['score']
                y = start_y + i * spacing
                
                rank_text = self.font_small.render("{}".format(i+1), True, NEON_PURPLE)
                self.screen.blit(rank_text, (20, y))
                
                name_text = self.font_small.render(name, True, NEON_GREEN)
                self.screen.blit(name_text, (60, y))
                
                score_text = self.font_small.render(str(score), True, NEON_CYAN)
                score_rect = score_text.get_rect(right=SCREEN_WIDTH - 20, top=y)
                self.screen.blit(score_text, score_rect)
        
        # Hint text at bottom
        hint_text = self.font_small.render("Start to continue", True, NEON_PINK)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(hint_text, hint_rect)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
