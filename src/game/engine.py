import pygame
from . import settings
from .map_loader import MapLoader
from .player import Player

from .weather import WeatherManager
from .api_client import APIClient
import os

class Game:
    def __init__(self):
        pygame.init()

    
        self.weather = WeatherManager()

        # 1. Cargar mapa primero
        self.map = MapLoader().load_default()

        # 2. Calcular dimensiones reales de la ventana
        window_w = self.map.width * settings.TILE_SIZE
        window_h = self.map.height * settings.TILE_SIZE

        # 3. Crear ventana con esas dimensiones
        self.screen = pygame.display.set_mode((window_w, window_h))
        pygame.display.set_caption("Courier Quest (scaffold)")

        self.clock = pygame.time.Clock()
        self.player = Player((0, 0))
        

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.weather.update()
            speed_mult = self.weather.current_multiplier()

            # simple movement demo (arrow keys -> move 1px)
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 120 * dt * speed_mult
            dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 120 * dt * speed_mult
            self.player.pixel_move(dx, dy)


            self.screen.fill((30, 30, 30))
            self.map.draw(self.screen)
            self.player.draw(self.screen)

            font = pygame.font.SysFont(None, 20)
            info = self.weather.debug_info()
            txt = font.render(f"{info['condition']} x{info['multiplier']} time {info['time_left']}", True, (255,255,255))
            self.screen.blit(txt, (10, 10))
            
            pygame.display.flip()

        pygame.quit()
