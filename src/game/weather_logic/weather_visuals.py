# src/game/weather_visuals.py
import random
import os
import pygame
from .. import settings
from .weather_Items import Cloud 


class WeatherVisuals:
    """
    Maneja la parte visual del clima (nubes, overlays, efectos).
    Recibe la condición actual desde WeatherManager.
    """

    def __init__(self,window_w, window_h):
        self.clouds = []
        self._cloud_spawn_timer = 0.0
        self._max_clouds = 0
        self.rain_timer = 0.0 

        self.filter_alpha = 0       # empieza invisible
        self.target_alpha = 90      # opacidad final del filtro
        self.filter_speed = 30      # velocidad de transición (aumenta o baja este valor)

        self.window_w=window_w
        self.window_h=window_h

    def update(self, dt, condition: str, transitioning: bool):
        # actualizar nubes
        for cloud in self.clouds:
            cloud.update(dt)

        # borrar solo nubes ya desvanecidas y sin transición
        self.clouds = [c for c in self.clouds if not (c.is_fully_transparent() and not c._transitioning)]

        # spawn de nubes
        if self._max_clouds > 0 and condition in ("clouds", "rain", "rain_light", "storm"):
            self._cloud_spawn_timer += dt
            if self._cloud_spawn_timer > random.uniform(0.3, 0.5):
                if len(self.clouds) < self._max_clouds:
                    self._spawn_cloud(condition)
                self._cloud_spawn_timer = 0

    def handle_condition_change(self, next_condition):
        if next_condition == "clear":
            for c in self.clouds:
                c.start_transition(0, 0, duration=5)  # fade out
            self._max_clouds = 0

        elif next_condition == "clouds":
            self._max_clouds += 50
            self._cloud_spawn_timer = 0
            for c in self.clouds:
                c.start_transition(255, 0, duration=3)  # blanco

        elif next_condition in ("rain", "rain_light", "storm"):
            self._max_clouds += 50
            self._cloud_spawn_timer = 0
            for c in self.clouds:
                c.start_transition(0, 255, duration=3)  # gris

    def _select_Image(self):
        num= random.randint(0,4)
        assets_dir = os.path.join(os.path.dirname(__file__), "..","..", "assets", "clouds")
        nubes = []

        
        if num == 0:
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_white0.png")).convert_alpha()) 
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_gray0.png")).convert_alpha())
        elif num == 1:
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_white1.png")).convert_alpha()) 
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_gray1.png")).convert_alpha())
        elif num == 2:
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_white2.png")).convert_alpha()) 
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_gray2.png")).convert_alpha())
        elif num == 3:
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_white3.png")).convert_alpha()) 
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_gray3.png")).convert_alpha())
        elif num == 4:
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_white4.png")).convert_alpha()) 
            nubes.append(pygame.image.load(os.path.join(assets_dir, "cloud_gray4.png")).convert_alpha())

        return num, nubes  
        


    def _spawn_cloud(self, condition: str):
        variant_index, nubes = self._select_Image()
        white = nubes[0]
        gray = nubes[1]

        x = random.randint(-1*(self.window_w//2), self.window_w//2)
        y = random.randint(0, self.window_h)
        speed = random.uniform(5, 10)

        cloud = Cloud(white, gray, x, y, speed, variant_index)

        if condition in ("rain", "rain_light", "storm"):
            cloud.alpha_white = 0
            cloud.alpha_gray = 0
            cloud.start_transition(0, 255, duration=3)  # gris
        elif condition == "clouds":
            cloud.alpha_white = 0
            cloud.alpha_gray = 0
            cloud.start_transition(255, 0, duration=3)  # blanco

        self.clouds.append(cloud)

    def draw_overlay(self, screen: pygame.Surface, player, dt, cond: str):

        # === Inicialización de alpha si no existe ===
        if not hasattr(self, "filter_alpha"):
            self.filter_alpha = 0
            self.target_alpha = 0
            self.filter_speed = 60   # velocidad del fade

        # === NUBES ===
        if cond in ("clear", "clouds", "rain", "rain_light", "storm"):
            for cloud in self.clouds:
                cloud.draw(screen)

        # === OVERLAYS según condición ===
        w, h = screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # --- Determinar target según condición ---
        if cond == "rain_light":
            self.target_alpha = 40
        elif cond == "rain":
            self.target_alpha = 60
        elif cond == "storm":
            self.target_alpha = 90
        else:
            self.target_alpha = 0

        # --- Interpolación gradual ---
        if self.filter_alpha < self.target_alpha:
            self.filter_alpha += self.filter_speed * dt
            if self.filter_alpha > self.target_alpha:
                self.filter_alpha = self.target_alpha
        elif self.filter_alpha > self.target_alpha:
            self.filter_alpha -= self.filter_speed * dt
            if self.filter_alpha < self.target_alpha:
                self.filter_alpha = self.target_alpha

        # --- Dibujar condiciones ---
        if cond in ("rain_light", "rain"):
            self.rain_timer += dt
            if self.rain_timer > 0:
                count = 60 if cond == "rain_light" else 120
                for _ in range(count):
                    x1 = random.randrange(0, w)
                    y1 = random.randrange(0, h)
                    length = 6 if cond == "rain_light" else 10
                    alpha = int(140 * (self.filter_alpha / 90))  
                    pygame.draw.line(
                        overlay,
                        (180, 180, 220, alpha),
                        (x1, y1),
                        (x1 + 2, y1 + length),
                        1
                    )

        elif cond == "storm":
            for _ in range(180):
                x1 = random.randrange(0, w)
                y1 = random.randrange(0, h)
                pygame.draw.line(
                    overlay,
                    (160, 160, 220, 180),
                    (x1, y1),
                    (x1 + 3, y1 + 12),
                    1,
                )

            if random.random() < 0.02:
                flash = pygame.Surface((w, h))
                flash.fill((255, 255, 255))
                screen.blit(flash, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        elif cond == "heat":
            overlay.fill((255, 200, 120, 60))

        elif cond == "fog":
            overlay.fill((220, 220, 220, 200))
            px, py = int(player.x), int(player.y)
            radius = max(60, int(3 * settings.TILE_SIZE))
            pygame.draw.circle(overlay, (0, 0, 0, 0), (px, py), radius)

        elif cond == "wind":
            overlay.fill((90, 120, 160, 40))

        # --- Filtro azul gradual aplicado en cualquier caso ---
        if self.filter_alpha > 0:
            blue_filter = pygame.Surface((w, h), pygame.SRCALPHA)
            # usar SIEMPRE self.filter_alpha, nunca fijo
            blue_filter.fill((20, 40, 100, int(self.filter_alpha)))
            screen.blit(blue_filter, (0, 0))

        screen.blit(overlay, (0, 0))

    def save_state(self) -> list:
        """
        Devuelve una lista de dicts representando todas las nubes.
        Puede ser serializada con pickle .
        """
        return [c.to_dict() for c in self.clouds]

    def load_state(self, clouds_data: list):
        self.clouds = []
        for cdata in clouds_data:
            variant_index = cdata.get("variant_index", 0)
            nubes = self._select_Image_by_index(variant_index)
            white = nubes[0]
            gray = nubes[1]
            cloud = Cloud.from_dict(cdata, white, gray)
            self.clouds.append(cloud)
            
    def _select_Image_by_index(self, num):
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "clouds")
        nubes = []
        nubes.append(pygame.image.load(os.path.join(assets_dir, f"cloud_white{num}.png")).convert_alpha())
        nubes.append(pygame.image.load(os.path.join(assets_dir, f"cloud_gray{num}.png")).convert_alpha())
        return nubes