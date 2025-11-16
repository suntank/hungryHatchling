#!/usr/bin/env python3
import pygame
import json
import os
import sys

# Initialize Pygame
pygame.init()

# Constants - scaled to match game's 240x240 resolution
GRID_SIZE = 20  # Halved from 40 to match game scaling
GRID_WIDTH = 15
GRID_HEIGHT = 15
SCREEN_WIDTH = GRID_WIDTH * GRID_SIZE  # 300px
SCREEN_HEIGHT = GRID_HEIGHT * GRID_SIZE + 100  # 300px + 100 toolbar = 400px
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# Categories and Items
CATEGORIES = {
    "terrain": {
        "name": "Terrain",
        "items": [
            {"id": "wall", "name": "Wall", "color": GRAY},
        ]
    },
    "collectibles": {
        "name": "Collectibles",
        "items": [
            {"id": "worm", "name": "Worm", "color": GREEN},
            {"id": "bonus", "name": "Bonus Fruit", "color": RED},
            {"id": "coin", "name": "Coin", "color": YELLOW},
            {"id": "diamond", "name": "Diamond", "color": CYAN},
            {"id": "isotope", "name": "Isotope", "color": (0, 255, 0)},  # Bright green
        ]
    },
    "enemies": {
        "name": "Enemies",
        "items": [
            {"id": "enemy_spider", "name": "Spider", "color": (139, 69, 19)},
            {"id": "enemy_beetle", "name": "Beetle", "color": (75, 0, 130)},
            {"id": "enemy_scorpion", "name": "Scorpion", "color": (255, 140, 0)},
            {"id": "enemy_ant", "name": "Ant", "color": (165, 42, 42)},
            {"id": "enemy_wasp", "name": "Wasp", "color": (255, 215, 0)},
            {"id": "enemy_snake", "name": "Snake", "color": (0, 128, 0)},
        ]
    },
    "special": {
        "name": "Special",
        "items": [
            {"id": "egg", "name": "Start Position", "color": WHITE},
            {"id": "erase", "name": "Eraser", "color": RED},
        ]
    }
}

# Legacy tool constants for backward compatibility
TOOL_WALL = "wall"
TOOL_WORM = "worm"
TOOL_EGG = "egg"
TOOL_BONUS = "bonus"
TOOL_COIN = "coin"
TOOL_DIAMOND = "diamond"
TOOL_ISOTOPE = "isotope"
TOOL_ERASE = "erase"

