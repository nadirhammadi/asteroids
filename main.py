import sys
import pygame
from typing import List
from constants import *
from player import Player
from asteroid import Explosion
from asteroidfield import AsteroidField, StarBackground


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Asteroids")
        self.clock = pygame.time.Clock()

        # Polices
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.big_font = pygame.font.SysFont(None, FONT_SIZE * 2)

        # Fond étoilé (indépendant de l'état de la partie, créé une seule fois)
        self.star_bg = StarBackground()

        # Cache des textes d'UI: une ligne n'est re-render que si sa valeur a changé
        self._ui_cache = {}

        self.reset()

    def reset(self):
        """(Ré)initialise l'état de la partie sans recréer la fenêtre ni les polices."""
        # Groupes de sprites
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()

        # Création du joueur
        start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.player = Player(start_pos)
        self.updatable.add(self.player)
        self.drawable.add(self.player)

        # Champ d'astéroïdes: chaque astéroïde s'ajoute lui-même à ces groupes
        asteroid_groups = (self.asteroids, self.updatable, self.drawable)
        self.asteroid_field = AsteroidField(asteroid_groups, ASTEROID_INITIAL_COUNT)

        # Explosions dynamiques
        self.explosions: List[Explosion] = []

        # État de la partie
        self.game_over = False
        self.paused = False
        self.level = 1
        self.score = 0
        self._ui_cache.clear()

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
                    self.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                self.reset()
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

        # Mise à jour du champ d'astéroïdes (les nouveaux s'ajoutent seuls aux groupes)
        self.asteroid_field.update(dt)

        # Collisions
        self._handle_collisions()

        # Mise à jour des explosions
        for exp in self.explosions[:]:
            if not exp.update(dt):
                self.explosions.remove(exp)

        # Si tous les astéroïdes sont détruits, niveau suivant
        if len(self.asteroids) == 0:
            self.level += 1
            self.asteroid_field.initial_count = min(ASTEROID_INITIAL_COUNT + self.level * 2, ASTEROID_MAX_ON_SCREEN)
            self.asteroid_field._initialize_asteroids()

    def _handle_collisions(self):
        # tirs <-> astéroïdes
        hits = pygame.sprite.groupcollide(
            self.asteroids, self.shots,
            False, True,
            pygame.sprite.collide_circle
        )
        for astro, shots_hit in hits.items():
            self.explosions.append(Explosion(astro.pos))
            astro.split()  # les fragments s'ajoutent seuls aux groupes de astro
            astro.kill()
            self.player.score += astro.score_value
            self.score = self.player.score

        # joueur <-> astéroïdes
        if not self.player.invulnerable:
            collided = pygame.sprite.spritecollide(
                self.player, self.asteroids,
                False,
                pygame.sprite.collide_circle
            )
            if collided:
                if self.player.hit():
                    self.explosions.append(Explosion(self.player.pos))
                    if self.player.lives <= 0:
                        self.game_over = True

    def render(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Fond étoilé
        self.star_bg.draw(self.screen)

        # Bordure
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            BORDER_THICKNESS
        )

        # Dessin des sprites
        for sprite in self.drawable:
            if hasattr(sprite, "draw") and callable(sprite.draw):
                sprite.draw(self.screen)
            else:
                self.screen.blit(sprite.image, sprite.rect.topleft)

        # Explosions
        for exp in self.explosions:
            exp.draw(self.screen)

        # UI + texte
        self._draw_ui()

        # Pause / Game Over
        if self.paused:
            self._draw_pause_screen()
        elif self.game_over:
            self._draw_game_over_screen()

        pygame.display.flip()

    def _cached_text(self, key: str, value: str, font: pygame.font.Font, color) -> pygame.Surface:
        """Ne re-render un texte que si sa valeur a changé depuis la dernière frame."""
        cached = self._ui_cache.get(key)
        if cached is None or cached[0] != value:
            surface = font.render(value, True, color)
            self._ui_cache[key] = (value, surface)
            return surface
        return cached[1]

    def _draw_ui(self):
        score_text = self._cached_text("score", f"Score: {self.score}", self.font, UI_COLOR)
        self.screen.blit(score_text, (20, 20))
        lives_text = self._cached_text("lives", f"Life: {self.player.lives}", self.font, UI_COLOR)
        self.screen.blit(lives_text, (20, 50))
        level_text = self._cached_text("level", f"Level: {self.level}", self.font, UI_COLOR)
        self.screen.blit(level_text, (20, 80))
        ast_text = self._cached_text("asteroids", f"Astéroïdes: {len(self.asteroids)}", self.font, UI_COLOR)
        self.screen.blit(ast_text, (20, 110))
        if not self.game_over:
            inst = self._cached_text(
                "instructions",
                "Left/Right Turn, Up accelerate, SPACE to shoot, P for pause",
                self.font, (150, 180, 220))
            self.screen.blit(inst, (SCREEN_WIDTH // 2 - inst.get_width() // 2, SCREEN_HEIGHT - 40))

    def _draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        pause_t = self.big_font.render("PAUSE", True, UI_COLOR)
        self.screen.blit(pause_t, (SCREEN_WIDTH // 2 - pause_t.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        cont = self.font.render("Press P to resume", True, UI_COLOR)
        self.screen.blit(cont, (SCREEN_WIDTH // 2 - cont.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def _draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        go_t = self.big_font.render("GAME OVER", True, (255, 100, 100))
        self.screen.blit(go_t, (SCREEN_WIDTH // 2 - go_t.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        final_s = self.font.render(f"Final Score: {self.score}", True, UI_COLOR)
        self.screen.blit(final_s, (SCREEN_WIDTH // 2 - final_s.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        restart = self.font.render("R or clic to retry", True, UI_COLOR)
        self.screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

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


if __name__ == "__main__":
    Game().run()
