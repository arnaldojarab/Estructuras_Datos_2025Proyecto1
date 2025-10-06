import os
import pygame
from .. import settings
from .button import Button
from typing import Callable, Optional

# constantes locales
PM_TITLE_Y_RATIO = 0.12
PM_NAME_PROMPT_Y_RATIO = 0.32
PM_NAME_BOX_Y_RATIO = 0.45
PM_NAME_HINT_Y_RATIO = 0.65
PM_CONTINUE_BTN_Y_RATIO = 0.72

PM_NAME_BOX_WIDTH = 460
PM_NAME_BOX_HEIGHT = 72
PM_NAME_BOX_BORDER_RADIUS = 8

PM_BUTTON_PADDING_X = 28
PM_BUTTON_PADDING_Y = 12
PM_BUTTON_BORDER_RADIUS = 10


class PauseMenu:
    def __init__(self, screen_size, hud_font: pygame.font.Font, small_font: pygame.font.Font, on_save: Optional[Callable[[str], bool]] = None):
        self.w, self.h = screen_size
        self.font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)
        self.on_save = on_save
        self.hud_font = hud_font
        self.small_font = small_font

        # Estado general del menú de pausa
        self.phase = "MAIN"        # MAIN | NAME | RESULT

        # Estado de sonido
        self.muted = False

        # Iconos (cargados una vez)
        self.icon_muted = self._load_icon("muted.png", size=40)     # círculo ~48, icono 40
        self.icon_unmuted = self._load_icon("unmuted.png", size=40)

        # Elementos UI
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)
        self.btn_save = None

        # Botón circular de mute (se posiciona en _layout)
        self.mute_center = (0, 0)
        self._mute_rect = None  # bounding box del icono
        self._layout((self.w, self.h))

        self._fname_buf = "slot-1"    # valor por defecto, editable
        self._fname_max = 60          # máximo de caracteres

        # Resultado del guardado
        self._save_ok: Optional[bool] = None

        self.btn_continue = None

        # Control de entrada de texto (TEXTINPUT)
        self._ti_active = False

    # -------- Public API --------
    def getMuted(self) -> bool:
        return self.muted

    def resize(self, screen_size):
        self._layout(screen_size)

    def draw(self, surface: pygame.Surface):
        
        current_size = surface.get_size()
        if current_size != (self.w, self.h):
            self._layout(current_size)

        pygame.draw.rect(surface, settings.MENU_BG, self.panel_rect)

        if self.phase == "MAIN":
            self._draw_main(surface)
        elif self.phase == "NAME":
            self._draw_name(surface)
        elif self.phase == "RESULT":
            self._draw_result(surface)

    def _draw_main(self, surface: pygame.Surface):
      self.btn_save.draw(surface)
      self.btn_exit.draw(surface)
      mouse_pos = pygame.mouse.get_pos()
      icon = self.icon_muted if self.muted else self.icon_unmuted
      if icon:
          base_w, base_h = icon.get_size()

          if self._mute_rect is not None:
              is_hover = self._mute_rect.collidepoint(mouse_pos)
          else:
              temp_rect = icon.get_rect(center=self.mute_center)
              is_hover = temp_rect.collidepoint(mouse_pos)

          scale = 1.12 if is_hover else 1.0
          draw_w = int(base_w * scale)
          draw_h = int(base_h * scale)

          scaled = pygame.transform.smoothscale(icon, (draw_w, draw_h))
          rect = scaled.get_rect(center=self.mute_center)
          self._mute_rect = rect
          surface.blit(scaled, rect)

    def _draw_name(self, surface: pygame.Surface):
      W, H = self.w, self.h

      # Título
      title = "Guardar Partida"
      title_surf = self.font.render(title, True, settings.GO_TEXT_COLOR)
      surface.blit(title_surf, (W // 2 - title_surf.get_width() // 2, int(H * PM_TITLE_Y_RATIO)))

      # Prompt
      prompt = "Ingrese el nombre del archivo"
      prompt_surf = self.font.render(prompt, True, settings.GO_TEXT_COLOR)
      surface.blit(prompt_surf, (W // 2 - prompt_surf.get_width() // 2, int(H * PM_NAME_PROMPT_Y_RATIO)))

      # Caja de entrada
      rect = pygame.Rect(W // 2 - PM_NAME_BOX_WIDTH // 2, int(H * PM_NAME_BOX_Y_RATIO),
                        PM_NAME_BOX_WIDTH, PM_NAME_BOX_HEIGHT)
      pygame.draw.rect(surface, (240, 240, 240), rect, border_radius=PM_NAME_BOX_BORDER_RADIUS)

      # Texto actual
      text_surf = self.font.render(self._fname_buf, True, settings.TEXT_DARK)
      surface.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                              rect.centery - text_surf.get_height() // 2))
      # Hint
      hint = "Enter para confirmar"
      hint_surf = self.small_font.render(hint, True, settings.GO_TEXT_COLOR)
      surface.blit(hint_surf, (W // 2 - hint_surf.get_width() // 2, int(H * PM_NAME_HINT_Y_RATIO)))

    def _draw_result(self, surface: pygame.Surface):
      W, H = self.w, self.h

      if self._save_ok:
          title = "Guardado Correctamente"
          title_surf = self.font.render(title, True, settings.TEXT_GREEN)
      else:
        title = "No se pudo guardar la partida"
        title_surf = self.font.render(title, True, settings.TEXT_RED)

      surface.blit(title_surf, (W // 2 - title_surf.get_width() // 2, int(H * PM_TITLE_Y_RATIO)))

      if self.btn_continue:
          self.btn_continue.draw(surface)

    # -------- Internals --------
    def _layout(self, screen_size):
        """Recalcula posiciones para centrar el botón y ubicar el mute."""
        self.w, self.h = screen_size
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)

        # Botón central: Guardar partida
        btn_w, btn_h = 260, 54
        btn_x = self.w // 2 - btn_w // 2
        btn_y = self.h // 2 - btn_h // 2

        self.btn_save = Button(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="Guardar partida",
            font=self.font,
            bg=settings.BUTTON_BG,
            bg_hover=settings.BTN_BG_HOVER,
            fg=settings.TEXT_DARK,
        )

        # Botón "Salir"
        gap_between = 16
        exit_y = btn_y + btn_h + gap_between
        self.btn_exit = Button(
            rect=pygame.Rect(btn_x, exit_y, btn_w, btn_h),
            text="Salir",
            font=self.font,
            bg=settings.BUTTON_BG,
            bg_hover=settings.BTN_BG_HOVER,
            fg=settings.TEXT_DARK,
        )

        # Posicionar el botón circular de mute
        gap_below = 72
        self.mute_center = (self.w // 2, exit_y + btn_h + gap_below)

        if self.phase == "RESULT":
            cont_surf = self.font.render("Continuar", True, settings.TEXT_DARK)
            btn_w2 = cont_surf.get_width() + PM_BUTTON_PADDING_X * 2
            btn_h2 = cont_surf.get_height() + PM_BUTTON_PADDING_Y * 2
            btn_x2 = self.w // 2 - btn_w2 // 2
            btn_y2 = int(self.h * PM_CONTINUE_BTN_Y_RATIO)
            self.btn_continue = Button(
                rect=pygame.Rect(btn_x2, btn_y2, btn_w2, btn_h2),
                text="Continuar",
                font=self.font,
                bg=settings.BUTTON_BG,
                bg_hover=settings.BTN_BG_HOVER,
                fg=settings.TEXT_DARK,
            )
        else:
            self.btn_continue = None

    def _load_icon(self, filename: str, size: int) -> pygame.Surface | None:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.normpath(os.path.join(base_dir, "..", "..", "assets", "ui_icons", filename))
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (size, size))
            return img
        except Exception:
            return None
        
    def handle_event(self, event) -> str | None:
      # ------- FASE MAIN -------
      if self.phase == "MAIN":
          if self.btn_save.handle_event(event):
              self.phase = "NAME"
              self._fname_buf = "slot-1"
              try:
                pygame.key.start_text_input()
                self._ti_active = True
              except Exception:
                self._ti_active = False

              return None
          if self.btn_exit.handle_event(event):
            return "exit"

          # Toggle de mute por clic en el icono
          if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
              if self._mute_rect and self._mute_rect.collidepoint(event.pos):
                  self.muted = not self.muted
          return None

      # ------- FASE NAME (entrada de texto) -------
      if self.phase == "NAME":
          if event.type == pygame.TEXTINPUT:
              if len(self._fname_buf) < self._fname_max:
                  self._fname_buf += event.text
              return None

          # Teclas de control / fallback
          if event.type == pygame.KEYDOWN:
              if event.key == pygame.K_BACKSPACE:
                  self._fname_buf = self._fname_buf[:-1]
                  return None
              if event.key == pygame.K_RETURN:
                  fname = self._fname_buf if len(self._fname_buf) > 0 else "slot-1"
                  ok = False
                  if self.on_save:
                      ok = bool(self.on_save(fname))   # on_save: (str) -> bool
                  self._save_ok = ok
                  self.phase = "RESULT"
                  try:
                      pygame.key.stop_text_input()
                  except Exception:
                      pass
                  finally:
                      self._ti_active = False

                  self._layout((self.w, self.h))
                  return None
              if event.key == pygame.K_ESCAPE:
                  try:
                      pygame.key.stop_text_input()
                  except Exception:
                      pass
                  finally:
                      self._ti_active = False
                  self.phase = "MAIN"
                  self._layout((self.w, self.h))
                  return None

              # Fallback: agregar carácter desde KEYDOWN si trae unicode
              if (not self._ti_active) and event.unicode and len(event.unicode) == 1 and event.unicode not in ("\r", "\n"):
                  if len(self._fname_buf) < self._fname_max:
                      self._fname_buf += event.unicode
                  return None


          return None

      # ------- FASE RESULT (pantalla de confirmación) -------
      if self.phase == "RESULT":
          if self.btn_continue and self.btn_continue.handle_event(event):
              # Volver al menú de pausa
              self.phase = "MAIN"
              try:
                  pygame.key.stop_text_input()
              except Exception:
                  pass
              self._layout((self.w, self.h))
              return "back"
          return None

      return None


