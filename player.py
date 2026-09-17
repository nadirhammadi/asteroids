import math
import random
import pygame
from pygame.locals import K_LEFT, K_RIGHT, K_UP, K_SPACE
from typing import List, Optional, Tuple
from constants import *
from utils import wrap_position, Particle
from shot import Shot


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[int, int]):
        super().__init__()
        self.radius = PLAYER_RADIUS

        # Image de base (utilisée pour la rotation)
        self._base_image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(self._base_image, PLAYER_COLOR, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self._base_image, PLAYER_BORDER, (self.radius, self.radius), self.radius, 2)
        # Nez du vaisseau
        nose = [
            (self.radius, 0),  # haut
            (self.radius - int(self.radius * 0.7), int(self.radius * 0.7)),
            (self.radius + int(self.radius * 0.7), int(self.radius * 0.7)),
        ]
        pygame.draw.polygon(self._base_image, PLAYER_BORDER, nose)

        # Cache des images pré-tournées, indexé par angle (multiples de PLAYER_ROT_SPEED)
        self._rotated_cache = {}
        self._invuln_overlay: Optional[pygame.Surface] = None

        self.angle = 0  # angle initial en degrés
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=pos)

        # Physique
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)

        # Timers
        self.shot_timer = 0.0
        self.invulnerable = False
        self.invul_timer = 0.0

        # Stats du joueur
        self.lives = 3
        self.score = 0

        # Particules et traînée
        self.engine_particles: List[Particle] = []
        self.trail: List[Tuple[float, float]] = []

    def _image_for_angle(self, angle: int) -> pygame.Surface:
        cached = self._rotated_cache.get(angle)
        if cached is None:
            cached = pygame.transform.rotate(self._base_image, angle)
            self._rotated_cache[angle] = cached
        return cached

    def rotate(self, direction: int):
        """Tourne le vaisseau: direction = +1 pour gauche, -1 pour droite."""
        self.angle = (self.angle + direction * PLAYER_ROT_SPEED) % 360
        # Image pré-tournée mise en cache, au lieu d'appeler transform.rotate
        # à chaque frame tant que le joueur tourne.
        self.image = self._image_for_angle(self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def accelerate(self):
        if self.vel.length() < PLAYER_MAX_SPEED:
            rad = -math.radians(self.angle) + math.pi / 2
            direction = pygame.Vector2(math.cos(rad), math.sin(rad))
            self.vel += direction * PLAYER_ACCELERATION
            self._create_engine_particles(direction)

    def _create_engine_particles(self, direction: pygame.Vector2):
        # Génère des particules derrière le vaisseau
        offset = direction * (-self.radius * 0.8)
        base_pos = self.pos + offset
        for _ in range(ENGINE_PARTICLE_COUNT):
            vel = -direction * random.uniform(1.0, 3.0) + pygame.Vector2(
                random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
            size = random.randint(2, 5)
            lifetime = random.uniform(*ENGINE_PARTICLE_LIFETIME)
            color = random.choice(PARTICLE_COLORS)
            self.engine_particles.append(Particle(base_pos, vel, size, lifetime, color))

    def update(self, dt: float):
        # Mouvement
        self.pos += self.vel
        wrap_position(self.pos, self.radius)
        self.rect.center = self.pos

        # Cooldown de tir
        self.shot_timer = max(0.0, self.shot_timer - dt)

        # Invincibilité
        if self.invulnerable:
            self.invul_timer -= dt
            if self.invul_timer <= 0.0:
                self.invulnerable = False

        # Particules
        self.engine_particles[:] = [p for p in self.engine_particles if p.update(dt)]

        # Traînée
        self.trail.append((self.pos.x, self.pos.y))
        if len(self.trail) > 15:
            self.trail.pop(0)

    def handle_input(self, keys: pygame.key.ScancodeWrapper, dt: float):
        # Rotation
        if keys[K_LEFT]:
            self.rotate(+1)
        if keys[K_RIGHT]:
            self.rotate(-1)
        # Accélération
        if keys[K_UP]:
            self.accelerate()
        # Tir
        if keys[K_SPACE] and self.shot_timer <= 0.0:
            self.shot_timer = PLAYER_SHOT_COOLDOWN
            rad = -math.radians(self.angle) + math.pi / 2
            direction = pygame.Vector2(math.cos(rad), math.sin(rad))
            return Shot(self.pos, direction)
        return None

    def activate_invulnerability(self, duration: float):
        self.invulnerable = True
        self.invul_timer = duration

    def hit(self) -> bool:
        if not self.invulnerable:
            self.lives -= 1
            self.activate_invulnerability(INVULNERABILITY_DURATION)
            return True
        return False

    def draw(self, surface: pygame.Surface):
        # Traînée
        if len(self.trail) > 1:
            pygame.draw.lines(surface, (100, 200, 255), False, self.trail, 2)

        # Vaisseau
        surface.blit(self.image, self.rect.topleft)

        # Particules moteur
        for p in self.engine_particles:
            p.draw(surface)

        # Overlay clignotant si invincible (image mise en cache, alpha seule change)
        if self.invulnerable:
            if self._invuln_overlay is None:
                self._invuln_overlay = pygame.Surface(
                    (self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(self._invuln_overlay, (255, 255, 255, 255),
                                   (self.radius + 5, self.radius + 5), self.radius + 5, 3)
            alpha = int(255 * (abs(pygame.time.get_ticks() % 500 - 250) / 250))
            self._invuln_overlay.set_alpha(alpha)
            surface.blit(self._invuln_overlay, (self.pos.x - self.radius - 5, self.pos.y - self.radius - 5))
