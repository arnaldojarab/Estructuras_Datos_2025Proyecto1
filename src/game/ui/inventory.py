# inventory.py
import pygame
from typing import Optional, Callable, Any, List

JobT = Any

class InventoryUI:
    """
    Vista del inventario:
      - Fuente de datos: JobLogic (inyectada).
      - Navegación: ↑/↓ (W/S)
      - ENTER/SPACE: set current en JobLogic + cerrar (callback)
      - Orden: P (prioridad), D (deadline)  [no modifica el orden en JobLogic, solo la vista]
    """

    def __init__(self, job_logic, font: Optional[pygame.font.Font] = None) -> None:
        pygame.font.init()
        self.font = font or pygame.font.SysFont("Segoe UI", 16)

        # Referencia a la lógica (single source of truth)
        self.job_logic = job_logic

        self.selected_index: int = 0
        self._sort_key: Optional[str] = "priority"   # "priority" | "deadline"
        self._sort_desc: bool = True                 # prioridad: DESC
        self.on_pick_job: Optional[Callable[[JobT], None]] = None
        self.on_close_inventory: Optional[Callable[[], None]] = None

        # Colores
        self.col_bg_panel   = (238, 240, 245)
        self.col_bd_panel   = (210, 214, 220)
        self.col_text_title = (25, 25, 28)
        self.col_text_label = (30, 30, 32)
        self.col_pill_bg    = (225, 229, 235)
        self.col_pill_bd    = (205, 210, 218)
        self.col_sep        = (205, 210, 218)
        self.col_list_bg    = (246, 247, 250)
        self.col_row_sel_bg = (220, 228, 245)
        self.col_row_sel_bd = (190, 205, 235)
        self.col_text_dim   = (55, 55, 60)

        # Layout centrado
        screen = pygame.display.get_surface()
        if screen is None:
            scr_w, scr_h = 1280, 720
        else:
            r = screen.get_rect()
            scr_w, scr_h = r.w, r.h

        self.padding  = 14
        self.header_h = 40
        self.row_h    = 28
        self.footer_h = 26

        panel_w = 450
        panel_h = max(220, int(scr_h * 0.90))
        panel_x = (scr_w - panel_w) // 2
        panel_y = (scr_h - panel_h) // 2
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        self.list_rect = pygame.Rect(
            self.panel_rect.x + self.padding,
            self.panel_rect.y + self.padding + self.header_h,
            self.panel_rect.w - 2 * self.padding,
            self.panel_rect.h - (self.header_h + self.footer_h + 2 * self.padding),
        )

    # ---------- Callbacks ----------
    def set_on_pick_job(self, fn: Callable[[JobT], None]) -> None:
        self.on_pick_job = fn

    def set_on_close_inventory(self, fn: Callable[[], None]) -> None:
        self.on_close_inventory = fn

    # ---------- Entrada ----------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        jobs_view = self._get_jobs_view()

        if (event.key in (pygame.K_UP, pygame.K_w)) and jobs_view:
            self.selected_index = max(0, self.selected_index - 1)
            return

        if (event.key in (pygame.K_DOWN, pygame.K_s)) and jobs_view:
            self.selected_index = min(len(jobs_view) - 1, self.selected_index + 1)
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and jobs_view:
            # 1) Notificar job elegido y setear current en JobLogic
            job = jobs_view[self.selected_index]
            if callable(self.on_pick_job):
                try:
                    self.on_pick_job(job)
                except Exception:
                    pass
            else:
                try:
                    self.job_logic.setCurrentJob(str(getattr(job, "id", "")))
                except Exception:
                    pass
            # 2) Cerrar inventario
            if callable(self.on_close_inventory):
                try:
                    self.on_close_inventory()
                except Exception:
                    pass
            return

        # Ordenamiento local (solo de la vista)
        if event.key == pygame.K_p:
            if self._sort_key != "priority":
                self._sort_key = "priority"; self._sort_desc = True
            else:
                self._sort_desc = not self._sort_desc
            return

        if event.key == pygame.K_d:
            if self._sort_key != "deadline":
                self._sort_key = "deadline"; self._sort_desc = False
            else:
                self._sort_desc = not self._sort_desc
            return

    # ---------- Dibujo ----------
    def draw(self, screen: pygame.Surface) -> None:
        r = self.panel_rect
        pygame.draw.rect(screen, self.col_bg_panel, r, border_radius=16)
        pygame.draw.rect(screen, self.col_bd_panel, r, width=1, border_radius=16)

        # Header
        title = self.font.render("Inventario", True, self.col_text_title)
        screen.blit(title, (r.x + self.padding, r.y + self.padding))

        # Pill de orden
        label_map = {"priority": "Prioridad", "deadline": "Deadline"}
        if self._sort_key in label_map:
            arrow = "↓" if self._sort_desc else "↑"
            pill_txt = self.font.render(f"Orden: {label_map[self._sort_key]} {arrow}", True, self.col_text_label)
            pad = 8
            pr = pill_txt.get_rect()
            pr.inflate_ip(2 * pad, 2 * pad)
            pr.top = r.y + self.padding - 4
            pr.right = r.right - self.padding
            pygame.draw.rect(screen, self.col_pill_bg, pr, border_radius=10)
            pygame.draw.rect(screen, self.col_pill_bd, pr, width=1, border_radius=10)
            screen.blit(pill_txt, (pr.x + pad, pr.y + pad))

        # Separador
        y_sep = r.y + self.padding + self.header_h - 6
        pygame.draw.line(screen, self.col_sep, (r.x + self.padding, y_sep), (r.right - self.padding, y_sep), 1)

        # Lista
        self._draw_jobs_list(screen)

        # Footer
        foot_y = r.bottom - self.footer_h
        pygame.draw.line(screen, self.col_sep, (r.x + self.padding, foot_y), (r.right - self.footer_h, foot_y), 1)
        helps = "P: Prioridad  |  D: Deadline  |  ↑/↓: Navegar  |  ENTER: Seleccionar"
        help_surf = self.font.render(helps, True, self.col_text_dim)
        screen.blit(help_surf, (r.x + self.padding, foot_y + (self.footer_h - help_surf.get_height()) // 2))

    def _draw_jobs_list(self, screen: pygame.Surface) -> None:
        area = self.list_rect
        pygame.draw.rect(screen, self.col_list_bg, area, border_radius=10)

        # Encabezados
        hdr_y = area.y + 6
        col_id_x     = area.x + 10
        col_pri_x    = area.x + int(area.w * 0.38)
        col_weight_x = area.x + int(area.w * 0.55)
        col_dead_x   = area.x + int(area.w * 0.72)

        def T(s, c=(60, 60, 65)):
            return self.font.render(s, True, c)

        screen.blit(T("Job"),      (col_id_x, hdr_y))
        screen.blit(T("Pri"),      (col_pri_x, hdr_y))
        screen.blit(T("Peso"),     (col_weight_x, hdr_y))
        screen.blit(T("Deadline"), (col_dead_x, hdr_y))

        # Línea bajo header
        y = hdr_y + self.font.get_height() + 4
        pygame.draw.line(screen, (215, 220, 228), (area.x + 6, y), (area.right - 6, y), 1)
        y += 6

        jobs_view = self._get_jobs_view()
        if not jobs_view:
            self.selected_index = 0
            return

        # Clamp de selección
        self.selected_index = max(0, min(self.selected_index, len(jobs_view) - 1))

        # Filas visibles
        max_rows = max(0, (area.bottom - y) // self.row_h)
        end_idx = min(len(jobs_view), max_rows)

        for i in range(end_idx):
            job = jobs_view[i]
            row_rect = pygame.Rect(area.x + 4, y, area.w - 8, self.row_h - 2)

            # seleccionado (solo resaltado azul; ya no hay verde)
            if i == self.selected_index:
                pygame.draw.rect(screen, self.col_row_sel_bg, row_rect, border_radius=6)
                pygame.draw.rect(screen, self.col_row_sel_bd, row_rect, width=1, border_radius=6)

            # Columnas
            screen.blit(T(str(getattr(job, "id", "")), (25, 25, 30)), (area.x + 10, y))
            screen.blit(T(str(getattr(job, "priority", 0)), (35, 35, 40)), (col_pri_x, y))
            screen.blit(T(str(getattr(job, "weight", 0)),   (35, 35, 40)), (col_weight_x, y))

            # Deadline robusto
            from datetime import datetime as _dt_type
            dline = None
            ds = getattr(job, "deadline_str", None)
            if callable(ds):
                try:
                    dline = ds()
                except Exception:
                    dline = None
            if dline is None:
                ddt = getattr(job, "deadline", None) or getattr(job, "deadline_dt", None)
                if isinstance(ddt, _dt_type):
                    try:
                        dline = ddt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        dline = str(ddt)[:16]
            if dline is None:
                dline = "—"
            screen.blit(T(dline, (35, 35, 40)), (col_dead_x, y))

            y += self.row_h

    # ---------- Vista ordenada (no muta JobLogic) ----------
    def _get_jobs_view(self) -> List[JobT]:
        """Obtiene el inventario desde JobLogic y aplica un orden local (si procede)."""
        jobs: List[JobT] = self.job_logic.getInventory()  # <- single source of truth
        if not jobs:
            return jobs

        if self._sort_key == "priority":
            return sorted(jobs, key=lambda j: getattr(j, "priority", 0), reverse=self._sort_desc)

        if self._sort_key == "deadline":
            from datetime import datetime
            def _deadline_key(j):
                kd = getattr(j, "key_deadline", None)
                if callable(kd):
                    try:
                        return kd()
                    except Exception:
                        pass
                d = getattr(j, "deadline", None) or getattr(j, "deadline_dt", None)
                return d if d is not None else datetime.max
            return sorted(jobs, key=_deadline_key, reverse=self._sort_desc)

        # Sin clave conocida: devuelve como está en JobLogic
        return jobs
