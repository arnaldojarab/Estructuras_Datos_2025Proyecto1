import pygame

from . import settings
from .map_logic.map_loader import MapLoader
from .player import Player
from .ui.menu import MainMenu

from .weather_logic.weather import WeatherManager

from .statistics_logic.statistic_logic import statisticLogic

from .jobs_logic.job_logic import JobLogic
from .ui.inventory import InventoryUI
from .ui.game_over import GameOverLogic
from .game_state import GameState

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
        self.statistics_logic = statisticLogic()

        # 6) Clima
        self.weather = WeatherManager(window_w,window_h) 

        # 7) Pedidos
        self.job_logic = JobLogic(tile_size=settings.TILE_SIZE)
        self.job_logic.reset()

        #8) UI: Inventario
        self.inventory_ui = InventoryUI(self.screen.get_width(), self.screen.get_height(), cols=6)
        self.inventory_ui.set_jobs([])  # arranca vacío; se refresca en _inventory_update

        # 9) Game Over Logic
        self.game_over = GameOverLogic(self.hud_font, self.small_font)

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
            self.weather.draw_weather_overlay(self.screen, self.player,dt)
            self.player.draw_stamina(self.screen)
            draw()

            pygame.display.flip()

        pygame.quit()

    # --------- Helpers ---------
    def _get_state_handlers(self):
        """Devuelve (handle_event, update, draw) según el estado actual."""
        if self.state == GameState.MENU:
            return (self._handle_event_menu, self._update_menu, self._draw_menu)
        elif self.state == GameState.INVENTORY:
            return(self._inventory_handle_event, self._inventory_update, self._inventory_draw)
        elif self.state == GameState.GAME_OVER:
          return (self._handle_event_gameover, self._update_gameover, self._draw_gameover)
        else:  # GameState.PLAYING
            return (self._handle_event_play, self._update_play, self._draw_play)
        

    def _reset_run(self):
        """Reinicia partida al empezar a jugar."""
        # reset de estaditicas
        self.statistics_logic.reset()
        
        # reset simple del jugador
        self.player.reset()

        # Reinicia pedidos
        self.job_logic.reset()
        
        # Reiniciar clima
        self.weather.reset()

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
        # Salir al menú
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            return
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.state = GameState.INVENTORY
            return

        # Deshacer posición con tecla C
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            self.player.undo_position()
            return

    def _update_play(self, dt: float):
        # 1) Actualiza clima (sin dibujar)
        self._update_weather(dt)

        # 2) Lee input y aplica multiplicador de velocidad del clima
        keys = pygame.key.get_pressed()
        base_px_per_sec = settings.TILE_SIZE * 8 # Modificar para ajustar velocidad base
        #speed_mult = self.weather.current_multiplier()  # de tu WeatherManager
        speed_mult = self.current_speed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * base_px_per_sec * dt * speed_mult
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * base_px_per_sec * dt * speed_mult
        self.player.move_with_collision(dx, dy,self.map)
        self.player.update(dt, self.job_logic.getWeight())

        # 3) Actualiza Estadísticas
        self.statistics_logic.update(dt, self.job_logic.getMoney(), self.job_logic.getReputation())
        if self.statistics_logic.check_time_finished():
            self.game_over.enter(self.get_score())
            self.state = GameState.GAME_OVER
        
        # 4) Actualiza pedidos
        self.job_logic.update(dt, self.player.x, self.player.y)

    # --------- Estado: GAME OVER ---------
    def _handle_event_gameover(self, event: pygame.event.Event):
      self.game_over.handle_event(event)

    def _update_gameover(self, dt: float):
        self.game_over.update(dt)
        if self.game_over.is_done():
            self.state = GameState.MENU

    def _draw_gameover(self):
        self.game_over.draw(self.screen)


    def _draw_weather(self):
        # HUD: clima (condición, multiplicador y tiempo restante del estado)
        info = self.weather.debug_info()
        weather_text = f"{info['condition']}  x{info['multiplier']}  t={info['time_left']}"
        weather_surface = self.small_font.render(weather_text, True, (255, 255, 255))

        margin = 10
        x = margin
        y = self.screen.get_height() - weather_surface.get_height() - margin

        self.screen.blit(weather_surface, (x, y))

    def _draw_play(self):
        #self._draw_temporizador()
        self._draw_weather()

        self.job_logic.draw(self.screen)
        self.statistics_logic.draw(self.screen)

    # --------- Clima ---------
    def _update_weather(self, dt: float):
        """Avanza el clima. Si tu WeatherManager usa su propio clock interno,
        puedes ignorar dt; si no, pásalo adentro y ajusta WeatherManager.update(dt)."""
        # En tu versión previa, llamabas self.weather.update() sin dt:
        self.weather.update(dt)
        # Si más adelante migras a update(dt), cámbialo por:
    
    def current_speed(self):
        return self.player.get_speed(self.job_logic.getWeight()) * self.weather.current_multiplier()  * self.map.surface_weight(self.player.x, self.player.y)


    def _inventory_handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_e, pygame.K_ESCAPE):
                self.state = GameState.PLAYING
                return
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # Seleccionar como current job
                sel_id = self.inventory_ui.selected_job_id()
                if sel_id:
                    self.job_logic.setCurrentJob(sel_id)  # Actualiza job actual en JobLogic
                return
        # Reenviar eventos a la UI (clics y flechas)
        self.inventory_ui.handle_event(event)


    def _inventory_update(self, dt):
        self.inventory_ui.update(dt)
        # Refresca con el inventario real (preserva selección)
        self.inventory_ui.set_jobs(self.job_logic.getInventory(), keep_selection=True)
        # Pasa stats al encabezado
        self.inventory_ui.set_header_stats(
            money=self.job_logic.getMoney(),
            weight=self.job_logic.getWeight(),
            reputation=self.job_logic.getReputation()
    )

    def _inventory_draw(self):
        # Tu loop ya dibuja: fondo/mapa/jugador/estamina
        # Aquí solo pintás el overlay del inventario
        self.inventory_ui.draw(self.screen)

    def get_score(self) -> float:
      # TODO: ajustar fórmula de score
      """
      score_base = suma de pagos * pay_mult (por reputación alta)
      bonus_tiempo = +X si terminas antes del 20% del tiempo restante
      penalizaciones = -Y por cancelaciones/caídas (opcional)
      score = score_base + bonus_tiempo - penalizaciones
      """
      return self.job_logic.getMoney()




