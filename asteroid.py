import pygame
import random
from constants import *
from utils import *
from typing import List, Tuple
from utils import wrap_position


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[int,int], size: int = 3, velocity: pygame.Vector2 = None):
        """
        size = 3 (grand), 2 (moyen), 1 (petit)
        """
        super().__init__()
        self.size = size
        self.radius = {3: 40, 2: 25, 1: 12}[size]
        self.pos = pygame.Vector2(pos)

        # Generate the asteroid image
        self._base_image = self._create_asteroid_image()
        self.angle = random.uniform(-ASTEROID_ROT_SPEED_MAX, ASTEROID_ROT_SPEED_MAX)
        self.rotation_acc = 0.0  # angle counter for continuous rotation
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=self.pos)

        # Linear velocity
        if velocity is None:
            angle0 = random.uniform(0, 360)
            speed0 = random.uniform(0.5, 2.0) * (4 - size)
            self.vel = pygame.Vector2(speed0, 0).rotate(angle0)
        else:
            self.vel = velocity

        # Score value
        self.score_value = {3: 20, 2: 50, 1: 100}[size]

    def _create_asteroid_image(self) -> pygame.Surface:
        surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA).convert_alpha()
        pts = []
        for i in range(ASTEROID_POINT_COUNT):
            a = i * (360 / ASTEROID_POINT_COUNT)
            dist = self.radius * random.uniform(0.7, 1.0)
            v = pygame.Vector2(dist, 0).rotate(a)
            pts.append((self.radius + v.x, self.radius + v.y))
        pygame.draw.polygon(surf, ASTEROID_COLORS[self.size-1], pts)
        pygame.draw.polygon(surf, ASTEROID_BORDER, pts, 2)
        for _ in range(3):
            x = random.randint(5, self.radius*2 - 5)
            y = random.randint(5, self.radius*2 - 5)
            if pygame.Vector2(x - self.radius, y - self.radius).length() < self.radius - 5:
                r = random.randint(2, 4)
                pygame.draw.circle(surf, (60, 60, 70), (x, y), r)
        return surf

    def update(self, dt: float):
        self.pos += self.vel
        wrap_position(self.pos, self.radius)
        self.rect.center = self.pos

        # Cntinuous rotation
        self.rotation_acc = (self.rotation_acc + self.angle) % 360
        self.image = pygame.transform.rotate(self._base_image, self.rotation_acc)
        self.rect = self.image.get_rect(center=self.pos)

    def split(self) -> List["Asteroid"]:
        fragments = []
        if self.size > 1:
            for _ in range(2):
                angle_variation = random.uniform(-30, 30)
                new_vel = self.vel.rotate(angle_variation) * 1.5
                fragments.append(Asteroid(self.pos, self.size - 1, new_vel))
        return fragments
    
class Explosion:
    def __init__(self, pos: pygame.Vector2):
        self.pos = pygame.Vector2(pos)
        self.particles: List[Particle] = []
        self.duration = EXPLOSION_LIFETIME
        self._create_particles()

    def _create_particles(self):
        for _ in range(EXPLOSION_PARTICLE_COUNT):
            angle = random.uniform(0, 360)
            speed = random.uniform(1.0, 5.0)
            vel = pygame.Vector2(speed, 0).rotate(angle)
            size = random.uniform(2, 6)
            lifetime = random.uniform(0.4, self.duration)
            color = random.choice(EXPLOSION_COLORS)
            self.particles.append(Particle(self.pos, vel, size, lifetime, color))

    def update(self, dt: float) -> bool:
        self.duration -= dt
        self.particles[:] = [p for p in self.particles if p.update(dt)]
        return self.duration > 0

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            p.draw(surface)