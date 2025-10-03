import os
import pygame
from .. import settings
from .button import Button
from typing import Optional, Callable

class MainMenu:
    def __init__(self, screen_size, on_load: Optional[Callable[[str], bool]] = None):
        self.w, self.h = screen_size
        self.font = pygame.font.Font(settings.UI_FONT_NAME, settings.UI_FONT_SIZE)
        self.on_load = on_load

        base_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.normpath(os.path.join(base_dir, "..", "..", "assets", "images", "menu_bg.png"))
        self.bg_surf = pygame.image.load(bg_path).convert()  
        self.bg_surf = pygame.transform.smoothscale(self.bg_surf, (self.w, self.h))
        

        #Mover botones e imagen
        self.offset_x = -150 

        
        # phases: MAIN (botones principales) | LOAD (lista de partidas)
        self.phase = "MAIN"

        # icon (will be loaded once)
        self.icon_surf = self._load_circular_icon(size=224)
        self.icon_rect = pygame.Rect(0, 0, 0, 0)

        # placeholders; computed in _layout()
        self.panel_rect = pygame.Rect(0, 0, self.w, self.h)
        self.btn_start = None
        self.btn_load = None

        # LOAD-phase UI
        self.load_title = "Cargar partida"
        self.save_buttons: list[Button] = []
        self.load_feedback: Optional[str] = None  # para mostrar errores (opcional)

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

        

        # MAIN buttons (centrados)
        btn_w, btn_h = 248, 54
        gap_y = 16                   # separación entre botones
        icon_gap = 48                # separación entre icono y primer botón

        # --- cálculo del ancho y x centrado ---
        btn_x = self.w // 2 - btn_w // 2 + self.offset_x

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
            ix = self.w // 2 - self.icon_surf.get_width() // 2 + self.offset_x
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

        if self.phase == "LOAD":
            self._build_save_list()

    def resize(self, screen_size):
        self._layout(screen_size)

    def draw(self, surface: pygame.Surface):
        # Si el tamaño del surface cambió, adapta el layout al vuelo
        current_size = surface.get_size()
        if current_size != (self.w, self.h):
            self._layout(current_size)
            self.bg_surf = pygame.transform.scale(self.bg_surf, current_size)
          

        # Fondo
        surface.blit(self.bg_surf, (0, 0)) 
        
        if self.phase == "MAIN":
            # Icon (circular), if loaded
            if self.icon_surf and self.icon_rect.width > 0:
                surface.blit(self.icon_surf, (self.icon_rect.x, self.icon_rect.y))
            self._draw_main(surface)
        else:  # LOAD
            self._draw_load(surface)

    def _draw_main(self, surface: pygame.Surface):
        self.btn_start.draw(surface)
        self.btn_load.draw(surface)

    def _draw_load(self, surface: pygame.Surface):
        # Título
        title_surf = self.font.render(self.load_title, True, settings.BUTTON_BG)
        surface.blit(title_surf, (self.w // 2 - title_surf.get_width() // 2+ self.offset_x, int(self.h * 0.18)))

        # Feedback si no hay saves
        if self.load_feedback:
            fb = self.font.render(self.load_feedback, True, settings.TEXT_RED)
            surface.blit(fb, (self.w // 2 - fb.get_width() // 2 + self.offset_x, self.h // 2 - fb.get_height() // 2))
        else:
          # Botones por archivo
          for b in self.save_buttons:
              b.draw(surface)


        # Hint simple
        hint = "ESC para volver"
        hint_surf = pygame.font.Font(settings.UI_FONT_NAME, 18).render(hint, True, settings.BUTTON_BG)
        surface.blit(hint_surf, (self.w // 2 - hint_surf.get_width() // 2 + self.offset_x, int(self.h * 0.88)))

    def handle_event(self, event) -> str | None:
        if self.phase == "MAIN":
            if self.btn_start.handle_event(event):
                return "start"
            if self.btn_load.handle_event(event):
                self.phase = "LOAD"
                self._layout((self.w, self.h))
                return None
            return None

        # LOAD phase
        if self.phase == "LOAD":
            # Volver con ESC
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.phase = "MAIN"
                return None

            # Click sobre un save
            for b in self.save_buttons:
                if b.handle_event(event):
                    filename = b.text  # viene con .sav
                    ok = False
                    if self.on_load:
                        ok = bool(self.on_load(filename))
                    if ok:
                        return "loaded"   # el engine pone GameState.PLAYING
                    else:
                        # muestra feedback, no cambia de pantalla
                        self.load_feedback = "No se pudo cargar la partida."
                        return None
            return None

        return None

    def on_load_game(self):
        """Placeholder for Load Game action (no-op for now)."""
        pass
    
    def _build_save_list(self):
        """Crea botones para cada .sav en /saves, centrados en vertical."""
        self.save_buttons.clear()
        self.load_feedback = None


        base_dir = os.path.dirname(os.path.abspath(__file__))
        saves_dir = os.path.join(base_dir, "..", "..", "..", "saves")

        try:
            entries = []
            if os.path.isdir(saves_dir):
                for name in os.listdir(saves_dir):
                    if name.lower().endswith(".sav"):
                        entries.append(name)
            entries.sort(key=str.lower)
        except Exception:
            entries = []

        # Crear botones verticales centrados
        btn_w, btn_h = 320, 48
        total_h = len(entries) * btn_h + max(0, (len(entries) - 1)) * 10
        y0 = self.h // 2 - total_h // 2
        x = self.w // 2 - btn_w // 2 + self.offset_x

        for idx, fname in enumerate(entries):
            y = y0 + idx * (btn_h + 10)
            self.save_buttons.append(
                Button(
                    rect=pygame.Rect(x, y, btn_w, btn_h),
                    text=fname,  # muestra el nombre con .sav
                    font=self.font,
                    bg=settings.BUTTON_BG,
                    bg_hover=settings.BTN_BG_HOVER,
                    fg=settings.TEXT_DARK
                )
            )

        # Si no hay saves, deja un feedback mínimo (opcional)
        if not self.save_buttons:
            self.load_feedback = "No se encontraron partidas guardadas."

