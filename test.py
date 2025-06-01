import sys
import random
import pygame
from typing import List, Tuple

# ─── Constantes ────────────────────────────────────────────────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BACKGROUND_COLOR = (10, 10, 30)
FPS = 60
INVULNERABILITY_DURATION = 2.0
BORDER_COLOR = (100, 150, 255)
BORDER_THICKNESS = 4

# Couleurs
PLAYER_COLOR = (0, 200, 255)
PLAYER_BORDER = (0, 0, 0)
ASTEROID_COLORS = [(180, 160, 140), (150, 130, 110), (120, 100, 80)]
ASTEROID_BORDER = (30, 30, 40)
SHOT_COLOR = (255, 220, 100)
SHOT_BORDER = (255, 255, 200)
EXPLOSION_COLORS = [(255, 200, 50), (255, 150, 30), (255, 100, 20)]
UI_COLOR = (200, 230, 255)
FONT_SIZE = 24
PARTICLE_COLORS = [(200, 230, 255), (150, 200, 255), (100, 170, 255)]

# Paramètres du vaisseau
PLAYER_RADIUS = 20
PLAYER_ACCELERATION = 0.2
PLAYER_MAX_SPEED = 6
PLAYER_ROT_SPEED = 4       # degrés par frame
PLAYER_SHOT_COOLDOWN = 0.2

# Paramètres des tirs
SHOT_SPEED = 10
SHOT_RADIUS = 3
SHOT_LIFETIME = 1

# Paramètres des astéroïdes
ASTEROID_BASE_SPEED = 1.5  # scalaire, multiplié par (4 - size)
ASTEROID_ROT_SPEED_MAX = 1  # en degrés/frame
ASTEROID_POINT_COUNT = 8

# Paramètres du champ d'astéroïdes
ASTEROID_INITIAL_COUNT = 6
ASTEROID_MAX_ON_SCREEN = 15
ASTEROID_SPAWN_INTERVAL = 5.0  # secondes

# Paramètres des particules (moteur + explosion)
ENGINE_PARTICLE_COUNT = 2
ENGINE_PARTICLE_LIFETIME = (0.3, 0.8)  # intervalle aléatoire
EXPLOSION_PARTICLE_COUNT = 30
EXPLOSION_LIFETIME = 0.8  # durée globale de l'explosion en secondes

# ─── CLASSES & FONCTIONS UTILES ─────────────────────────────────────────────────

def wrap_position(vec: pygame.Vector2, radius: float) -> None:
    """Fait le wrapping d’une position aux bords de l’écran."""
    if vec.x < -radius:
        vec.x = SCREEN_WIDTH + radius
    elif vec.x > SCREEN_WIDTH + radius:
        vec.x = -radius
    if vec.y < -radius:
        vec.y = SCREEN_HEIGHT + radius
    elif vec.y > SCREEN_HEIGHT + radius:
        vec.y = -radius

class Particle:
    """Classe générique pour particules (moteur ou explosion)."""
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


