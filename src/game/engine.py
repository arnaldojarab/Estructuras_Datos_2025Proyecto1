import pygame
from enum import Enum, auto

from . import settings
from .map_loader import MapLoader
from .player import Player
from .ui.menu import MainMenu
from .util import format_mmss
from .util import CountdownTimer

from .weather import WeatherManager
from .job_loader import JobLoader

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

        # 7) Pedidos
        self._init_orders()

    def _init_orders(self):
        """Configura el sistema de los pedidos."""
        self.jobs = JobLoader()          # prepara cliente y contenedor
        self.jobs.load_from_api()        # fetch inicial (bloquea lo justo o hazlo en pantalla de carga)
        self.orders = self.jobs.create_order_manager()
        self._job_offer_elapsed = 5.0  # para controlar cada cuánto ofrecer un nuevo pedido
        self._pickup_markers = []   # [(px, py, id)]
        self._dropoff_markers = []  # [(px, py, id)]

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
            self.player.draw_stamina(self.screen)
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
        ts = settings.TILE_SIZE
        start_cx = 1 * ts + ts // 2
        start_cy = 1 * ts + ts // 2
        self.player.x = start_cx
        self.player.y = start_cy
        #self.player.stamina = 100

        # Reinicia pedidos
        self._pickup_markers = []   # [(px, py)]
        self._dropoff_markers = []  # [(px, py)]

        
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
        self.player.move_with_collision(dx, dy,self.map)
        self.player.update(dt)

        # 3) Timer de partida
        self.timer.tick(dt)
        if self.timer.finished():
            self.state = GameState.MENU
        
        # 4) Actualiza pedidos
        self._job_offer_elapsed += dt
        while self._job_offer_elapsed >= 6.0:
            self.launch_a_job()
            self._job_offer_elapsed -= 10.0
        
        # 5) Verifica proximidad a pickups
        self._check_pickup_proximity()
        self._check_dropoff_proximity()

    def _draw_temporizador(self):
        # HUD: temporizador arriba izquierda 
        timer_surface = self.hud_font.render(
            format_mmss(self.timer.time_left), True, settings.TIMER_TEXT
        )
        self.screen.blit(timer_surface, (10, 8))

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
        self._draw_temporizador()
        self._draw_weather()
        self._draw_job_markers()

    # --------- Clima ---------
    def _update_weather(self, dt: float):
        """Avanza el clima. Si tu WeatherManager usa su propio clock interno,
        puedes ignorar dt; si no, pásalo adentro y ajusta WeatherManager.update(dt)."""
        # En tu versión previa, llamabas self.weather.update() sin dt:
        self.weather.update()
        # Si más adelante migras a update(dt), cámbialo por:
    
    def launch_a_job(self):
      job = self.orders.pop_next_job()
      if not job:
          print("No job available")
          return

      gx, gy = job.pickup
      ts = settings.TILE_SIZE
      px = gx * ts + ts // 2
      py = gy * ts + ts // 2

      self._pickup_markers.append((px, py, job.id))   # amarillo
      # self._dropoff_markers.append((qx, qy, job.id))  # verde
    
    def _draw_job_markers(self):
      # pickups: amarillo
      for (px, py, id) in self._pickup_markers:
          pygame.draw.circle(self.screen, (255, 255, 0), (px, py), 6)      # relleno
          pygame.draw.circle(self.screen, (0, 0, 0), (px, py), 6, 2)       # borde (opcional)
      
      # dropoffs: verde
      for (qx, qy, id) in self._dropoff_markers:
          pygame.draw.circle(self.screen, (0, 200, 0), (qx, qy), 6)
          pygame.draw.circle(self.screen, (0, 0, 0), (qx, qy), 6, 2)

    def _check_pickup_proximity(self):
      """
      Si el jugador está a 3 celdas o menos de un pickup,
      imprime el Job correspondiente y elimina ese marcador de _pickup_markers.
      """
      ts = settings.TILE_SIZE

      # Posición del jugador en coordenadas de grilla
      # (si tu Player ya mantiene grid_pos actualizada, puedes usarla directamente)
      pgx = int(self.player.x // ts)
      pgy = int(self.player.y // ts)

      to_remove_idx = []

      # Recorremos marcadores: (px, py, job_id)
      for idx, marker in enumerate(self._pickup_markers):
          px, py, jid = marker
          mgx = int(px // ts)  # grid x del marcador
          mgy = int(py // ts)  # grid y del marcador

          # Distancia Manhattan en celdas
          dist = abs(mgx - pgx) + abs(mgy - pgy)

          if dist <= 3:
              job = self.jobs.get(jid)
              print(job)
              # Agregar dropoff marker
              dx, dy = job.dropoff
              qx = dx * ts + ts // 2
              qy = dy * ts + ts // 2
              self._dropoff_markers.append((qx, qy, job.id))

              to_remove_idx.append(idx)

      # Elimina en orden inverso para no desplazar índices
      for i in reversed(to_remove_idx):
          self._pickup_markers.pop(i)

    def _check_dropoff_proximity(self):
      """
      Si el jugador está a ≤ 3 celdas de un dropoff:
        - imprime el Job correspondiente
        - elimina ese marcador de _dropoff_markers
      """
      ts = settings.TILE_SIZE
      pgx = int(self.player.x // ts)
      pgy = int(self.player.y // ts)

      to_remove_idx = []

      for idx, (qx, qy, jid) in enumerate(self._dropoff_markers):
          mgx = int(qx // ts)  # grid x del dropoff
          mgy = int(qy // ts)  # grid y del dropoff
          dist = abs(mgx - pgx) + abs(mgy - pgy)

          if dist <= 3:
              job = self.jobs.get(jid)
              print("Reached dropoff:", job)
              to_remove_idx.append(idx)

      for i in reversed(to_remove_idx):
          self._dropoff_markers.pop(i)



