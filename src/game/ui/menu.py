import os
import pygame
from .. import settings
from .button import Button

class MainMenu:
    def __init__(self, screen_size):
        self.w, self.h = screen_size
        self.font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)

        # icon (will be loaded once)
        self.icon_surf = self._load_circular_icon(size=224)
        self.icon_rect = pygame.Rect(0, 0, 0, 0)

        # placeholders; computed in _layout()
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)
        self.btn_start = None
        self.btn_load = None
        self._layout((self.w, self.h))

    def _load_circular_icon(self, size: int) -> pygame.Surface | None:
        """Load the icon and make it circular with per-pixel alpha."""
        try:
            # Build path relative to this file: src/game/ui/menu.py -> ../../assets/images/kimby_icon_1.png
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.normpath(os.path.join(base_dir, "..", "..", "assets", "images", "kimby_icon_2.png"))

            img = pygame.image.load(icon_path).convert_alpha()
            # fit square
            min_side = min(img.get_width(), img.get_height())
            img = img.subsurface(pygame.Rect(
                (img.get_width() - min_side)//2,
                (img.get_height() - min_side)//2,
                min_side, min_side
            )).copy()
            img = pygame.transform.smoothscale(img, (size, size))

            # circular mask
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (size//2, size//2), size//2)

            circ = pygame.Surface((size, size), pygame.SRCALPHA)
            circ.blit(img, (0, 0))
            circ.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return circ
        except Exception:
            return None

    def _layout(self, screen_size):
        """Recalcula panel y posiciones según el tamaño actual (centrado vertical del bloque)."""
        self.w, self.h = screen_size
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)

        # --- tamaños y separaciones ---
        btn_w, btn_h = 248, 54
        gap_y = 16                   # separación entre botones
        icon_gap = 48                # separación entre icono y primer botón

        # --- cálculo del ancho y x centrado ---
        btn_x = self.w // 2 - btn_w // 2

        # --- medir el alto del bloque (icono + gap + botón + gap + botón) ---
        has_icon = self.icon_surf is not None
        icon_h = self.icon_surf.get_height() if has_icon else 0

        # alto de los dos botones + su separación
        buttons_block_h = btn_h + gap_y + btn_h

        # alto total del bloque (si hay icono, se suma icono + icon_gap)
        block_h = (icon_h + icon_gap + buttons_block_h) if has_icon else buttons_block_h

        # y inicial para centrar verticalmente todo el bloque
        y0 = max(0, self.h // 2 - block_h // 2)

        # --- posiciones verticales ---
        if has_icon:
            # icono centrado horizontalmente en y0
            ix = self.w // 2 - self.icon_surf.get_width() // 2
            iy = y0
            self.icon_rect = pygame.Rect(ix, iy, self.icon_surf.get_width(), self.icon_surf.get_height())
            # primer botón debajo del icono
            btn_y = iy + icon_h + icon_gap
        else:
            # si no hay icono, el bloque comienza en y0 con el primer botón
            self.icon_rect = pygame.Rect(0, 0, 0, 0)
            btn_y = y0

        # segundo botón debajo del primero
        load_y = btn_y + btn_h + gap_y

        # --- instanciar/actualizar botones centrados ---
        self.btn_start = Button(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="Iniciar nueva partida",
            font=self.font,
            bg=settings.BUTTON_BG,
            bg_hover=settings.BTN_BG_HOVER,
            fg=settings.TEXT_DARK,
        )

        self.btn_load = Button(
            rect=pygame.Rect(btn_x, load_y, btn_w, btn_h),
            text="Cargar partida",
            font=self.font,
            bg=settings.BUTTON_BG,
            bg_hover=settings.BTN_BG_HOVER,
            fg=settings.TEXT_DARK,
        )

    def resize(self, screen_size):
        self._layout(screen_size)

    def draw(self, surface: pygame.Surface):
        current_size = surface.get_size()
        if current_size != (self.w, self.h):
            self._layout(current_size)

        # Fullscreen panel background
        pygame.draw.rect(surface, settings.MENU_BG, self.panel_rect)

        # Icon (circular), if loaded
        if self.icon_surf and self.icon_rect.width > 0:
            surface.blit(self.icon_surf, (self.icon_rect.x, self.icon_rect.y))

        # Buttons
        self.btn_start.draw(surface)
        self.btn_load.draw(surface)

    def handle_event(self, event) -> str | None:
        if self.btn_start.handle_event(event):
            return "start"
        if self.btn_load.handle_event(event):
            # Placeholder action for "Cargar partida"
            self.on_load_game()
            return "load"
        return None

    def on_load_game(self):
        """Placeholder for Load Game action (no-op for now)."""
        pass