class Player(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[int,int]):
        super().__init__()
        self.radius = PLAYER_RADIUS

        # Image de référence non tournée
        self._base_image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(self._base_image, PLAYER_COLOR, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self._base_image, PLAYER_BORDER, (self.radius, self.radius), self.radius, 2)
        # On dessine le « nez » initial orienté vers le haut
        nose = [
            (self.radius, 0),  # pointe en haut
            (self.radius - int(self.radius*0.7), int(self.radius*0.7)),
            (self.radius + int(self.radius*0.7), int(self.radius*0.7)),
        ]
        pygame.draw.polygon(self._base_image, PLAYER_BORDER, nose)

        # On conserve l’angle actuel du vaisseau (0° ⇒ vers le haut)
        self.angle = 0  # en degrés, 0 = vers le haut

        # L’image courante (sera une rotation de _base_image)
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=pos)

        # Physique
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)

        # Timers
        self.shot_timer = 0.0
        self.invulnerable = False
        self.invul_timer = 0.0

        # Stats joueur
        self.lives = 3
        self.score = 0

        # Listes pour particules et traînée
        self.engine_particles: List[Particle] = []
        self.trail: List[Tuple[float,float]] = []

    def rotate(self, direction: int):
        """Tourne le vaisseau: direction = +1 pour gauche, -1 pour droite."""
        self.angle = (self.angle + direction * PLAYER_ROT_SPEED) % 360
        # On fait pivoter la surface entière au lieu de redessiner à la main
        self.image = pygame.transform.rotate(self._base_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def accelerate(self):
        if self.vel.length() < PLAYER_MAX_SPEED:
            # Calculer vecteur avant (angle 0 = vers le haut)
            rad = -math.radians(self.angle) + math.pi/2
            direction = pygame.Vector2(math.cos(rad), math.sin(rad))
            self.vel += direction * PLAYER_ACCELERATION
            self._create_engine_particles(direction)

    def _create_engine_particles(self, direction: pygame.Vector2):
        # Génère ENGINE_PARTICLE_COUNT particules à la position arrière du vaisseau
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

        # Shot cooldown
        self.shot_timer = max(0.0, self.shot_timer - dt)

        # Invulnérabilité
        if self.invulnerable:
            self.invul_timer -= dt
            if self.invul_timer <= 0.0:
                self.invulnerable = False

        # Mise à jour particules moteur
        self.engine_particles[:] = [p for p in self.engine_particles if p.update(dt)]

        # Mise à jour traînée
        self.trail.append((self.pos.x, self.pos.y))
        if len(self.trail) > 15:
            self.trail.pop(0)

    def handle_input(self, keys: pygame.key.ScancodeWrapper, dt: float):
        from pygame.locals import K_LEFT, K_RIGHT, K_UP, K_SPACE
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
            # Calculer direction de tir (même logique que pour l’accélération)
            rad = -math.radians(self.angle) + math.pi/2
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
        # On dessine la traînée du vaisseau (fontionne même pour un objet tourné)
        if len(self.trail) > 1:
            pygame.draw.lines(surface, (100, 200, 255, 100), False, self.trail, 2)

        # On dessine l’image (déjà tournée) du vaisseau
        surface.blit(self.image, self.rect.topleft)

        # Dessiner particules moteur
        for p in self.engine_particles:
            p.draw(surface)

        # Si invulnérable, ajouter un contour clignotant
        if self.invulnerable:
            alpha = int(255 * (abs(pygame.time.get_ticks() % 500 - 250) / 250))
            overlay = pygame.Surface((self.radius*2+10, self.radius*2+10), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (255, 255, 255, alpha),
                               (self.radius+5, self.radius+5), self.radius+5, 3)
            surface.blit(overlay, (self.pos.x - self.radius - 5, self.pos.y - self.radius - 5))


class Shot(pygame.sprite.Sprite):
    def __init__(self, pos: pygame.Vector2, direction: pygame.Vector2):
        super().__init__()
        self.radius = SHOT_RADIUS
        self.pos = pygame.Vector2(pos)
        self.direction = direction.normalize()
        self.vel = self.direction * SHOT_SPEED
        self.lifetime = SHOT_LIFETIME

        # Préparer l’image du tir
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA).convert_alpha()
        pygame.draw.circle(self.image, SHOT_COLOR, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, SHOT_BORDER, (self.radius, self.radius), self.radius, 1)
        self.rect = self.image.get_rect(center=self.pos)

        # Traînée (quelques positions seulement)
        self.trail: List[Tuple[float,float]] = []

    def update(self, dt: float):
        self.pos += self.vel
        wrap_position(self.pos, self.radius)
        self.rect.center = self.pos

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

        # Mise à jour traînée
        self.trail.append((self.pos.x, self.pos.y))
        if len(self.trail) > 8:
            self.trail.pop(0)

    def draw(self, surface: pygame.Surface):
        # Traînée semi-transparente
        if len(self.trail) > 1:
            pygame.draw.lines(surface, (255, 220, 100, 100), False, self.trail, 2)
        surface.blit(self.image, self.rect.topleft)


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, pos: Tuple[int,int], size: int = 3, velocity: pygame.Vector2 = None):
        """
        size = 3 (grand), 2 (moyen), 1 (petit)
        """
        super().__init__()
        self.size = size
        self.radius = {3: 40, 2: 25, 1: 12}[size]
        self.pos = pygame.Vector2(pos)

        # Générer une image de base pour cet astéroïde (forme polygonale aléatoire)
        self._base_image = self._create_asteroid_image()
        self.angle = random.uniform(-ASTEROID_ROT_SPEED_MAX, ASTEROID_ROT_SPEED_MAX)
        self.rotation_acc = 0.0  # compteur d’angle pour animation continue
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=self.pos)

        # Vélocité linéaire
        if velocity is None:
            angle0 = random.uniform(0, 360)
            speed0 = random.uniform(0.5, 2.0) * (4 - size)
            self.vel = pygame.Vector2(speed0, 0).rotate(angle0)
        else:
            self.vel = velocity

        # Valeur de score
        self.score_value = {3: 20, 2: 50, 1: 100}[size]

    def _create_asteroid_image(self) -> pygame.Surface:
        surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA).convert_alpha()
        # Points irréguliers autour d’un cercle
        pts = []
        for i in range(ASTEROID_POINT_COUNT):
            a = i * (360 / ASTEROID_POINT_COUNT)
            dist = self.radius * random.uniform(0.7, 1.0)
            v = pygame.Vector2(dist, 0).rotate(a)
            pts.append((self.radius + v.x, self.radius + v.y))
        pygame.draw.polygon(surf, ASTEROID_COLORS[self.size-1], pts)
        pygame.draw.polygon(surf, ASTEROID_BORDER, pts, 2)

        # Détails : petits cratères
        for _ in range(3):
            x = random.randint(5, self.radius*2 - 5)
            y = random.randint(5, self.radius*2 - 5)
            # Si le point est à l’intérieur du polygone
            if pygame.Vector2(x - self.radius, y - self.radius).length() < self.radius - 5:
                r = random.randint(2, 4)
                pygame.draw.circle(surf, (60, 60, 70), (x, y), r)
        return surf

    def update(self, dt: float):
        # Mouvement linéaire
        self.pos += self.vel
        wrap_position(self.pos, self.radius)
        self.rect.center = self.pos

        # Rotation continue (on applique un petit angle à chaque frame)
        self.rotation_acc = (self.rotation_acc + self.angle) % 360
        self.image = pygame.transform.rotate(self._base_image, self.rotation_acc)
        self.rect = self.image.get_rect(center=self.pos)

    def split(self) -> List["Asteroid"]:
        fragments = []
        if self.size > 1:
            for _ in range(2):
                # On fait tourner légèrement la vélocité initiale et on accélère
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
        # left
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


