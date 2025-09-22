from __future__ import annotations
import pygame
from typing import Literal, Optional

from .. import settings
from ..util import format_mmss, CountdownTimer  # usas estos en tu engine actual

AlignX = Literal["left", "center", "right"]
AlignY = Literal["top", "center", "bottom"]


class statisticLogic:
    """
    Administra estadísticas del HUD. 
    """

    def __init__(
        self,
        start_seconds: Optional[float] = None,
        align_x: AlignX = "center",
        align_y: AlignY = "top",
        margin_x: int = 0,
        margin_y: int = 5,
        font: Optional[pygame.font.Font] = None,
    ) -> None:
        pygame.font.init()

        self._timer = CountdownTimer(
            start_seconds if start_seconds is not None else settings.TIMER_START_SECONDS
        )
        self._font = font or pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)
        self._font_stats = pygame.font.Font(settings.UI_FONT_NAME, settings.STATS_FONT_SIZE)


        # Posicionamiento del temporizador (p. ej. centrado arriba)
        self._align_x: AlignX = align_x
        self._align_y: AlignY = align_y
        self._margin_x = margin_x
        self._margin_y = margin_y

        self._money: float = 0.0        # dinero inicial
        self._reputation: int = 70      # reputación inicial (int)

    # ---------------- API pública mínima ----------------
    def reset(self) -> None:
        """Reinicia TODAS las estadísticas manejadas por esta clase."""
        self._reset_timer()

    def update(self, dt: float, money: float = 0.0, reputation: int = 70) -> None:
        """Actualiza TODAS las estadísticas frame a frame."""
        self._update_timer(dt)
        self._update_money(money)
        self._update_reputation(reputation)


    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja TODAS las estadísticas en pantalla."""
        self._draw_timer(surface)
        self._draw_money(surface)
        self._draw_reputation(surface)

    # ---------------- Métodos privados (segmentados) ----------------
    def _reset_timer(self) -> None:
        self._timer.reset()

    def _update_timer(self, dt: float) -> None:
        self._timer.tick(dt)

    def _draw_timer(self, surface: pygame.Surface) -> None:
        label = format_mmss(self._timer.time_left)
        text_surf = self._font.render(label, True, settings.TIMER_TEXT)
        rect = self._place_rect(surface, text_surf.get_rect())
        surface.blit(text_surf, rect)
    
    def _reset_money(self) -> None:
        self._money = 0.0
    
    def _update_money(self, amount: float) -> None:
        self._money = amount
    
    def _draw_money(self, surface: pygame.Surface) -> None:
        label = f'dinero: ${self._money:,.2f}'
        fg = (16, 110, 16)
        pos = (10, 10) # margen sup-izq
        self._draw_text_with_outline(surface, label, fg, pos)

    def _reset_reputation(self) -> None:
        self._reputation = 70
    
    def _update_reputation(self, amount: int) -> None:
        self._reputation = amount
        # if self._reputation > 100:
        #     self._reputation = 100
        # elif self._reputation < 0:
        #     self._reputation = 0
    
    def _draw_reputation(self, surface: pygame.Surface) -> None:
        label = f'reputacion: {self._reputation}'
        fg = (255, 255, 255)
        # calcular Y usando la altura de la fuente (+4px de padding)
        line_h = self._font.get_height() + 4
        pos = (10, 10 + line_h)
        text_surf = self._font_stats.render(label, True, fg)
        surface.blit(text_surf, pos)

    # ---------------- Utilidades de posicionamiento ----------------
    def _place_rect(self, surface: pygame.Surface, rect: pygame.Rect) -> pygame.Rect:
        """Calcula un rect según la alineación configurada y márgenes."""
        sw, sh = surface.get_width(), surface.get_height()

        # Eje X
        if self._align_x == "left":
            rect.left = self._margin_x
        elif self._align_x == "center":
            rect.centerx = sw // 2
        else:  # "right"
            rect.right = sw - self._margin_x

        # Eje Y
        if self._align_y == "top":
            rect.top = self._margin_y
        elif self._align_y == "center":
            rect.centery = sh // 2
        else:  # "bottom"
            rect.bottom = sh - self._margin_y

        return rect
    
    def _draw_text_with_outline(self, surface: pygame.Surface, text: str, fg: tuple[int,int,int], pos: tuple[int,int], outline=(0,0,0), thickness: int = 2) -> None:
        """Render simple de contorno: dibuja el texto en negro alrededor, luego el relleno."""
        txt_main = self._font_stats.render(text, True, fg)
        txt_out  = self._font_stats.render(text, True, outline)

        x, y = pos
        # offsets en cruz+diagonales para un contorno visible
        for ox in (-thickness, 0, thickness):
            for oy in (-thickness, 0, thickness):
                if ox == 0 and oy == 0: 
                    continue
                surface.blit(txt_out, (x + ox, y + oy))
        surface.blit(txt_main, (x, y))

    # ---------------- Extras públicos útiles ----------------
    def finished(self) -> bool:
        return self._timer.finished()

    @property
    def time_left(self) -> float:
        return self._timer.time_left