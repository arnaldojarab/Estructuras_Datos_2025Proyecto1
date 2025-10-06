import random
import os
import pygame
import math
from .. import settings
from .weather_Items import Cloud 


class WeatherVisuals:
    """
    Maneja la parte visual del clima (nubes, overlays, efectos).
    Recibe la condición actual desde WeatherManager.
    """

    def __init__(self, window_w, window_h):
        self.clouds = []
        self._cloud_spawn_timer = 0.0
        self._max_clouds = 0
        self.rain_timer = 0.0 

        self.lightning_alpha = 0
        self.lightning = None


        self.wind_offset = 0  # desplazamiento para animar las líneas de viento
        self.wind_speed = 250  # px/s, velocidad de las líneas de viento
        self.wind_gusts = []
        self.max_wind_gusts = 25  # cuántas ráfagas simultáneas

        

        self.filter_speed = 50     # velocidad de transición 

        # Cargar imágenes heat/cold
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "overlays")
        self.heat_image = pygame.image.load(os.path.join(assets_dir, "heat.png")).convert_alpha()
        self.cold_image = pygame.image.load(os.path.join(assets_dir, "cold.png")).convert_alpha()

        # Ventana
        self.window_w = window_w
        self.window_h = window_h

        # alpha por clima
        self.climates = ["clear","clouds","rain_light","rain","storm","fog","wind","heat","cold"]
        self.alphas = {c: 0 for c in self.climates}  
        self.targets = {
            "clear": 0,
            "clouds": 50,
            "rain_light": 40,
            "rain": 60,
            "storm": 90,
            "fog": 70,
            "wind": 50,
            "heat": 120,
            "cold": 120
        }

    def update(self, dt, condition: str, transitioning: bool):
        # actualizar nubes
        for cloud in self.clouds:
            cloud.update(dt)

        # borrar nubes totalmente transparentes y sin transición
        self.clouds = [c for c in self.clouds if not (c.is_fully_transparent() and not c._transitioning)]

        # spawn de nubes
        if self._max_clouds > 0 and condition in ("clouds", "rain", "rain_light", "storm", "fog"):
            self._cloud_spawn_timer += dt
            if self._cloud_spawn_timer > random.uniform(0.3, 0.5):
                if len(self.clouds) < self._max_clouds:
                    self._spawn_cloud(condition)
                self._cloud_spawn_timer = 0

        
        for clima in self.climates:
            target = self.targets.get(clima, 0)
            if clima == condition:
                if self.alphas[clima] < target:
                    self.alphas[clima] += self.filter_speed * dt
                    if self.alphas[clima] > target:
                        self.alphas[clima] = target
            else:
                if self.alphas[clima] > 0:
                    self.alphas[clima] -= self.filter_speed * dt
                    if self.alphas[clima] < 0:
                        self.alphas[clima] = 0

    def handle_condition_change(self, next_condition):
        if next_condition in ("clear", "wind", "cold", "heat"):
            for c in self.clouds:
                c.start_transition(0, 0, duration=5)
            self._max_clouds = 0
        elif next_condition == "clouds":
            self._max_clouds += 50
            self._cloud_spawn_timer = 0
            for c in self.clouds:
                c.start_transition(255, 0, duration=3)
        elif next_condition == "rain_light":
            self._max_clouds += 50
            self._cloud_spawn_timer = 0
            for c in self.clouds:
                c.start_transition(0, 150, duration=3)
        elif next_condition in ("rain", "storm"):
            self._max_clouds += 85
            self._cloud_spawn_timer = 0
            for c in self.clouds:
                c.start_transition(0, 255, duration=3)
        elif next_condition == "fog":
            self._max_clouds += 130
            self._cloud_spawn_timer = 0
            for c in self.clouds:
                c.start_transition(150, 0, duration=3)

    def _select_Image(self):
        num= random.randint(0,4)
        assets_dir = os.path.join(os.path.dirname(__file__), "..","..", "assets", "clouds")
        nubes = []
        nubes.append(pygame.image.load(os.path.join(assets_dir, f"cloud_white{num}.png")).convert_alpha())
        nubes.append(pygame.image.load(os.path.join(assets_dir, f"cloud_gray{num}.png")).convert_alpha())
        return num, nubes  
    
    def _select_lightning_image(self):
        num= random.randint(0,4)
        assets_dir = os.path.join(os.path.dirname(__file__), "..","..", "assets", "lightning")
        return pygame.image.load(os.path.join(assets_dir, f"lightning_{num}.png")).convert_alpha()

    def _spawn_cloud(self, condition: str):
        variant_index, nubes = self._select_Image()
        white = nubes[0]
        gray = nubes[1]

        x = random.randint(-1*(self.window_w//2), self.window_w//2)
        y = random.randint(0, self.window_h)
        speed = random.uniform(5, 10)

        cloud = Cloud(white, gray, x, y, speed, variant_index)

        if condition in ("rain", "storm"):
            cloud.alpha_white = 0
            cloud.alpha_gray = 0
            cloud.start_transition(0, 255, duration=3)
        elif condition == "rain_light":
            cloud.alpha_white = 0
            cloud.alpha_gray = 0
            cloud.start_transition(0, 150, duration=3)
        elif condition == "clouds":
            cloud.alpha_white = 0
            cloud.alpha_gray = 0
            cloud.start_transition(255, 0, duration=3)
        elif condition == "fog":
            cloud.alpha_white = 0
            cloud.alpha_gray = 0
            cloud.start_transition(150, 0, duration=3)

        self.clouds.append(cloud)

    def draw_overlay(self, screen: pygame.Surface, player, dt, cond: str):
        w, h = screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)

        # --- DIBUJAR NUBES ---
        
        for cloud in self.clouds:
            cloud.draw(screen)

        # --- DIBUJAR LLUVIA ---
        if self.alphas["rain_light"] > 0 or self.alphas["rain"] > 0:
            total_alpha = int(max(self.alphas["rain_light"], self.alphas["rain"]) / 90 * 140)
            count = 60 if cond=="rain_light" else 120
            for _ in range(count):
                x1 = random.randrange(0, w)
                y1 = random.randrange(0, h)
                length = 9 if cond=="rain_light" else 10
                pygame.draw.line(overlay, (180,180,220,total_alpha), (x1,y1), (x1+2, y1+length),1)

        # --- DIBUJAR STORM ---
        if self.alphas["storm"] > 0:
            for _ in range(180):
                x1 = random.randrange(0, w)
                y1 = random.randrange(0, h)
                pygame.draw.line(overlay, (160,160,220,180), (x1,y1), (x1+3,y1+12),2)

            if random.random() < 0.009:
                flash = pygame.Surface((w,h))
                flash.fill((255,255,255))
                screen.blit(flash,(0,0),special_flags=pygame.BLEND_RGB_ADD)
                self.lightning_alpha = 255
                self.lightning = self._select_lightning_image()

            if self.lightning_alpha > 0 and self.lightning is not None:
                self.lightning.set_alpha(self.lightning_alpha)
                lx = w//2 - self.lightning.get_width()//2
                ly = 50
                screen.blit(self.lightning,(0,0))
                self.lightning_alpha -= 900*dt
                if self.lightning_alpha < 0:
                    self.lightning_alpha = 0

        # --- IMAGENES HEAT / COLD ---
        if self.alphas["heat"] > 0:
            img = pygame.transform.scale(self.heat_image,(w,h))
            img.set_alpha(int(self.alphas["heat"]))
            screen.blit(img,(0,0))

        if self.alphas["cold"] > 0:
            img = pygame.transform.scale(self.cold_image,(w,h))
            img.set_alpha(int(self.alphas["cold"]))
            screen.blit(img,(0,0))

        # --- FOG ---
        if self.alphas["fog"] > 0:
            overlay.fill((220,220,220,int(self.alphas["fog"])))
            px, py = int(player.x), int(player.y)
            radius = max(60, int(3*settings.TILE_SIZE))
            pygame.draw.circle(overlay, (220,220,220,30), (px, py), radius)

        # --- WIND ---
        if self.alphas["wind"] > 0:
            if len(self.wind_gusts) < self.max_wind_gusts:
                for _ in range(self.max_wind_gusts):
                    x = random.randint(-self.window_w, self.window_w)
                    y = random.randint(0, self.window_h)
                    speed = random.uniform(100, 300)   # velocidad horizontal
                    length = random.randint(40, 100)   # largo de la línea
                    thickness = random.randint(1, 3)   # grosor
                    phase = random.uniform(0, math.pi * 2)   # fase inicial
                    freq = random.uniform(1, 3)               # frecuencia de oscilación
                    amp = random.uniform(2, 6)                # amplitud (qué tanto se mueve)
                    self.wind_gusts.append([x, y, speed, length, thickness, phase, freq, amp])

            # actualizar y dibujar ráfagas
            new_gusts = []
            for gust in self.wind_gusts:
                x, y, speed, length, thickness, phase, freq, amp = gust
                # movimiento base
                x += speed * dt
                # oscilación en Y
                y_offset = math.sin(phase + freq * pygame.time.get_ticks() * 0.001) * amp

                color = (150, 180, 220, int(self.alphas["wind"]))
                pygame.draw.line(
                    overlay,
                    color,
                    (x, y + y_offset),
                    (x + length, y + y_offset),
                    thickness,
                )

                # conservar ráfaga si sigue en pantalla, si no reciclarla
                if x < self.window_w:
                    new_gusts.append([x, y, speed, length, thickness, phase, freq, amp])
                else:
                    new_gusts.append([
                        -random.randint(50, 200),
                        random.randint(0, self.window_h),
                        random.uniform(100, 300),
                        random.randint(40, 100),
                        random.randint(1, 3),
                        random.uniform(0, math.pi * 2),
                        random.uniform(1, 3),
                        random.uniform(2, 6),
                    ])

            self.wind_gusts = new_gusts


        # --- FILTRO AZUL SOLO PARA LLUVIA/STORM ---
        if self.alphas["rain_light"] > 0 or self.alphas["rain"] > 0 or self.alphas["storm"] > 0:
            blue_alpha = max(self.alphas["rain_light"],self.alphas["rain"],self.alphas["storm"])
            blue_filter = pygame.Surface((w,h),pygame.SRCALPHA)
            blue_filter.fill((20,40,100,int(blue_alpha)))
            screen.blit(blue_filter,(0,0))

        screen.blit(overlay,(0,0))

    # --- SERIALIZACIÓN DE NUBES ---
    def save_state(self) -> dict:
        return {
            "clouds": [c.to_dict() for c in self.clouds],
            "alphas": self.alphas,
            "_cloud_spawn_timer": self._cloud_spawn_timer,
            "_max_clouds": self._max_clouds,
            "wind_gusts": self.wind_gusts,
            "lightning_alpha": self.lightning_alpha
        }

    def load_state(self, data: dict):
        # Restaurar nubes
        clouds_data = data.get("clouds", [])
        self.clouds = []
        for cdata in clouds_data:
            variant_index = cdata.get("variant_index", 0)
            nubes = self._select_Image_by_index(variant_index)
            white, gray = nubes
            cloud = Cloud.from_dict(cdata, white, gray)
            self.clouds.append(cloud)

        # Restaurar parámetros visuales
        self.alphas = data.get("alphas", self.alphas)
        self._cloud_spawn_timer = data.get("_cloud_spawn_timer", 0.0)
        self._max_clouds = data.get("_max_clouds", 0)
        self.wind_gusts = data.get("wind_gusts", [])
        self.lightning_alpha = data.get("lightning_alpha", 0)

    def _select_Image_by_index(self, num):
        assets_dir = os.path.join(os.path.dirname(__file__), "..","..", "assets", "clouds")
        nubes = []
        nubes.append(pygame.image.load(os.path.join(assets_dir, f"cloud_white{num}.png")).convert_alpha())
        nubes.append(pygame.image.load(os.path.join(assets_dir, f"cloud_gray{num}.png")).convert_alpha())
        return nubes
    
