# utils.py
import pygame
from typing import Tuple
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


def wrap_position(position: pygame.Vector2, radius: float) -> bool:
    """Ajuste la position si elle sort de l'écran et retourne True si un wrapping a eu lieu"""
    wrapped = False

    if position.x < -radius:
        position.x = SCREEN_WIDTH + radius
        wrapped = True
    elif position.x > SCREEN_WIDTH + radius:
        position.x = -radius
        wrapped = True

    if position.y < -radius:
        position.y = SCREEN_HEIGHT + radius
        wrapped = True
    elif position.y > SCREEN_HEIGHT + radius:
        position.y = -radius
        wrapped = True

    return wrapped


class Particle:
    """Particule générique (explosion, traînée moteur)."""

    def __init__(self, pos: pygame.Vector2, vel: pygame.Vector2, size: float,
                 lifetime: float, color: Tuple[int, int, int]):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.lifetime = lifetime
        self.max_lifetime = lifetime

        # L'image est dessinée une seule fois à la création; seule son alpha
        # change ensuite via set_alpha(), au lieu de recréer une Surface et
        # de redessiner un cercle à chaque frame pour chaque particule.
        self._radius = max(1, int(size))
        self._image = pygame.Surface((self._radius * 2, self._radius * 2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(self._image, (*color, 255), (self._radius, self._radius), self._radius)

    def update(self, dt: float) -> bool:
        self.pos += self.vel * dt * FPS
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        self._image.set_alpha(alpha)
        surface.blit(self._image, (self.pos.x - self._radius, self.pos.y - self._radius))
