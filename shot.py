import pygame
from constants import *
from utils import *
from typing import List, Tuple


class Shot(pygame.sprite.Sprite):
    def __init__(self, pos: pygame.Vector2, direction: pygame.Vector2):
        super().__init__()
        self.radius = SHOT_RADIUS
        self.pos = pygame.Vector2(pos)
        self.direction = direction.normalize()
        self.vel = self.direction * SHOT_SPEED
        self.lifetime = SHOT_LIFETIME

        # Prépare shot image
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(self.image, SHOT_COLOR, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, SHOT_BORDER, (self.radius, self.radius), self.radius, 1)
        self.rect = self.image.get_rect(center=self.pos)

        # Drag and trail
        self.trail: List[Tuple[float,float]] = []

    def update(self, dt: float):
        self.pos += self.vel
        wrap_position(self.pos, self.radius)
        self.rect.center = self.pos
        

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

        # Drag effect
        self.trail.append((self.pos.x, self.pos.y))
        if len(self.trail) > 8:
            self.trail.pop(0)

    def draw(self, surface: pygame.Surface):
        # semi-transparent trail
        if len(self.trail) > 1:
            pygame.draw.lines(surface, (255, 220, 100, 100), False, self.trail, 2)
        surface.blit(self.image, self.rect.topleft)