class LevelEditor:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Level Editor - PySnake")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 12)
        self.font_medium = pygame.font.Font(None, 18)
        
        # Editor state
        self.current_tool = TOOL_WALL
        self.current_category = None  # Track which category is open
        self.walls = []
        self.worms = []
        self.bonus_fruits = []
        self.coins = []
        self.diamonds = []
        self.isotopes = []
        self.enemies = []  # New: store all enemy types
        self.starting_position = [10, 7]
        self.starting_direction = "RIGHT"
        self.boss_data = None  # Boss data for boss levels (e.g., "frog", "wormBoss")
        
        # Level metadata
        self.level_number = 1
        self.level_name = "New Level"
        self.description = "A new level"
        self.background_image = "bg.png"
        self.worms_required = 5
        
        # Get script directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.levels_dir = os.path.join(self.script_dir, "levels")
        
        # Create levels directory if it doesn't exist
        if not os.path.exists(self.levels_dir):
            os.makedirs(self.levels_dir)
        
        # UI elements
        self.toolbar_height = 60  # Halved from 120
        self.category_buttons = self._create_category_buttons()
        # Action buttons - positioned in a row at the bottom
        button_y = SCREEN_HEIGHT - 48  # Adjusted for smaller toolbar
        self.save_button = pygame.Rect(SCREEN_WIDTH - 43, button_y, 38, 14)
        self.load_button = pygame.Rect(SCREEN_WIDTH - 85, button_y, 38, 14)
        self.clear_button = pygame.Rect(SCREEN_WIDTH - 128, button_y, 38, 14)
        
        self.running = True
        self.mouse_down = False
        self.right_mouse_down = False
        
        # Text input for filename
        self.input_mode = False
        self.input_text = "level_01"
        self.input_prompt = "Enter filename (without .json):"
        
        # Level selection mode
        self.selection_mode = False
        self.available_levels = []
        self.selected_level_index = 0
        
        # Item selection mode (for choosing items within a category)
        self.item_selection_mode = False
        self.selected_item_index = 0
        self.available_items = []
        
    def _create_category_buttons(self):
        """Create buttons for each category"""
        buttons = {}
        button_width = 60  # Halved from 120
        button_height = 17  # Halved from 34
        spacing = 5  # Halved from 10
        start_x = 5  # Halved from 10
        y = GRID_HEIGHT * GRID_SIZE + 25  # Position relative to grid (halved from 50)
        
        category_ids = list(CATEGORIES.keys())
        for i, category_id in enumerate(category_ids):
            x = start_x + i * (button_width + spacing)
            buttons[category_id] = pygame.Rect(x, y, button_width, button_height)
        
        return buttons
    
    def _get_available_levels(self):
        """Get list of available level files from levels folder"""
        if not os.path.exists(self.levels_dir):
            return []
        
        levels = []
        for filename in os.listdir(self.levels_dir):
            if filename.endswith('.json'):
                levels.append(filename)
        
        return sorted(levels)
    
    def handle_events(self):
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle text input separately when in input mode
            elif self.input_mode and event.type == pygame.KEYDOWN:
                self._handle_text_input(event)
                continue
            
            # Handle level selection separately when in selection mode
            elif self.selection_mode and event.type == pygame.KEYDOWN:
                self._handle_selection_input(event)
                continue
            
            # Handle item selection separately when in item selection mode
            elif self.item_selection_mode and event.type == pygame.KEYDOWN:
                self._handle_item_selection_input(event)
                continue
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_down = True
                    self._handle_click(event.pos)
                elif event.button == 3:  # Right click
                    self.right_mouse_down = True
                    self._handle_right_click(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False
                elif event.button == 3:
                    self.right_mouse_down = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_down:
                    self._handle_click(event.pos)
                elif self.right_mouse_down:
                    self._handle_right_click(event.pos)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.input_mode = True
                    self.input_text = f"level_{self.level_number:02d}"
                elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.available_levels = self._get_available_levels()
                    if self.available_levels:
                        self.selection_mode = True
                        self.selected_level_index = 0
                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.clear_level()
                elif event.key == pygame.K_1:
                    self.current_tool = TOOL_WALL
                elif event.key == pygame.K_2:
                    self.current_tool = TOOL_WORM
                elif event.key == pygame.K_3:
                    self.current_tool = TOOL_EGG
                elif event.key == pygame.K_4:
                    self.current_tool = TOOL_ERASE
                elif event.key == pygame.K_UP:
                    self.level_number = max(1, self.level_number - 1)
                elif event.key == pygame.K_DOWN:
                    self.level_number += 1
    
    def _handle_click(self, pos):
        """Handle mouse clicks"""
        x, y = pos
        
        # Check if clicking on toolbar buttons
        if y > GRID_HEIGHT * GRID_SIZE:
            # Check category buttons - open item selection window
            for category_id, rect in self.category_buttons.items():
                if rect.collidepoint(pos):
                    self.current_category = category_id
                    self.available_items = CATEGORIES[category_id]["items"]
                    self.item_selection_mode = True
                    self.selected_item_index = 0
                    return
            
            # Check action buttons
            if self.save_button.collidepoint(pos):
                self.input_mode = True
                self.input_text = f"level_{self.level_number:02d}"
                return
            elif self.load_button.collidepoint(pos):
                self.available_levels = self._get_available_levels()
                if self.available_levels:
                    self.selection_mode = True
                    self.selected_level_index = 0
                return
            elif self.clear_button.collidepoint(pos):
                self.clear_level()
                return
        else:
            # Click on grid
            grid_x = x // GRID_SIZE
            grid_y = y // GRID_SIZE
            
            if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                self._place_item(grid_x, grid_y)
    
    def _handle_right_click(self, pos):
        """Handle right-click to erase items"""
        x, y = pos
        
        # Only erase on grid, not toolbar
        if y < GRID_HEIGHT * GRID_SIZE:
            grid_x = x // GRID_SIZE
            grid_y = y // GRID_SIZE
            
            if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                self._remove_item_at(grid_x, grid_y)
    
    def _handle_text_input(self, event):
        """Handle text input for filename"""
        if event.key == pygame.K_RETURN:
            # Save with the entered filename
            self.save_level()
            self.input_mode = False
        elif event.key == pygame.K_ESCAPE:
            # Cancel input
            self.input_mode = False
        elif event.key == pygame.K_BACKSPACE:
            # Remove last character
            self.input_text = self.input_text[:-1]
        else:
            # Add character (only allow alphanumeric, underscore, hyphen)
            if event.unicode and (event.unicode.isalnum() or event.unicode in ['_', '-']):
                self.input_text += event.unicode
    
    def _handle_selection_input(self, event):
        """Handle keyboard input for level selection"""
        if event.key == pygame.K_UP:
            self.selected_level_index = max(0, self.selected_level_index - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_level_index = min(len(self.available_levels) - 1, self.selected_level_index + 1)
        elif event.key == pygame.K_RETURN:
            # Load the selected level
            if 0 <= self.selected_level_index < len(self.available_levels):
                selected_file = self.available_levels[self.selected_level_index]
                self.load_level_from_file(selected_file)
            self.selection_mode = False
        elif event.key == pygame.K_ESCAPE:
            # Cancel selection
            self.selection_mode = False
    
    def _handle_item_selection_input(self, event):
        """Handle keyboard input for item selection within a category"""
        if event.key == pygame.K_UP:
            self.selected_item_index = max(0, self.selected_item_index - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_item_index = min(len(self.available_items) - 1, self.selected_item_index + 1)
        elif event.key == pygame.K_RETURN:
            # Select the item and set it as current tool
            if 0 <= self.selected_item_index < len(self.available_items):
                selected_item = self.available_items[self.selected_item_index]
                self.current_tool = selected_item["id"]
            self.item_selection_mode = False
        elif event.key == pygame.K_ESCAPE:
            # Cancel selection
            self.item_selection_mode = False
    
    def _place_item(self, grid_x, grid_y):
        """Place an item at the given grid position"""
        pos = {"x": grid_x, "y": grid_y}
        
        # Remove any existing items at this position
        self._remove_item_at(grid_x, grid_y)
        
        if self.current_tool == TOOL_WALL:
            self.walls.append(pos)
        elif self.current_tool == TOOL_WORM:
            self.worms.append(pos)
        elif self.current_tool == TOOL_EGG:
            self.starting_position = [grid_x, grid_y]
        elif self.current_tool == TOOL_BONUS:
            self.bonus_fruits.append(pos)
        elif self.current_tool == TOOL_COIN:
            self.coins.append(pos)
        elif self.current_tool == TOOL_DIAMOND:
            self.diamonds.append(pos)
        elif self.current_tool == TOOL_ISOTOPE:
            self.isotopes.append(pos)
        elif self.current_tool.startswith("enemy_"):
            # Handle all enemy types
            enemy_data = {"x": grid_x, "y": grid_y, "type": self.current_tool}
            self.enemies.append(enemy_data)
        # TOOL_ERASE just removes items, no placement needed
    
    def _remove_item_at(self, grid_x, grid_y):
        """Remove any item at the given grid position"""
        # Remove walls
        self.walls = [w for w in self.walls if not (w["x"] == grid_x and w["y"] == grid_y)]
        
        # Remove worms
        self.worms = [w for w in self.worms if not (w["x"] == grid_x and w["y"] == grid_y)]
        
        # Remove bonus fruits
        self.bonus_fruits = [b for b in self.bonus_fruits if not (b["x"] == grid_x and b["y"] == grid_y)]
        
        # Remove coins
        self.coins = [c for c in self.coins if not (c["x"] == grid_x and c["y"] == grid_y)]
        
        # Remove diamonds
        self.diamonds = [d for d in self.diamonds if not (d["x"] == grid_x and d["y"] == grid_y)]
        
        # Remove isotopes
        self.isotopes = [i for i in self.isotopes if not (i["x"] == grid_x and i["y"] == grid_y)]
        
        # Remove enemies
        self.enemies = [e for e in self.enemies if not (e["x"] == grid_x and e["y"] == grid_y)]
        
        # Note: Starting position is not removed, just overwritten if placing egg
    
    def save_level(self):
        """Save the current level to a JSON file"""
        level_data = {
            "level_number": self.level_number,
            "name": self.level_name,
            "description": self.description,
            "background_image": self.background_image,
            "grid_width": GRID_WIDTH,
            "grid_height": GRID_HEIGHT,
            "worms_required": len(self.worms),  # Auto-calculate based on worms placed
            "starting_position": self.starting_position,
            "starting_direction": self.starting_direction,
            "walls": self.walls,
            "worm_positions": self.worms,
            "bonus_fruit_positions": self.bonus_fruits,
            "coin_positions": self.coins,
            "diamond_positions": self.diamonds,
            "isotope_positions": self.isotopes,
            "enemies": self.enemies,
            "boss_data": self.boss_data  # Preserve boss_data instead of overwriting with None
        }
        
        # Use input_text for filename
        filename = f"{self.input_text}.json" if self.input_text else f"level_{self.level_number:02d}.json"
        filepath = os.path.join(self.levels_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(level_data, f, indent=2)
            print(f"Level saved to {filepath}")
        except Exception as e:
            print(f"Error saving level: {e}")
    
    def load_level(self):
        """Load a level from a JSON file using level_number"""
        filename = f"level_{self.level_number:02d}.json"
        self.load_level_from_file(filename)
    
    def load_level_from_file(self, filename):
        """Load a level from a specific JSON file"""
        filepath = os.path.join(self.levels_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                level_data = json.load(f)
            
            self.level_name = level_data.get("name", "New Level")
            self.description = level_data.get("description", "A level")
            self.background_image = level_data.get("background_image", "bg.png")
            self.worms_required = level_data.get("worms_required", 5)
            self.starting_position = level_data.get("starting_position", [10, 7])
            self.starting_direction = level_data.get("starting_direction", "RIGHT")
            self.walls = level_data.get("walls", [])
            self.worms = level_data.get("worm_positions", [])
            self.bonus_fruits = level_data.get("bonus_fruit_positions", [])
            self.coins = level_data.get("coin_positions", [])
            self.diamonds = level_data.get("diamond_positions", [])
            self.isotopes = level_data.get("isotope_positions", [])
            self.enemies = level_data.get("enemies", [])
            self.boss_data = level_data.get("boss_data", None)  # Load boss_data
            
            print(f"Level loaded from {filepath}")
            if self.boss_data:
                print(f"  Boss data: {self.boss_data}")
        except FileNotFoundError:
            print(f"Level file not found: {filepath}")
        except Exception as e:
            print(f"Error loading level: {e}")
    
    def clear_level(self):
        """Clear all items from the level"""
        self.walls = []
        self.worms = []
        self.bonus_fruits = []
        self.coins = []
        self.diamonds = []
        self.isotopes = []
        self.enemies = []
        self.boss_data = None  # Clear boss data too
        self.starting_position = [10, 7]
        print("Level cleared")
    
    def draw(self):
        """Draw the editor interface"""
        self.screen.fill(BLACK)
        
        # Draw grid
        self._draw_grid()
        
        # Draw items
        self._draw_walls()
        self._draw_worms()
        self._draw_bonus_fruits()
        self._draw_coins()
        self._draw_diamonds()
        self._draw_isotopes()
        self._draw_enemies()
        self._draw_starting_position()
        
        # Draw toolbar
        self._draw_toolbar()
        
        # Draw input overlay if in input mode
        if self.input_mode:
            self._draw_input_overlay()
        
        # Draw selection overlay if in selection mode
        if self.selection_mode:
            self._draw_selection_overlay()
        
        # Draw item selection overlay if in item selection mode
        if self.item_selection_mode:
            self._draw_item_selection_overlay()
        
        pygame.display.flip()
    
    def _draw_grid(self):
        """Draw the grid lines"""
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, DARK_GRAY, 
                           (x * GRID_SIZE, 0), 
                           (x * GRID_SIZE, GRID_HEIGHT * GRID_SIZE))
        
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(self.screen, DARK_GRAY, 
                           (0, y * GRID_SIZE), 
                           (GRID_WIDTH * GRID_SIZE, y * GRID_SIZE))
    
    def _draw_walls(self):
        """Draw walls on the grid"""
        for wall in self.walls:
            x = wall["x"] * GRID_SIZE
            y = wall["y"] * GRID_SIZE
            pygame.draw.rect(self.screen, GRAY, (x, y, GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(self.screen, WHITE, (x, y, GRID_SIZE, GRID_SIZE), 2)
    
    def _draw_worms(self):
        """Draw worms on the grid"""
        for worm in self.worms:
            x = worm["x"] * GRID_SIZE + GRID_SIZE // 2
            y = worm["y"] * GRID_SIZE + GRID_SIZE // 2
            pygame.draw.circle(self.screen, GREEN, (x, y), GRID_SIZE // 3)
            pygame.draw.circle(self.screen, WHITE, (x, y), GRID_SIZE // 3, 2)
    
    def _draw_bonus_fruits(self):
        """Draw bonus fruits on the grid"""
        for bonus in self.bonus_fruits:
            x = bonus["x"] * GRID_SIZE + GRID_SIZE // 2
            y = bonus["y"] * GRID_SIZE + GRID_SIZE // 2
            # Draw as a golden apple (yellow/orange circle)
            pygame.draw.circle(self.screen, YELLOW, (x, y), GRID_SIZE // 3)
            pygame.draw.circle(self.screen, ORANGE, (x, y), GRID_SIZE // 3, 2)
            # Add a small star in the center to distinguish from egg
            star_size = GRID_SIZE // 6
            pygame.draw.line(self.screen, ORANGE, (x, y - star_size), (x, y + star_size), 2)
            pygame.draw.line(self.screen, ORANGE, (x - star_size, y), (x + star_size, y), 2)
    
    def _draw_coins(self):
        """Draw coins on the grid"""
        for coin in self.coins:
            x = coin["x"] * GRID_SIZE + GRID_SIZE // 2
            y = coin["y"] * GRID_SIZE + GRID_SIZE // 2
            # Draw as a golden coin (yellow circle with border)
            pygame.draw.circle(self.screen, YELLOW, (x, y), GRID_SIZE // 4)
            pygame.draw.circle(self.screen, ORANGE, (x, y), GRID_SIZE // 4, 2)
            # Add a dollar sign or marking
            inner_radius = GRID_SIZE // 6
            pygame.draw.circle(self.screen, ORANGE, (x, y), inner_radius, 2)
    
    def _draw_diamonds(self):
        """Draw diamonds on the grid"""
        for diamond in self.diamonds:
            x = diamond["x"] * GRID_SIZE + GRID_SIZE // 2
            y = diamond["y"] * GRID_SIZE + GRID_SIZE // 2
            # Draw as a cyan/blue diamond shape
            size = GRID_SIZE // 3
            points = [
                (x, y - size),  # Top
                (x + size, y),  # Right
                (x, y + size),  # Bottom
                (x - size, y)   # Left
            ]
            pygame.draw.polygon(self.screen, CYAN, points)
            pygame.draw.polygon(self.screen, BLUE, points, 2)
            # Add inner diamond for sparkle effect
            inner_size = size // 2
            inner_points = [
                (x, y - inner_size),
                (x + inner_size, y),
                (x, y + inner_size),
                (x - inner_size, y)
            ]
            pygame.draw.polygon(self.screen, WHITE, inner_points, 1)
    
    def _draw_isotopes(self):
        """Draw isotopes on the grid (shooting power-up)"""
        for isotope in self.isotopes:
            x = isotope["x"] * GRID_SIZE + GRID_SIZE // 2
            y = isotope["y"] * GRID_SIZE + GRID_SIZE // 2
            # Draw as a bright green glowing circle with radiation symbol
            radius = GRID_SIZE // 3
            # Outer glow
            pygame.draw.circle(self.screen, (0, 255, 0), (x, y), radius)
            pygame.draw.circle(self.screen, (0, 200, 0), (x, y), radius, 2)
            # Inner core
            inner_radius = GRID_SIZE // 6
            pygame.draw.circle(self.screen, (100, 255, 100), (x, y), inner_radius)
            # Draw simple radiation symbol (3 triangular segments)
            segment_size = GRID_SIZE // 8
            for angle in [0, 120, 240]:
                import math
                rad = math.radians(angle)
                tip_x = x + int(radius * 0.7 * math.cos(rad))
                tip_y = y + int(radius * 0.7 * math.sin(rad))
                pygame.draw.circle(self.screen, (0, 150, 0), (tip_x, tip_y), segment_size // 2)
    
    def _draw_enemies(self):
        """Draw enemies on the grid"""
        for enemy in self.enemies:
            x = enemy["x"] * GRID_SIZE
            y = enemy["y"] * GRID_SIZE
            enemy_type = enemy.get("type", "enemy_spider")
            
            # Get color for this enemy type from the CATEGORIES
            enemy_color = RED  # Default color
            for category_data in CATEGORIES.values():
                for item in category_data["items"]:
                    if item["id"] == enemy_type:
                        enemy_color = item["color"]
                        break
            
            # Draw enemy as a distinctive shape (octagon/circle with marking)
            center_x = x + GRID_SIZE // 2
            center_y = y + GRID_SIZE // 2
            radius = GRID_SIZE // 3
            
            # Draw body
            pygame.draw.circle(self.screen, enemy_color, (center_x, center_y), radius)
            pygame.draw.circle(self.screen, BLACK, (center_x, center_y), radius, 2)
            
            # Draw simple angry eyes
            eye_offset = radius // 3
            eye_size = 3
            pygame.draw.circle(self.screen, BLACK, (center_x - eye_offset, center_y - eye_offset), eye_size)
            pygame.draw.circle(self.screen, BLACK, (center_x + eye_offset, center_y - eye_offset), eye_size)
            
            # Draw angry mouth
            pygame.draw.line(self.screen, BLACK, 
                           (center_x - eye_offset, center_y + eye_offset),
                           (center_x + eye_offset, center_y + eye_offset), 2)
    
    def _draw_starting_position(self):
        """Draw the starting position (egg)"""
        x = self.starting_position[0] * GRID_SIZE
        y = self.starting_position[1] * GRID_SIZE
        
        # Draw egg shape (ellipse)
        egg_rect = pygame.Rect(x + GRID_SIZE // 4, y + GRID_SIZE // 6, 
                              GRID_SIZE // 2, GRID_SIZE * 2 // 3)
        pygame.draw.ellipse(self.screen, YELLOW, egg_rect)
        pygame.draw.ellipse(self.screen, ORANGE, egg_rect, 2)
    
    def _draw_toolbar(self):
        """Draw the toolbar at the bottom"""
        # Toolbar background
        toolbar_rect = pygame.Rect(0, GRID_HEIGHT * GRID_SIZE, 
                                  SCREEN_WIDTH, self.toolbar_height)
        pygame.draw.rect(self.screen, DARK_GRAY, toolbar_rect)
        
        # Top section: Info text (two lines)
        base_y = GRID_HEIGHT * GRID_SIZE
        info_text = f"Level: {self.level_number} | Walls: {len(self.walls)} | Worms: {len(self.worms)} | Bonus: {len(self.bonus_fruits)}"
        info = self.font_small.render(info_text, True, WHITE)
        self.screen.blit(info, (8, base_y + 5))
        
        # Second line of info for coins, diamonds, isotopes, and enemies
        info_text2 = f"Coins: {len(self.coins)} | Diamonds: {len(self.diamonds)} | Isotopes: {len(self.isotopes)} | Enemies: {len(self.enemies)}"
        info2 = self.font_small.render(info_text2, True, WHITE)
        self.screen.blit(info2, (8, base_y + 25))
        
        # Middle section: Category buttons
        for category_id, rect in self.category_buttons.items():
            # Highlight if this is the current category with selected tool
            category_has_current_tool = False
            for item in CATEGORIES[category_id]["items"]:
                if item["id"] == self.current_tool:
                    category_has_current_tool = True
                    break
            
            color = CYAN if category_has_current_tool else LIGHT_GRAY
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, WHITE, rect, 2)
            
            # Button label - use category name
            label_text = CATEGORIES[category_id]["name"]
            label = self.font_small.render(label_text, True, BLACK)
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)
        
        # Bottom section: Action buttons and current tool display
        # Current tool indicator (left side)
        tool_text = f"Tool: {self.current_tool.upper()}"
        tool_render = self.font_small.render(tool_text, True, CYAN)
        self.screen.blit(tool_render, (8, base_y + 87))
        
        # Draw action buttons (right side)
        # Clear button
        pygame.draw.rect(self.screen, RED, self.clear_button)
        pygame.draw.rect(self.screen, WHITE, self.clear_button, 2)
        clear_text = self.font_small.render("CLEAR", True, WHITE)
        clear_rect = clear_text.get_rect(center=self.clear_button.center)
        self.screen.blit(clear_text, clear_rect)
        
        # Load button
        pygame.draw.rect(self.screen, BLUE, self.load_button)
        pygame.draw.rect(self.screen, WHITE, self.load_button, 2)
        load_text = self.font_small.render("LOAD", True, WHITE)
        load_rect = load_text.get_rect(center=self.load_button.center)
        self.screen.blit(load_text, load_rect)
        
        # Save button
        pygame.draw.rect(self.screen, GREEN, self.save_button)
        pygame.draw.rect(self.screen, WHITE, self.save_button, 2)
        save_text = self.font_small.render("SAVE", True, WHITE)
        save_rect = save_text.get_rect(center=self.save_button.center)
        self.screen.blit(save_text, save_rect)
    
    def _draw_input_overlay(self):
        """Draw input overlay for filename entry"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Input box
        box_width = 200  # Halved from 400
        box_height = 60  # Halved from 120
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (GRID_HEIGHT * GRID_SIZE - box_height) // 2
        
        # Draw box background
        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 2)
        
        # Draw prompt
        prompt = self.font_small.render(self.input_prompt, True, WHITE)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, box_y + 12))
        self.screen.blit(prompt, prompt_rect)
        
        # Draw input text with cursor
        input_display = self.input_text + "_"
        input_render = self.font_medium.render(input_display, True, CYAN)
        input_rect = input_render.get_rect(center=(SCREEN_WIDTH // 2, box_y + 30))
        self.screen.blit(input_render, input_rect)
        
        # Draw instructions
        instructions = self.font_small.render("ENTER to save | ESC to cancel", True, LIGHT_GRAY)
        inst_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, box_y + 48))
        self.screen.blit(instructions, inst_rect)
    
    def _draw_selection_overlay(self):
        """Draw level selection overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Selection box
        box_width = 200  # Halved from 400
        box_height = min(200, 60 + len(self.available_levels) * 18)  # Scaled proportionally
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (GRID_HEIGHT * GRID_SIZE - box_height) // 2
        
        # Draw box background
        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 2)
        
        # Draw title
        title = self.font_medium.render("Select Level to Load", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, box_y + 12))
        self.screen.blit(title, title_rect)
        
        # Draw level list
        list_y = box_y + 30
        max_visible = min(8, len(self.available_levels))
        start_index = max(0, min(self.selected_level_index - max_visible // 2, len(self.available_levels) - max_visible))
        
        for i in range(start_index, min(start_index + max_visible, len(self.available_levels))):
            level_name = self.available_levels[i]
            # Remove .json extension for display
            display_name = level_name[:-5] if level_name.endswith('.json') else level_name
            
            # Highlight selected item
            if i == self.selected_level_index:
                highlight_rect = pygame.Rect(box_x + 5, list_y + (i - start_index) * 18, box_width - 10, 15)
                pygame.draw.rect(self.screen, CYAN, highlight_rect)
                text_color = BLACK
            else:
                text_color = WHITE
            
            # Draw level name
            level_text = self.font_small.render(display_name, True, text_color)
            self.screen.blit(level_text, (box_x + 10, list_y + (i - start_index) * 18 + 3))
        
        # Draw instructions
        inst_y = box_y + box_height - 15
        instructions = self.font_small.render("↑↓: Navigate | ENTER: Load | ESC: Cancel", True, LIGHT_GRAY)
        inst_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, inst_y))
        self.screen.blit(instructions, inst_rect)
    
    def _draw_item_selection_overlay(self):
        """Draw item selection overlay for choosing items within a category"""
        if not self.current_category:
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Selection box
        box_width = 225  # Halved from 450
        box_height = min(225, 60 + len(self.available_items) * 20)  # Scaled proportionally
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (GRID_HEIGHT * GRID_SIZE - box_height) // 2
        
        # Draw box background
        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 2)
        
        # Draw title with category name
        category_name = CATEGORIES[self.current_category]["name"]
        title = self.font_medium.render(f"Select {category_name} Item", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, box_y + 12))
        self.screen.blit(title, title_rect)
        
        # Draw item list
        list_y = box_y + 30
        max_visible = min(8, len(self.available_items))
        start_index = max(0, min(self.selected_item_index - max_visible // 2, len(self.available_items) - max_visible))
        
        for i in range(start_index, min(start_index + max_visible, len(self.available_items))):
            item = self.available_items[i]
            item_name = item["name"]
            item_color = item["color"]
            
            # Highlight selected item
            if i == self.selected_item_index:
                highlight_rect = pygame.Rect(box_x + 5, list_y + (i - start_index) * 20, box_width - 10, 18)
                pygame.draw.rect(self.screen, CYAN, highlight_rect)
                text_color = BLACK
            else:
                text_color = WHITE
            
            # Draw color preview square
            color_square = pygame.Rect(box_x + 10, list_y + (i - start_index) * 20 + 3, 12, 12)
            pygame.draw.rect(self.screen, item_color, color_square)
            pygame.draw.rect(self.screen, WHITE, color_square, 1)
            
            # Draw item name
            item_text = self.font_small.render(item_name, True, text_color)
            self.screen.blit(item_text, (box_x + 28, list_y + (i - start_index) * 20 + 4))
        
        # Draw instructions
        inst_y = box_y + box_height - 15  # Scaled from 30
        instructions = self.font_small.render("↑↓: Navigate | ENTER: Select | ESC: Cancel", True, LIGHT_GRAY)
        inst_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, inst_y))
        self.screen.blit(instructions, inst_rect)
    
    def run(self):
        """Main editor loop"""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()
