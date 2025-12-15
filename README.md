# Snake Game

A fun retro Snake game built with pygame-ce, designed for 480x480 displays with support for both keyboard and SNES-style gamepad controls.

## Features

- **Multiple Levels**: Complete levels by growing your snake to 50 segments
- **Lives System**: Start with 3 lives, gain bonus lives when completing levels
- **High Score Table**: Top 10 scores with 3-letter name entry
- **Bonus Food**: Special yellow food appears randomly for extra points
- **Particle Effects**: Visual feedback for eating food and collisions
- **Music System**: Randomly plays background music from 3 tracks without immediate repeats
- **Progressive Difficulty**: Snake speeds up with each level

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Add your music files to the game directory:
   - `music1.ogg`
   - `music2.ogg`
   - `music3.ogg`

## How to Play

Run the game:
```bash
python main.py
```

### Controls

#### Keyboard
- **Arrow Keys**: Move snake
- **Enter**: Start button (pause/resume, select menu options)
- **W/A/S/D**: Navigate onscreen keyboard during high score entry
- **Space**: Select character from onscreen keyboard
- **Type directly**: Enter high score name using keyboard

#### Gamepad (SNES-style)
- **D-Pad**: Move snake / Navigate menus
- **Button A (0)**: Select character from onscreen keyboard
- **Button B (1)**: Backspace during name entry
- **Start (7)**: Pause/resume, confirm selections

### Gameplay

- **Regular Food (Red)**: +10 points per level, grows snake by 3 segments
- **Bonus Food (Yellow)**: +50 points per level, grows snake by 1 segment
- **Level Complete**: Reach 50 segments to advance to next level
- **Lives**: You have 3 lives. Bonus life awarded each level (max 5)
- **Game Over**: When you run out of lives, enter your name if you got a high score!

## Game States

1. **Main Menu**: Start game, view high scores, or quit
2. **Playing**: Control the snake and eat food
3. **Paused**: Press Start to pause/resume
4. **Level Complete**: Advance to next level with bonus life
5. **High Score Entry**: Enter your 3-letter name using keyboard or onscreen selection
6. **High Scores**: View top 10 scores
7. **Game Over**: Return to menu

## Files

- `main.py`: Main game loop and logic
- `game_core.py`: Core game classes (Snake, Particle, MusicManager, etc.)
- `renderer.py`: Additional rendering functions
- `highscores.json`: Saved high scores (created automatically)

## Notes

- The game will display warnings if music files are not found, but will continue to work
- High scores are automatically saved to `highscores.json`
- Screen resolution is fixed at 480x480 pixels (perfect for small displays)
- Game runs at 60 FPS

## Customization

You can modify constants in `game_core.py`:
- `GRID_SIZE`: Size of each grid cell (default: 8)
- `FPS`: Frames per second (default: 60)
- Colors and other visual elements

Enjoy playing Snake!
