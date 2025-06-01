import pygame
import random
from asteroid import Asteroid
from constants import *
from typing import List, Tuple

class AsteroidField:
    def __init__(self, group: pygame.sprite.Group, initial_count: int = ASTEROID_INITIAL_COUNT):
        self.group = group
        self.spawn_timer = 0.0
        self.spawn_interval = ASTEROID_SPAWN_INTERVAL
        self.max_asteroids = ASTEROID_MAX_ON_SCREEN
        self.initial_count = initial_count
        self._initialize_asteroids()

    def _random_edge_position(self) -> Tuple[int,int]:
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
            pos = self._random_edge_position()
            self.group.add(Asteroid(pos))

    def update(self, dt: float):
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and len(self.group) < self.max_asteroids:
            self.spawn_timer = 0.0
            self.group.add(Asteroid(self._random_edge_position()))


class StarBackground:
    def __init__(self, num_stars: int = 200):
        self.stars = []
        for _ in range(num_stars):
            self.stars.append({
                'pos': [random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)],
                'size': random.uniform(0.5, 2.0),
                'brightness': random.uniform(0.3, 1.0)
            })

    def draw(self, surface: pygame.Surface):
        for star in self.stars:
            b = int(255 * star['brightness'])
            pygame.draw.circle(surface, (b, b, b),
                               (int(star['pos'][0]), int(star['pos'][1])),
                               int(star['size']))
