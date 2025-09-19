import pygame
from .. import settings 
from .button import Button

class MainMenu:
    def __init__(self, screen_size):
        self.w, self.h = screen_size
        self.font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)

        # placeholders; se calculan en _layout()
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)
        self.btn_start = None
        self._layout((self.w, self.h))

    def _layout(self, screen_size):
        """Recalcula panel y posiciones según el tamaño actual."""
        self.w, self.h = screen_size
        # Panel a pantalla completa (ancho x alto actuales)
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)

        # Botón centrado en la pantalla (no solo en el panel)
        btn_w, btn_h = 220, 54
        btn_x = self.w // 2 - btn_w // 2
        btn_y = self.h // 2 - btn_h // 2

        self.btn_start = Button(
            rect=pygame.Rect(btn_x, btn_y, btn_w, btn_h),
            text="Empezar  a  jugar",
            font=self.font,
            bg=settings.BTN_BG,
            bg_hover=settings.BTN_BG_HOVER,
            fg=settings.BTN_TEXT
        )

    def resize(self, screen_size):
        # Si cambias el tamaño de ventana fuera del menú, llama a esto
        self._layout(screen_size)

    def draw(self, surface: pygame.Surface):
        # Si el tamaño del surface cambió, adapta el layout al vuelo
        current_size = surface.get_size()
        if current_size != (self.w, self.h):
            self._layout(current_size)

        # Panel gris pantalla completa
        pygame.draw.rect(surface, settings.MENU_PANEL_GRAY, self.panel_rect)

        # Botón
        self.btn_start.draw(surface)

    def handle_event(self, event) -> str | None:
        if self.btn_start.handle_event(event):
            return "start"
        return None
