# utils.py
import sys
import random
import math
import pygame
from typing import List, Tuple
from constants import *


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
    """Classe générique pour particules d’explosion."""
    def __init__(self, pos: pygame.Vector2, vel: pygame.Vector2, size: float,
                 lifetime: float, color: Tuple[int,int,int]):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color

    def update(self, dt: float) -> bool:
        self.pos += self.vel * dt * FPS
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        radius = int(self.size)
        temp = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(temp, (*self.color, alpha), (radius, radius), radius)
        surface.blit(temp, (self.pos.x - radius, self.pos.y - radius))
