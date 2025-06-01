import sys
import random
import math
import pygame
from typing import List, Tuple
from constants import *
from player import Player
from shot import Shot
from utils import wrap_position, Particle
from asteroid import Asteroid, Explosion
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

        # Stary background
        self.star_bg = StarBackground()

        # Groupes of sprites
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()

        # Ccreate the player and add to groups
        start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.player = Player(start_pos)
        self.updatable.add(self.player)
        self.drawable.add(self.player)

        # Asteroid field
        self.asteroid_field = AsteroidField(self.asteroids, ASTEROID_INITIAL_COUNT)
        for ast in self.asteroids:
            self.updatable.add(ast)
            self.drawable.add(ast)

        # Dynamic explosions
        self.explosions: List[Explosion] = []

        # Game state
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
                    self.__init__()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                self.__init__()
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

        # Update sprites
        self.updatable.update(dt)

        # Update asteroidfield
        self.asteroid_field.update(dt)
        for ast in self.asteroids:
            if ast not in self.updatable:
                self.updatable.add(ast)
                self.drawable.add(ast)

        # Collisions
        self._handle_collisions()

        # Update explosions
        for exp in self.explosions[:]:
            if not exp.update(dt):
                self.explosions.remove(exp)

        # if all asteroids are destroyed, level up
        if len(self.asteroids) == 0:
            self.level += 1
            self.asteroid_field.initial_count = min(ASTEROID_INITIAL_COUNT + self.level * 2, ASTEROID_MAX_ON_SCREEN)
            self.asteroid_field._initialize_asteroids()
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
            self.explosions.append(Explosion(astro.pos))

            # split astéroïde
            fragments = astro.split()
            for f in fragments:
                self.asteroids.add(f)
                self.updatable.add(f)
                self.drawable.add(f)

            astro.kill()
            self.player.score += astro.score_value
            self.score = self.player.score

        # player ↔ astéroïdes
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

        # star background
        self.star_bg.draw(self.screen)

        # Bordure
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            BORDER_THICKNESS
        )

        # Draw all sprites
        for sprite in self.drawable:
            if hasattr(sprite, "draw") and callable(sprite.draw):
                sprite.draw(self.screen)
            else:
                self.screen.blit(sprite.image, sprite.rect.topleft)

        # Draw explosions
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

    def _draw_ui(self):
        score_text = self.font.render(f"Score: {self.score}", True, UI_COLOR)
        self.screen.blit(score_text, (20, 20))
        lives_text = self.font.render(f"Life: {self.player.lives}", True, UI_COLOR)
        self.screen.blit(lives_text, (20, 50))
        level_text = self.font.render(f"Level: {self.level}", True, UI_COLOR)
        self.screen.blit(level_text, (20, 80))
        ast_text = self.font.render(f"Astéroïdes: {len(self.asteroids)}", True, UI_COLOR)
        self.screen.blit(ast_text, (20, 110))
        if not self.game_over:
            inst = self.font.render("Left/Right Turn, Up accelerate, SPACE to shoot, P for pause", True, (150,180,220))
            self.screen.blit(inst, (SCREEN_WIDTH//2 - inst.get_width()//2, SCREEN_HEIGHT - 40))

    def _draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        pause_t = self.big_font.render("PAUSE", True, UI_COLOR)
        self.screen.blit(pause_t, (SCREEN_WIDTH//2 - pause_t.get_width()//2, SCREEN_HEIGHT//2 - 50))
        cont = self.font.render("Press P to resume", True, UI_COLOR)
        self.screen.blit(cont, (SCREEN_WIDTH//2 - cont.get_width()//2, SCREEN_HEIGHT//2 + 20))

    def _draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        go_t = self.big_font.render("GAME OVER", True, (255, 100, 100))
        self.screen.blit(go_t, (SCREEN_WIDTH//2 - go_t.get_width()//2, SCREEN_HEIGHT//2 - 80))
        final_s = self.font.render(f"Final Score: {self.score}", True, UI_COLOR)
        self.screen.blit(final_s, (SCREEN_WIDTH//2 - final_s.get_width()//2, SCREEN_HEIGHT//2 - 20))
        restart = self.font.render("R or clic to retry", True, UI_COLOR)
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



if __name__ == "__main__":
    Game().run()