# ─── CLASSE PRINCIPALE DU JEU ────────────────────────────────────────────────────
import math

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Asteroids Remastered - Optimized")
        self.clock = pygame.time.Clock()

        # Polices
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.big_font = pygame.font.SysFont(None, FONT_SIZE * 2)

        # Fond étoilé
        self.star_bg = StarBackground()

        # Groupes de sprites
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()

        # Création du joueur et ajout manuel dans les groupes
        start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.player = Player(start_pos)
        self.updatable.add(self.player)
        self.drawable.add(self.player)

        # Champ d’astéroïdes
        self.asteroid_field = AsteroidField(self.asteroids, ASTEROID_INITIAL_COUNT)
        # Ajout manuel des astéroïdes aux groupes updatable/drawable
        for ast in self.asteroids:
            self.updatable.add(ast)
            self.drawable.add(ast)

        # Explosions dynamiques (liste d’objets non-Sprite)
        self.explosions: List[Explosion] = []

        # État du jeu
        self.game_over = False
        self.paused = False
        self.level = 1
        self.score = 0

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    # Réinitialiser tout
                    self.__init__()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                self.__init__()  # clic pour refaire
        return True

    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()
        new_shot = self.player.handle_input(keys, dt)
        if new_shot:
            self.shots.add(new_shot)
            self.updatable.add(new_shot)
            self.drawable.add(new_shot)

    def update(self, dt: float):
        if self.paused or self.game_over:
            return

        # Mise à jour des sprites
        self.updatable.update(dt)

        # Mise à jour du champ d’astéroïdes
        self.asteroid_field.update(dt)
        # Puis on vérifie si de nouveaux astéroïdes ont été ajoutés à self.asteroids
        for ast in self.asteroids:
            if ast not in self.updatable:
                self.updatable.add(ast)
                self.drawable.add(ast)

        # Collisions
        self._handle_collisions()

        # Mise à jour des explosions
        for exp in self.explosions[:]:
            if not exp.update(dt):
                self.explosions.remove(exp)

        # Si plus d’astéroïdes à l’écran ⇒ niveau suivant
        if len(self.asteroids) == 0:
            self.level += 1
            self.asteroid_field.initial_count = min(ASTEROID_INITIAL_COUNT + self.level * 2, ASTEROID_MAX_ON_SCREEN)
            self.asteroid_field._initialize_asteroids()
            # On re-ajoute les nouveaux astéroïdes aux groupes
            for ast in self.asteroids:
                if ast not in self.updatable:
                    self.updatable.add(ast)
                    self.drawable.add(ast)

    def _handle_collisions(self):
        # tirs ↔ astéroïdes
        hits = pygame.sprite.groupcollide(
            self.asteroids, self.shots,
            False, True,
            pygame.sprite.collide_circle
        )
        for astro, shots_hit in hits.items():
            # Explosion
            self.explosions.append(Explosion(astro.pos))

            # Éclatement si possible
            nouveaux = astro.split()
            for na in nouveaux:
                self.asteroids.add(na)
                self.updatable.add(na)
                self.drawable.add(na)

            astro.kill()  # supprime l’astéroïde d’orchestre
            self.player.score += astro.score_value
            self.score = self.player.score

        # joueur ↔ astéroïdes (si pas invulnérable)
        if not self.player.invulnerable:
            collided = pygame.sprite.spritecollide(
                self.player, self.asteroids,
                False,
                pygame.sprite.collide_circle
            )
            if collided:
                if self.player.hit():
                    # Explosion sur le joueur
                    self.explosions.append(Explosion(self.player.pos))
                    if self.player.lives <= 0:
                        self.game_over = True

    def render(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Fond d’étoiles
        self.star_bg.draw(self.screen)

        # Bordure
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            BORDER_THICKNESS
        )

        # On dessine d’abord tous les sprites via drawable
        for sprite in self.drawable:
            # On appelle la méthode draw spécifique si elle existe
            if hasattr(sprite, "draw") and callable(sprite.draw):
                sprite.draw(self.screen)
            else:
                self.screen.blit(sprite.image, sprite.rect.topleft)

        # Explosion (pas dans un groupe Sprite, on appelle explicitement draw)
        for exp in self.explosions:
            exp.draw(self.screen)

        # UI + texte
        self._draw_ui()

        # Écran pause / game over
        if self.paused:
            self._draw_pause_screen()
        elif self.game_over:
            self._draw_game_over_screen()

        pygame.display.flip()

    def _draw_ui(self):
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, UI_COLOR)
        self.screen.blit(score_text, (20, 20))
        # Vies
        lives_text = self.font.render(f"Vies: {self.player.lives}", True, UI_COLOR)
        self.screen.blit(lives_text, (20, 50))
        # Niveau
        level_text = self.font.render(f"Niveau: {self.level}", True, UI_COLOR)
        self.screen.blit(level_text, (20, 80))
        # Astéroïdes restantes
        ast_text = self.font.render(f"Astéroïdes: {len(self.asteroids)}", True, UI_COLOR)
        self.screen.blit(ast_text, (20, 110))
        # Instructions (si pas game over)
        if not self.game_over:
            inst = self.font.render("←/→ pour tourner, ↑ pour accélérer, SPACE pour tirer, P pour pause", True, (150,180,220))
            self.screen.blit(inst, (SCREEN_WIDTH//2 - inst.get_width()//2, SCREEN_HEIGHT - 40))

    def _draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        pause_t = self.big_font.render("PAUSE", True, UI_COLOR)
        self.screen.blit(pause_t, (SCREEN_WIDTH//2 - pause_t.get_width()//2, SCREEN_HEIGHT//2 - 50))
        cont = self.font.render("Appuyez sur P pour reprendre", True, UI_COLOR)
        self.screen.blit(cont, (SCREEN_WIDTH//2 - cont.get_width()//2, SCREEN_HEIGHT//2 + 20))

    def _draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        go_t = self.big_font.render("GAME OVER", True, (255, 100, 100))
        self.screen.blit(go_t, (SCREEN_WIDTH//2 - go_t.get_width()//2, SCREEN_HEIGHT//2 - 80))
        final_s = self.font.render(f"Score Final: {self.score}", True, UI_COLOR)
        self.screen.blit(final_s, (SCREEN_WIDTH//2 - final_s.get_width()//2, SCREEN_HEIGHT//2 - 20))
        restart = self.font.render("R ou clic pour relancer", True, UI_COLOR)
        self.screen.blit(restart, (SCREEN_WIDTH//2 - restart.get_width()//2, SCREEN_HEIGHT//2 + 30))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.handle_input(dt)
            self.update(dt)
            self.render()
        pygame.quit()
        sys.exit()


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
