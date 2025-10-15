#!/usr/bin/env python3
import pygame
import json
import os
import random
from game_core import *

pygame.init()
pygame.mixer.init()

FPS = 60

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)  # 2x larger (was 16)
        self.font_medium = pygame.font.Font(None, 24)  # 2x larger (was 24)
        self.font_large = pygame.font.Font(None, 36)  # 2x larger (was 36)
        
        self.state = GameState.MENU
        self.snake = Snake()
        self.food_pos = None
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.score = 0
        self.level = 1
        self.lives = 3
        self.move_timer = 0
        self.particles = []
        
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Gamepad connected: {self.joystick.get_name()}")
        
        self.music_manager = MusicManager()
        self.music_manager.play_next()
        
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
        
        self.spawn_food()
    
    def load_high_scores(self):
        try:
            if os.path.exists('highscores.json'):
                with open('highscores.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_high_scores(self):
        try:
            with open('highscores.json', 'w') as f:
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
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake.body:
                self.food_pos = (x, y)
                break
    
    def spawn_bonus_food(self):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake.body and (x, y) != self.food_pos:
                self.bonus_food_pos = (x, y)
                self.bonus_food_timer = 300
                break
    
    def create_particles(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(1, 3)
            velocity = (speed * pygame.math.Vector2(1, 0).rotate_rad(angle).x,
                       speed * pygame.math.Vector2(1, 0).rotate_rad(angle).y)
            self.particles.append(Particle(x, y, color, velocity))
    
    def update_game(self):
        self.music_manager.update()
        
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update()
        
        if self.bonus_food_timer > 0:
            self.bonus_food_timer -= 1
            if self.bonus_food_timer == 0:
                self.bonus_food_pos = None
        
        self.move_timer += 1
        move_interval = max(2, 10 - self.level)
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.snake.move()
            
            if self.snake.check_collision():
                self.lives -= 1
                head_x, head_y = self.snake.body[0]
                self.create_particles(head_x * GRID_SIZE + GRID_SIZE // 2,
                                    head_y * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, RED, 20)
                
                if self.lives <= 0:
                    if self.is_high_score(self.score):
                        self.state = GameState.HIGH_SCORE_ENTRY
                        self.player_name = ['A', 'A', 'A']
                        self.name_index = 0
                    else:
                        self.state = GameState.GAME_OVER
                else:
                    self.snake.reset()
                return
            
            if self.snake.body[0] == self.food_pos:
                self.snake.grow(3)
                self.score += 10 * self.level
                fx, fy = self.food_pos
                self.create_particles(fx * GRID_SIZE + GRID_SIZE // 2,
                                    fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, GREEN, 15)
                self.spawn_food()
                
                if random.random() < 0.3:
                    self.spawn_bonus_food()
            
            if self.bonus_food_pos and self.snake.body[0] == self.bonus_food_pos:
                self.snake.grow(1)
                self.score += 50 * self.level
                bx, by = self.bonus_food_pos
                self.create_particles(bx * GRID_SIZE + GRID_SIZE // 2,
                                    by * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y, YELLOW, 20)
                self.bonus_food_pos = None
                self.bonus_food_timer = 0
            
            if len(self.snake.body) >= 50:
                self.state = GameState.LEVEL_COMPLETE
    
    def handle_input(self):
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
        
        if self.joystick:
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
    
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            if self.state == GameState.MENU:
                if event.key == pygame.K_UP:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                elif event.key == pygame.K_DOWN:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN:
                    self.select_menu_option()
            elif self.state == GameState.PLAYING:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_RETURN:
                    self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                if event.key == pygame.K_RETURN:
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
                if button == GamepadButton.BTN_START:
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
        
        if event.type == pygame.JOYHATMOTION and self.joystick:
            hat = event.value
            if self.state == GameState.MENU:
                if hat[1] == 1:
                    self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
                elif hat[1] == -1:
                    self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
            elif self.state == GameState.HIGH_SCORE_ENTRY:
                if hat[0] == -1:
                    self.keyboard_selection[1] = max(0, self.keyboard_selection[1] - 1)
                elif hat[0] == 1:
                    self.keyboard_selection[1] = min(9, self.keyboard_selection[1] + 1)
                elif hat[1] == 1:
                    self.keyboard_selection[0] = max(0, self.keyboard_selection[0] - 1)
                elif hat[1] == -1:
                    self.keyboard_selection[0] = min(3, self.keyboard_selection[0] + 1)
        
        return True
    
    def handle_high_score_keyboard(self, event):
        if event.key == pygame.K_BACKSPACE:
            if self.name_index > 0:
                self.name_index -= 1
                self.player_name[self.name_index] = 'A'
        elif event.key == pygame.K_LEFT:
            if self.name_index > 0:
                self.name_index -= 1
        elif event.key == pygame.K_RIGHT:
            if self.name_index < 2:
                self.name_index += 1
        elif event.key == pygame.K_UP:
            # Optional: Navigate onscreen keyboard
            self.keyboard_selection[0] = max(0, self.keyboard_selection[0] - 1)
        elif event.key == pygame.K_DOWN:
            # Optional: Navigate onscreen keyboard
            self.keyboard_selection[0] = min(3, self.keyboard_selection[0] + 1)
        elif event.key == pygame.K_RETURN:
            name = ''.join(self.player_name)
            self.add_high_score(name, self.score)
            self.state = GameState.HIGH_SCORES
        elif event.key == pygame.K_SPACE:
            # Use onscreen keyboard selection
            self.use_onscreen_keyboard()
        elif event.unicode.isalnum() and len(event.unicode) == 1:
            # Direct keyboard input - just type the letters!
            self.player_name[self.name_index] = event.unicode.upper()
            if self.name_index < 2:
                self.name_index += 1
    
    def use_onscreen_keyboard(self):
        row, col = self.keyboard_selection
        char = self.keyboard_layout[row][col]
        if char == '<':
            if self.name_index > 0:
                self.name_index -= 1
        elif char == '>':
            if self.name_index < 2:
                self.name_index += 1
        elif char != ' ':
            self.player_name[self.name_index] = char
            if self.name_index < 2:
                self.name_index += 1
    
    def select_menu_option(self):
        if self.menu_selection == 0:
            self.reset_game()
            self.state = GameState.PLAYING
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
        self.spawn_food()
        self.bonus_food_pos = None
        self.bonus_food_timer = 0
        self.particles = []
    
    def next_level(self):
        self.level += 1
        self.lives = min(5, self.lives + 1)
        self.snake.reset()
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
        
        pygame.display.flip()
    
    def draw_menu(self):
        title = self.font_large.render("SNAKE", True, GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self.screen.blit(title, title_rect)
        
        for i, option in enumerate(self.menu_options):
            color = YELLOW if i == self.menu_selection else WHITE
            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 100 + i * 30))
            self.screen.blit(text, text_rect)
            
            if i == self.menu_selection:
                pygame.draw.rect(self.screen, YELLOW, 
                               (text_rect.left - 10, text_rect.top, 
                                text_rect.width + 20, text_rect.height), 2)
    
    def draw_game(self):
        # Draw HUD bar at the top
        pygame.draw.rect(self.screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        pygame.draw.line(self.screen, WHITE, (0, HUD_HEIGHT), (SCREEN_WIDTH, HUD_HEIGHT), 2)
        
        # Draw HUD text
        score_text = self.font_small.render(f"{self.score}", True, WHITE)
        self.screen.blit(score_text, (5, 0))
        
        level_text = self.font_small.render(f"LVL: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, (HUD_HEIGHT // 2)+1))
        self.screen.blit(level_text, level_rect)
        
        lives_text = self.font_small.render(f"Lives: {self.lives}", True, WHITE)
        lives_rect = lives_text.get_rect(right=SCREEN_WIDTH - 5, top=0)
        self.screen.blit(lives_text, lives_rect)
        
        # Draw grid (offset by HUD height)
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, DARK_GRAY, (x, GAME_OFFSET_Y), (x, SCREEN_HEIGHT))
        for y in range(GAME_OFFSET_Y, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, DARK_GRAY, (0, y), (SCREEN_WIDTH, y))
        
        # Draw food
        if self.food_pos:
            fx, fy = self.food_pos
            center_x = fx * GRID_SIZE + GRID_SIZE // 2
            center_y = fy * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
            pygame.draw.circle(self.screen, RED, (center_x, center_y), GRID_SIZE // 2)
        
        # Draw bonus food with pulsing effect
        if self.bonus_food_pos:
            bx, by = self.bonus_food_pos
            center_x = bx * GRID_SIZE + GRID_SIZE // 2
            center_y = by * GRID_SIZE + GRID_SIZE // 2 + GAME_OFFSET_Y
            pulse = abs((self.bonus_food_timer % 60) - 30) / 30
            size = int(GRID_SIZE // 2 + pulse * 2)
            pygame.draw.circle(self.screen, YELLOW, (center_x, center_y), size)
            pygame.draw.circle(self.screen, ORANGE, (center_x, center_y), max(2, size // 2))
        
        # Draw snake with gradient
        for i, (x, y) in enumerate(self.snake.body):
            ratio = i / max(len(self.snake.body) - 1, 1)
            color = (int(GREEN[0] + (DARK_GREEN[0] - GREEN[0]) * ratio),
                    int(GREEN[1] + (DARK_GREEN[1] - GREEN[1]) * ratio),
                    int(GREEN[2] + (DARK_GREEN[2] - GREEN[2]) * ratio))
            
            rect = pygame.Rect(x * GRID_SIZE + 1, y * GRID_SIZE + 1 + GAME_OFFSET_Y, 
                             GRID_SIZE - 2, GRID_SIZE - 2)
            pygame.draw.rect(self.screen, color, rect, border_radius=2)
            
            # Draw eyes on head
            if i == 0:
                dx, dy = self.snake.direction.value
                if dx == 1:
                    eye1 = (x * GRID_SIZE + GRID_SIZE - 2, y * GRID_SIZE + 2 + GAME_OFFSET_Y)
                    eye2 = (x * GRID_SIZE + GRID_SIZE - 2, y * GRID_SIZE + GRID_SIZE - 2 + GAME_OFFSET_Y)
                elif dx == -1:
                    eye1 = (x * GRID_SIZE + 2, y * GRID_SIZE + 2 + GAME_OFFSET_Y)
                    eye2 = (x * GRID_SIZE + 2, y * GRID_SIZE + GRID_SIZE - 2 + GAME_OFFSET_Y)
                elif dy == -1:
                    eye1 = (x * GRID_SIZE + 2, y * GRID_SIZE + 2 + GAME_OFFSET_Y)
                    eye2 = (x * GRID_SIZE + GRID_SIZE - 2, y * GRID_SIZE + 2 + GAME_OFFSET_Y)
                else:
                    eye1 = (x * GRID_SIZE + 2, y * GRID_SIZE + GRID_SIZE - 2 + GAME_OFFSET_Y)
                    eye2 = (x * GRID_SIZE + GRID_SIZE - 2, y * GRID_SIZE + GRID_SIZE - 2 + GAME_OFFSET_Y)
                
                pygame.draw.circle(self.screen, YELLOW, eye1, 2)
                pygame.draw.circle(self.screen, YELLOW, eye2, 2)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
    
    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)
        
        hint_text = self.font_small.render("Start to resume", True, WHITE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_game_over(self):
        self.screen.fill(BLACK)
        
        over_text = self.font_large.render("GAME OVER", True, RED)
        over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(over_text, over_rect)
        
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(score_text, score_rect)
        
        level_text = self.font_medium.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(level_text, level_rect)
        
        hint_text = self.font_small.render("Start to continue", True, WHITE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        complete_text = self.font_large.render("LEVEL UP!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(complete_text, complete_rect)
        
        bonus_text = self.font_medium.render("Bonus Life!", True, YELLOW)
        bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(bonus_text, bonus_rect)
        
        hint_text = self.font_small.render("Start to continue", True, WHITE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(hint_text, hint_rect)
    
    def draw_high_score_entry(self):
        self.screen.fill(BLACK)
        
        title = self.font_large.render("NEW HIGH SCORE!", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(title, title_rect)
        
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(score_text, score_rect)
        
        name_y = 75
        for i, char in enumerate(self.player_name):
            x = SCREEN_WIDTH // 2 - 30 + i * 20
            color = YELLOW if i == self.name_index else WHITE
            char_text = self.font_large.render(char, True, color)
            char_rect = char_text.get_rect(center=(x, name_y))
            self.screen.blit(char_text, char_rect)
            
            if i == self.name_index:
                pygame.draw.rect(self.screen, YELLOW,
                               (char_rect.left - 5, char_rect.top - 2,
                                char_rect.width + 10, char_rect.height + 4), 2)
        
        key_y_start = 110
        for row_idx, row in enumerate(self.keyboard_layout):
            for col_idx, char in enumerate(row):
                x = 10 + col_idx * 22
                y = key_y_start + row_idx * 20
                
                is_selected = (row_idx == self.keyboard_selection[0] and 
                             col_idx == self.keyboard_selection[1])
                color = YELLOW if is_selected else WHITE
                
                key_text = self.font_small.render(char, True, color)
                key_rect = key_text.get_rect(center=(x, y))
                self.screen.blit(key_text, key_rect)
                
                if is_selected:
                    pygame.draw.rect(self.screen, YELLOW,
                                   (key_rect.left - 3, key_rect.top - 2,
                                    key_rect.width + 6, key_rect.height + 4), 1)
        
        legend_text = self.font_small.render("Better luck next time!", True, WHITE)
        legend_rect = legend_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(legend_text, legend_rect)
    
    def draw_high_scores(self):
        self.screen.fill(BLACK)
        
        title = self.font_large.render("HIGH SCORES", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 20))
        self.screen.blit(title, title_rect)
        
        if not self.high_scores:
            no_scores = self.font_medium.render("No scores yet!", True, WHITE)
            no_scores_rect = no_scores.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(no_scores, no_scores_rect)
        else:
            for i, entry in enumerate(self.high_scores[:10]):
                name = entry['name']
                score = entry['score']
                y = 50 + i * 18
                
                rank_text = self.font_small.render(f"{i+1}.", True, WHITE)
                self.screen.blit(rank_text, (20, y))
                
                name_text = self.font_small.render(name, True, GREEN)
                self.screen.blit(name_text, (45, y))
                
                score_text = self.font_small.render(str(score), True, YELLOW)
                score_rect = score_text.get_rect(right=SCREEN_WIDTH - 20, top=y)
                self.screen.blit(score_text, score_rect)
        
        hint_text = self.font_small.render("Start to continue", True, WHITE)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(hint_text, hint_rect)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
