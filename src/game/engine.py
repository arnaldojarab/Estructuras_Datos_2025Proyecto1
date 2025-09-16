import pygame
from . import settings
from .map_loader import MapLoader
from .player import Player

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.WINDOW_W, settings.WINDOW_H))
        pygame.display.set_caption("Courier Quest (scaffold)")
        self.clock = pygame.time.Clock()
        self.map = MapLoader().load_default()
        self.player = Player((1,1))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # simple movement demo (arrow keys -> move 1px)
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 120 * dt
            dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 120 * dt
            self.player.pixel_move(dx, dy)

            self.screen.fill((30, 30, 30))
            self.map.draw(self.screen)
            self.player.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
