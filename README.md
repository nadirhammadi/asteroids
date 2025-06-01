# asteroids

Key Features
- Player spaceship with physics-based movement
- Asteroid destruction with fragmentation
- Particle effects for explosions and engine trails
- Starfield background
- Score system and lives
- SProgressive difficulty levels

Game Controls:
- LEFT/RIGHT ARROWS: Rotate
- UP ARROW: Accelerate
- SPACEBAR: Fire
- P: Pause/Resume
- ESC: Quit
- R: Restart after game over

Requirements
- Python 3.8+
- Pygame 2.0+

Installation:
1. Clone Repo :
   git clone https://github.com/nadirhammadi/asteroids.git
   cd asteroids

2. Create and activate a vertual environement (recommanded) :
   # Linux/Mac:
   python -m venv venv
   source venv/bin/activate
   
   # Windows:
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

How to Run:
   python Main.py

Customization
Modify constants.py to change:
- Screen dimensions (SCREEN_WIDTH, SCREEN_HEIGHT)
- Game difficulty (FPS, INVULNERABILITY_DURATION)
- Color schemes (PLAYER_COLOR, ASTEROID_COLORS)
- Physics parameters (ACCELERATION, MAX_SPEED)

Project structure:
├── asteroid.py         # Asteroid class implementation
├── asteriodfield.py    # Asteroid field management
├── utils.py            # Utility classes (Explosion, StarBackground)
├── constants.py        # Game constants (screen size, colors, settings)
├── main.py             # Main game entry point
├── player.py           # Player spaceship class
├── requirements.txt    # Python dependencies
├── shot.py             # Projectile class
├── README.txt            # Ce fichier 
