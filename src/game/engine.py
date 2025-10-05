import pygame
import os
import pickle
import tempfile
import re
from . import settings
from .map_logic.map_loader import MapLoader
from .player import Player
from .ui.menu import MainMenu

from .weather_logic.weather import WeatherManager

from .statistics_logic.statistic_logic import statisticLogic

from .jobs_logic.job_logic import JobLogic
from .ui.inventory import InventoryUI
from .ui.game_over import GameOverLogic
from .ui.pause_menu import PauseMenu
from .game_state import GameState

from .sounds import SoundManager

class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 256)
        pygame.init()

        # 1) Cargar mapa
        self.map = MapLoader().load_default()

        # 2) Ventana del tamaño del mapa
        window_w = self.map.width * settings.TILE_SIZE
        window_h = self.map.height * settings.TILE_SIZE
        self.screen = pygame.display.set_mode((window_w, window_h))
        pygame.display.set_caption("Courier Quest")
        # Cargar icono (ruta relativa a este archivo)
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.normpath(
                os.path.join(base_dir, "..", "assets", "images", "kimby_icon_3.png")
            )
            icon = pygame.image.load(icon_path).convert_alpha()

            # Escalar a 32x32 para que se vea bien como ícono de ventana
            icon = pygame.transform.smoothscale(icon, (32, 32))

            pygame.display.set_icon(icon)
        except Exception:
            # Si falla, simplemente no cambia el icono
            pass

        # 3) Reloj y jugador
        self.clock = pygame.time.Clock()
        self.player = Player((0, 0))

        # 4) UI: menú + fuentes HUD 
        self.menu = MainMenu((window_w, window_h), self._load_game)
        self.hud_font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)
        self.small_font = pygame.font.Font(settings.UI_FONT_NAME, 18)  # para texto de clima

        self.pause_menu = PauseMenu((window_w, window_h), self.hud_font, self.small_font)

        # 5) Estado + timer
        self.state = GameState.MENU
        self.statistics_logic = statisticLogic()

        # 6) Clima
        self.weather = WeatherManager(window_w,window_h) 

        # 7) Pedidos
        self.job_logic = JobLogic(tile_size=settings.TILE_SIZE)
        self.job_logic.reset()

        #8) UI: Inventario
        ##self.inventory_ui = InventoryUI(self.screen.get_width(), self.screen.get_height())
        self.inventory_ui = InventoryUI()
        self.inventory_ui.set_jobs([])  # arranca vacío; se refresca en _inventory_update

        # 9) Game Over Logic
        self.game_over = GameOverLogic(self.hud_font, self.small_font)

        #10) SoundManager para reproducir sonidos jeje
        pygame.mixer.set_num_channels(16)  # opcional, por si hay varios SFX
        self.sfx = SoundManager()    

        #11) Pausa Logic
        self.pause_menu = PauseMenu((window_w, window_h), self.hud_font, self.small_font, self._save_game)
        self.sfx.set_master_volume(1)


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
        elif self.state == GameState.PAUSED:
            return (self._handle_event_paused, self._update_paused, self._draw_paused)
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
      elif action == "loaded":
          # ya se llamo a _load_game desde el menú y devolvió True
          self.state = GameState.PLAYING

    def _update_menu(self, dt: float):
        pass

    def _draw_menu(self):
        # Panel + botón (overlay)
        self.menu.draw(self.screen)
    
    # --------- Estado: PAUSED ---------
    def _handle_event_paused(self, event: pygame.event.Event):
        action = self.pause_menu.handle_event(event)
        if action == "exit":
            self._reset_run()
            self.menu.reset_menu()
            self.state = GameState.MENU
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
            return
    
    def _update_paused(self, dt: float):
        pass
    
    def _draw_paused(self):
        self.pause_menu.draw(self.screen)

    # --------- Estado: PLAYING ---------
    def _handle_event_play(self, event: pygame.event.Event):
        # Salir al menú
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
            return
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.state = GameState.INVENTORY
            return

        # Deshacer posición con tecla C
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            # si tu undo_position() devuelve True cuando logró deshacer, úsalo
            try:
                did_undo = self.player.undo_position()
            except Exception:
                did_undo = False  # evita crashear si algo falla accidentalmente

            if did_undo is None or did_undo is True:
                # Sonar trompeta con pequeño fade para evitar "click"
                #self.sfx.play("undo", fade_ms=20)

                tx = int(self.player.x // settings.TILE_SIZE)
                ty = int(self.player.y // settings.TILE_SIZE)
            return
        

    def _update_play(self, dt: float):
        # 1) Actualiza clima (sin dibujar)
        self._update_weather(dt)

        # 2) Lee input y aplica multiplicador de velocidad del clima
        keys = pygame.key.get_pressed()
        base_px_per_sec = settings.TILE_SIZE * 8  # Modificar para ajustar velocidad base
        speed_mult = self.current_speed()

        # Soporte flechas + WASD
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]
        up    = keys[pygame.K_UP]    or keys[pygame.K_w]

        dx = (right - left) * base_px_per_sec * dt * speed_mult
        dy = (down - up)   * base_px_per_sec * dt * speed_mult

        # Normaliza velocidad en diagonal (sin ventaja al moverse en 45°)
        if dx != 0 and dy != 0:
            diag = 0.70710678  # 1/sqrt(2)
            dx *= diag
            dy *= diag

        self.player.move_with_collision(dx, dy, self.map, self.job_logic.getWeight(), self.weather.get_current_condition())
        self.player.update(dt, self.job_logic.getWeight())


        # 3) Actualiza Estadísticas
        currentMoney = self.job_logic.getMoney()
        currentReputation = self.job_logic.getReputation()
        self.statistics_logic.update(dt, currentMoney, currentReputation)
        if self.statistics_logic.check_time_finished() or currentReputation < settings.MIN_REPUTACION:
            self.game_over.set_title("GAME OVER (you lose)", win=False)
            self.game_over.enter(self.get_score())
            self.state = GameState.GAME_OVER
        if currentMoney >= settings.META_INGRESOS:
            self.game_over.set_title("CONGRATS! (you win)", win=True)
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
            self._reset_run()
            self.menu.reset_menu()
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
        return self.player.get_speed(self.job_logic.getWeight()) * self.weather.current_multiplier()  * self.map.surface_weight(self.player.x, self.player.y) * self.job_logic.getRepSpeed() 


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
        #self.inventory_ui.update(dt)
        # Refresca con el inventario real (preserva selección)
        self.inventory_ui.set_jobs(self.job_logic.getInventory(), keep_selection=True)
        # Pasa stats al encabezado

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
    
    def _save_game(self, filename: str) -> bool:
      # --- sanea y normaliza el nombre ---
      def _sanitize(name: str) -> str:
          name = (name or "slot-1").strip()
          # Solo letras/números/espacios/guion/guion_bajo/punto
          name = re.sub(r"[^A-Za-z0-9 _\-.]", "_", name)
          # Colapsa espacios múltiples
          name = re.sub(r"\s+", " ", name)
          return name

      safe_name = _sanitize(filename)
      if not safe_name.lower().endswith(".sav"):
          safe_name += ".sav"

      # Directorio destino absoluto: /saves
      base_dir = os.path.dirname(os.path.abspath(__file__))
      # saves_dir = os.path.join(os.sep, "saves")
      saves_dir = os.path.join(base_dir, "..", "..", "saves")
      os.makedirs(saves_dir, exist_ok=True)
      final_path = os.path.join(saves_dir, safe_name)

      data = self.get_current_data()

      # Escritura atómica: primero a archivo temporal, luego replace
      tmp_file = None
      try:
          tmp = tempfile.NamedTemporaryFile("wb", dir=saves_dir, delete=False)
          tmp_file = tmp.name
          with tmp:
              pickle.dump(data, tmp, protocol=pickle.HIGHEST_PROTOCOL)
          os.replace(tmp_file, final_path)
          tmp_file = None
          return True
      except Exception:
          return False
      finally:
          # Limpieza si falló antes del replace
          if tmp_file and os.path.exists(tmp_file):
              try:
                  os.remove(tmp_file)
              except Exception:
                  pass

    def _load_game(self, filename: str) -> bool:
      if not filename.lower().endswith(".sav"):
          filename += ".sav"

      # Same directory convention as _save_game
      base_dir = os.path.dirname(os.path.abspath(__file__))
      saves_dir = os.path.join(base_dir, "..", "..", "saves")
      path = os.path.join(saves_dir, filename)

      try:
          if not os.path.exists(path):
              return False

          with open(path, "rb") as f:
              state = pickle.load(f)

          if not isinstance(state, dict):
              return False

          self.set_current_data(state)
          return True

      except Exception as e:
          return False

    def get_current_data(self) -> dict:
        """Prepara un dict con el estado actual para guardado."""
        return {
            "map_logic": self.map.save_map(),
            "player": self.player.save_state(),
            "statistics": self.statistics_logic.save_state(),
            "job_logic": self.job_logic.save_state(),
            "weather": self.weather.save_state(),
        }
    
    def set_current_data(self, data: dict) -> bool:
        """Restaura el estado desde un dict (cargado de archivo)."""
        if not isinstance(data, dict):
            return False

        # Validar presencia y tipo de cada sub-estado (debe ser dict)
        map_state       = data.get("map_logic")
        player_state    = data.get("player")
        stats_state     = data.get("statistics")
        jobs_state      = data.get("job_logic")
        weather_state   = data.get("weather")

        if not all(isinstance(x, dict) for x in (map_state, player_state, stats_state, jobs_state, weather_state)):
            return False

        ok = True

        ok &= bool(self.map.load_map(map_state))
        ok &= bool(self.player.load_state(player_state))
        ok &= bool(self.job_logic.load_state(jobs_state))
        ok &= bool(self.weather.load_state(weather_state))
        ok &= bool(self.statistics_logic.load_state(stats_state))

        return ok




