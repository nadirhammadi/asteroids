import pygame
import random
from typing import Tuple
from asteroid import Asteroid
from constants import *


class AsteroidField:
    def __init__(self, groups: Tuple[pygame.sprite.Group, ...], initial_count: int = ASTEROID_INITIAL_COUNT):
        """
        groups: tuple (asteroids, updatable, drawable) - chaque astéroïde
        généré s'y ajoute lui-même, sans synchronisation manuelle côté Game.
        """
        self.groups = groups
        self.group = groups[0]  # groupe "asteroids", pour le comptage/l'itération
        self.spawn_timer = 0.0
        self.spawn_interval = ASTEROID_SPAWN_INTERVAL
        self.max_asteroids = ASTEROID_MAX_ON_SCREEN
        self.initial_count = initial_count
        self._initialize_asteroids()

    def _random_edge_position(self) -> Tuple[int, int]:
        side = random.choice(['top', 'right', 'bottom', 'left'])
        if side == 'top':
            return (random.randint(0, SCREEN_WIDTH), -40)
        if side == 'right':
            return (SCREEN_WIDTH + 40, random.randint(0, SCREEN_HEIGHT))
        if side == 'bottom':
            return (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 40)
        return (-40, random.randint(0, SCREEN_HEIGHT))

    def _initialize_asteroids(self):
        for _ in range(self.initial_count):
            Asteroid(self._random_edge_position(), groups=self.groups)

    def update(self, dt: float):
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and len(self.group) < self.max_asteroids:
            self.spawn_timer = 0.0
            Asteroid(self._random_edge_position(), groups=self.groups)


class StarBackground:
    def __init__(self, num_stars: int = 200):
        self.stars = []
        for _ in range(num_stars):
            brightness = random.uniform(0.3, 1.0)
            b = int(255 * brightness)
            self.stars.append({
                'pos': (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
                'size': max(1, int(random.uniform(0.5, 2.0))),
                'color': (b, b, b),
            })

    def draw(self, surface: pygame.Surface):
        for star in self.stars:
            pygame.draw.circle(surface, star['color'], star['pos'], star['size'])
