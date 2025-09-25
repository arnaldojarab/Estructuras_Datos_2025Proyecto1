# --- inventory_ui.py (o donde tengas tu InventoryUI) ---
import pygame
from typing import List, Optional, Any

try:
    from .jobs_logic.job import Job  # si InventoryUI vive dentro del paquete del juego
except Exception:
    # fallback para tipado en editores; en runtime no es crítico
    Job = Any

class InventoryUI:
    def __init__(self, w: int, h: int, cols: int = 5, cell: int = 48, padding: int = 12):
        self.w, self.h = w, h
        self.cols, self.cell, self.padding = cols, cell, padding
        self.font = pygame.font.SysFont(None, 22)
        self.title_font = pygame.font.SysFont(None, 28, bold=True)

        self._jobs: List[Job] = []
        self._selected_idx: Optional[int] = None
        self._selected_id: Optional[str] = None  # preserva selección entre refrescos

        # stats opcionales mostradas en el encabezado
        self._money: float = 0.0
        self._weight: float = 0.0
        self._reputation: int = 0

        # Panel centrado
        panel_w = cols * cell + (cols + 1) * padding
        panel_h = 300
        self.panel_rect = pygame.Rect((w - panel_w)//2, (h - panel_h)//2, panel_w, panel_h)

    # --- NUEVO: refrescar lista con Jobs, preservando selección por id ---
    def set_jobs(self, jobs: List[Job], keep_selection: bool = True) -> None:
        prev_id = self._selected_id if keep_selection else None
        self._jobs = jobs[:] if jobs else []
        if not self._jobs:
            self._selected_idx = None
            self._selected_id = None
            return
        # try to keep previous selection
        idx = 0
        if prev_id is not None:
            for i, jb in enumerate(self._jobs):
                if getattr(jb, "id", None) == prev_id:
                    idx = i
                    break
        self._selected_idx = idx
        self._selected_id = getattr(self._jobs[idx], "id", None)

    # --- NUEVO: stats que pintaremos en el encabezado ---
    def set_header_stats(self, money: float, weight: float, reputation: int) -> None:
        self._money = money
        self._weight = weight
        self._reputation = reputation

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            grid_rect = self._grid_rect()
            if grid_rect.collidepoint(mx, my):
                col = int((mx - grid_rect.x) // (self.cell + self.padding))
                row = int((my - grid_rect.y) // (self.cell + self.padding))
                idx = row * self.cols + col
                if 0 <= idx < len(self._jobs):
                    self._selected_idx = idx
                    self._selected_id = getattr(self._jobs[idx], "id", None)

        if event.type == pygame.KEYDOWN and self._jobs:
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self._selected_idx = min((self._selected_idx or 0) + 1, len(self._jobs) - 1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._selected_idx = max((self._selected_idx or 0) - 1, 0)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._selected_idx = min((self._selected_idx or 0) + self.cols, len(self._jobs) - 1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._selected_idx = max((self._selected_idx or 0) - self.cols, 0)
            # actualiza id seleccionado
            if self._selected_idx is not None:
                self._selected_id = getattr(self._jobs[self._selected_idx], "id", None)

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        # 1) Oscurecer fondo
        dim = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        screen.blit(dim, (0, 0))

        # 2) Panel
        pygame.draw.rect(screen, (235, 235, 235), self.panel_rect, border_radius=8)
        pygame.draw.rect(screen, (40, 40, 40), self.panel_rect, 2, border_radius=8)

        # 3) Título + stats
        title = self.title_font.render("Inventario (E para cerrar)", True, (20, 20, 20))
        screen.blit(title, (self.panel_rect.x + self.padding, self.panel_rect.y + self.padding))

        stats_txt = f"Items: {len(self._jobs)}  |  Peso: {self._weight:.1f}  |  $: {self._money:.0f}  |  Rep: {self._reputation}"
        stats = self.font.render(stats_txt, True, (40, 40, 40))
        stats_y = self.panel_rect.y + self.padding + 20
        screen.blit(stats, (self.panel_rect.right - self.padding - stats.get_width(), stats_y))

        # 4) Grilla
        grid_rect = self._grid_rect()
        x, y = grid_rect.topleft
        for i, job in enumerate(self._jobs):
            col = i % self.cols
            row = i // self.cols
            cx = x + col * (self.cell + self.padding)
            cy = y + row * (self.cell + self.padding)
            cell_rect = pygame.Rect(cx, cy, self.cell, self.cell)

            pygame.draw.rect(screen, (250, 250, 250), cell_rect, border_radius=6)
            pygame.draw.rect(screen, (60, 60, 60), cell_rect, 2, border_radius=6)

            # Etiqueta corta: últimos 3-4 chars del id
            jid = getattr(job, "id", "???")
            short = jid[-4:] if isinstance(jid, str) else "JOB"
            label = self.font.render(short.upper(), True, (30, 30, 30))
            label_pos = label.get_rect(center=(cell_rect.centerx, cell_rect.centery - 6))
            screen.blit(label, label_pos)

            # Sub-etiqueta: peso o prioridad
            sub = self.font.render(f"{getattr(job,'weight',0):.1f}kg", True, (80, 80, 80))
            sub_pos = sub.get_rect(center=(cell_rect.centerx, cell_rect.centery + 12))
            screen.blit(sub, sub_pos)

            # selección
            if self._selected_idx == i:
                pygame.draw.rect(screen, (0, 0, 0), cell_rect.inflate(6, 6), 2, border_radius=8)

        # 5) Descripción del seleccionado
        if self._selected_idx is not None and 0 <= self._selected_idx < len(self._jobs):
            job = self._jobs[self._selected_idx]
            text_lines = [
                f"ID: {getattr(job,'id','')}",
                f"Payout: ${getattr(job,'payout',0):.0f}",
                f"Peso: {getattr(job,'weight',0):.1f} kg   Pri: {getattr(job,'priority',0)}",
                f"Pickup: {getattr(job,'pickup',('?','?'))}  ->  Dropoff: {getattr(job,'dropoff',('?','?'))}",
                "ENTER/ESPACIO: establecer como 'current job'"
            ]
            base_x = self.panel_rect.x + self.padding
            base_y = self.panel_rect.bottom - self.padding - 5*18
            for k, line in enumerate(text_lines):
                t = self.font.render(line, True, (20, 20, 20))
                screen.blit(t, (base_x, base_y + k*18))

    def _grid_rect(self) -> pygame.Rect:
        top = self.panel_rect.y + 52
        height = self.panel_rect.height - 52 - 72
        return pygame.Rect(self.panel_rect.x + self.padding, top, self.panel_rect.width - 2*self.padding, height)

    # --- NUEVO: util para el engine ---
    def selected_job_id(self) -> Optional[str]:
        return self._selected_id

