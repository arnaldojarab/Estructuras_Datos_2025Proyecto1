import pygame
from enum import Enum, auto

from . import settings
from .map_loader import MapLoader
from .player import Player
from .ui.menu import MainMenu
from .util import format_mmss
from .util import CountdownTimer

from .weather import WeatherManager

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()

class Game:
    def __init__(self):
        pygame.init()

        # 1) Cargar mapa
        self.map = MapLoader().load_default()

        # 2) Ventana del tamaño del mapa
        window_w = self.map.width * settings.TILE_SIZE
        window_h = self.map.height * settings.TILE_SIZE
        self.screen = pygame.display.set_mode((window_w, window_h))
        pygame.display.set_caption("Courier Quest")

        # 3) Reloj y jugador
        self.clock = pygame.time.Clock()
        self.player = Player((0, 0))

        # 4) UI: menú + fuentes HUD 
        self.menu = MainMenu((window_w, window_h))
        self.hud_font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)
        self.small_font = pygame.font.Font(settings.UI_FONT_NAME, 18)  # para texto de clima

        # 5) Estado + timer
        self.state = GameState.MENU
        self.timer = CountdownTimer(settings.TIMER_START_SECONDS)

        # 6) Clima
        self._init_weather()

    def _init_weather(self):
        """Configura el sistema de clima."""
        self.weather = WeatherManager()  

    # --------- Ciclo principal ---------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(settings.FPS) / 1000.0

            # Selección de handlers por estado
            handle_event, update, draw = self._get_state_handlers()

            # EVENT
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    handle_event(event)

            # UPDATE
            update(dt)

            # DRAW
            self.screen.fill(settings.MENU_BG)
            # Dibuja mundo de fondo siempre:
            self.map.draw(self.screen)
            self.player.draw(self.screen)
            draw()

            pygame.display.flip()

        pygame.quit()

    # --------- Helpers ---------
    def _get_state_handlers(self):
        """Devuelve (handle_event, update, draw) según el estado actual."""
        if self.state == GameState.MENU:
            return (self._handle_event_menu, self._update_menu, self._draw_menu)
        else:  # GameState.PLAYING
            return (self._handle_event_play, self._update_play, self._draw_play)

    def _reset_run(self):
        """Reinicia partida al empezar a jugar."""
        self.timer.reset()
        # reset simple del jugador (ajústalo si tienes método reset())
        self.player.grid_pos = (1, 1)
        self.player.pixel_pos = [
            self.player.grid_pos[0] * settings.TILE_SIZE,
            self.player.grid_pos[1] * settings.TILE_SIZE,
        ]
        # Opcional: reiniciar clima al comenzar una nueva run
        self._init_weather()

    # --------- Estado: MENU ---------
    def _handle_event_menu(self, event: pygame.event.Event):
        action = self.menu.handle_event(event)
        if action == "start":
            self._reset_run()
            self.state = GameState.PLAYING

    def _update_menu(self, dt: float):
        # Aquí podrías animar el menú si quisieras
        pass

    def _draw_menu(self):
        # Panel + botón (overlay)
        self.menu.draw(self.screen)

    # --------- Estado: PLAYING ---------
    def _handle_event_play(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU

    def _update_play(self, dt: float):
        # 1) Actualiza clima (sin dibujar)
        self._update_weather(dt)

        # 2) Lee input y aplica multiplicador de velocidad del clima
        keys = pygame.key.get_pressed()
        base_px_per_sec = 120  # tu demo actual
        speed_mult = self.weather.current_multiplier()  # de tu WeatherManager
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * base_px_per_sec * dt * speed_mult
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * base_px_per_sec * dt * speed_mult
        self.player.pixel_move(dx, dy)

        # 3) Timer de partida
        self.timer.tick(dt)
        if self.timer.finished():
            self.state = GameState.MENU

    def _draw_play(self):
        # HUD: temporizador arriba izquierda 
        timer_surface = self.hud_font.render(
            format_mmss(self.timer.time_left), True, settings.TIMER_TEXT
        )
        self.screen.blit(timer_surface, (10, 8))

        # HUD: clima (condición, multiplicador y tiempo restante del estado)
        info = self.weather.debug_info()
        weather_text = f"{info['condition']}  x{info['multiplier']}  t={info['time_left']}"
        weather_surface = self.small_font.render(weather_text, True, (255, 255, 255))

        margin = 10
        x = margin
        y = self.screen.get_height() - weather_surface.get_height() - margin

        self.screen.blit(weather_surface, (x, y))

    # --------- Clima ---------
    def _update_weather(self, dt: float):
        """Avanza el clima. Si tu WeatherManager usa su propio clock interno,
        puedes ignorar dt; si no, pásalo adentro y ajusta WeatherManager.update(dt)."""
        # En tu versión previa, llamabas self.weather.update() sin dt:
        self.weather.update()
        # Si más adelante migras a update(dt), cámbialo por:


