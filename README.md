# Asteroids

## Key Features
- Player spaceship with physics-based movement
- Asteroid destruction with fragmentation
- Particle effects for explosions and engine trails
- Starfield background
- Score system and lives
- Progressive difficulty levels

## Game Controls
- LEFT/RIGHT ARROWS: Rotate
- UP ARROW: Accelerate
- SPACEBAR: Fire
- P: Pause/Resume
- ESC: Quit
- R: Restart after game over

## Requirements
- Python 3.8+
- Pygame 2.0+

## Installation
1. Clone the repo.

2. Create and activate a virtual environment (recommended):

   Linux/Mac:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

   Windows:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## How to Run
```
python main.py
```

## Customization
Modify `constants.py` to change:
- Screen dimensions (`SCREEN_WIDTH`, `SCREEN_HEIGHT`)
- Game difficulty (`FPS`, `INVULNERABILITY_DURATION`)
- Color schemes (`PLAYER_COLOR`, `ASTEROID_COLORS`)
- Physics parameters (`PLAYER_ACCELERATION`, `PLAYER_MAX_SPEED`)

## Project Structure
```
├── asteroid.py         # Asteroid class implementation
├── asteroidfield.py    # Asteroid field management, starfield background
├── utils.py            # Utility helpers (position wrapping, Particle)
├── constants.py        # Game constants (screen size, colors, settings)
├── main.py              # Main game entry point
├── player.py            # Player spaceship class
├── requirements.txt     # Python dependencies
├── shot.py               # Projectile class
└── README.md             # This file
```
