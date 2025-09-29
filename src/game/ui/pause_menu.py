import os
import pygame
from .. import settings
from .button import Button


class PauseMenu:
    def __init__(self, screen_size):
        self.w, self.h = screen_size
        self.font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)

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
        self._mute_rect = None  # bounding box del icono (para hover/click)
        self._layout((self.w, self.h))

    # -------- Public API --------
    def getMuted(self) -> bool:
        return self.muted

    def resize(self, screen_size):
        self._layout(screen_size)

    def draw(self, surface: pygame.Surface):
        # Recalcular si cambia el tamaño de la ventana
        current_size = surface.get_size()
        if current_size != (self.w, self.h):
            self._layout(current_size)

        # Fondo del panel
        pygame.draw.rect(surface, settings.MENU_BG, self.panel_rect)

        # Botón central
        self.btn_save.draw(surface)

        # --- Botón de mute ---
        mouse_pos = pygame.mouse.get_pos()
        icon = self.icon_muted if self.muted else self.icon_unmuted

        if icon:
            # base: centrado en self.mute_center
            base_w, base_h = icon.get_size()

            # detectar hover usando el rect actual (si ya fue calculado),
            # o una caja centrada provisional del tamaño base
            if self._mute_rect is not None:
                is_hover = self._mute_rect.collidepoint(mouse_pos)
            else:
                temp_rect = icon.get_rect(center=self.mute_center)
                is_hover = temp_rect.collidepoint(mouse_pos)

            # factor de escala (sutil) al hacer hover
            scale = 1.12 if is_hover else 1.0
            draw_w = int(base_w * scale)
            draw_h = int(base_h * scale)

            scaled = pygame.transform.smoothscale(icon, (draw_w, draw_h))
            rect = scaled.get_rect(center=self.mute_center)

            # guardar rect para hover/click de siguientes frames
            self._mute_rect = rect

            # dibujar ícono
            surface.blit(scaled, rect)

    # -------- Internals --------
    def _layout(self, screen_size):
        """Recalcula posiciones para centrar el botón y ubicar el mute."""
        self.w, self.h = screen_size
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)

        # Tamaños
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

        # Posicionar el botón circular de mute
        gap_below = 72  # separación por debajo del botón central
        self.mute_center = (self.w // 2, btn_y + btn_h + gap_below)

    def _load_icon(self, filename: str, size: int) -> pygame.Surface | None:
        """Carga un PNG desde src/assets/ui_icons/ y lo escala al tamaño indicado (con alpha)."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.normpath(os.path.join(base_dir, "..", "..", "assets", "ui_icons", filename))
            img = pygame.image.load(path).convert_alpha()
            # Mantener proporción al escalar dentro de un cuadrado size×size
            img = pygame.transform.smoothscale(img, (size, size))
            return img
        except Exception:
            return None
        
    def handle_event(self, event) -> str | None:
      if self.btn_save.handle_event(event):
          return "save"

      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
          if self._mute_rect and self._mute_rect.collidepoint(event.pos):
              self.muted = not self.muted  

      return None

