# inventory_ui.py
import pygame
from typing import List, Optional, Callable, Any

JobT = Any  # para tipado ligero sin depender del import real


class InventoryUI:
    """
    Inventario en panel lateral (header/lista/footer) con orden por prioridad o deadline.
    - Selección con ↑/↓ y clic (doble-clic confirma).
    - ENTER/SPACE confirma y marca "current".
    - P alterna prioridad (DESC por defecto).
    - D alterna deadline (ASC por defecto: más próximo primero).
    """

    # -------------------------
    # Inicialización / Layout
    # -------------------------
    def __init__(self, font: Optional[pygame.font.Font] = None) -> None:
        pygame.font.init()
        self.font = font or pygame.font.SysFont("Segoe UI", 16)

        # Estado de datos
        self._jobs: List[JobT] = []
        self.selected_index: int = 0
        self._selected_id: Optional[str] = None
        self.current_job_id: Optional[str] = None  # job marcado como "current"

        # Ordenamiento
        self._sort_key: Optional[str] = "priority"  # "priority" | "deadline"
        self._sort_desc: bool = True                # priority: DESC (alto→bajo)

        # Callback (opcional) cuando se confirma selección
        self.on_pick_job: Optional[Callable[[JobT], None]] = None

        # Doble clic
        self.double_click_ms = 300
        self._last_click_ts = 0

        # Colores UI
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
        self.col_text_main  = (35, 35, 40)
        self.col_text_dim   = (55, 55, 60)
        self.col_row_current_bg = (198, 240, 205)  # verde suave
        self.col_row_current_bd = (120, 185, 135)  # borde verde

        # Layout
        screen = pygame.display.get_surface()
        if screen is None:
            scr_w, scr_h = 1280, 720  # fallback si todavía no hay display
        else:
            r = screen.get_rect()
            scr_w, scr_h = r.w, r.h

        self.padding  = 14
        self.header_h = 40
        self.row_h    = 28
        self.footer_h = 26

        # Panel grande a la derecha: 42% ancho, 90% alto
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

    # -------------------------
    # API opcional para engine
    # -------------------------
    def set_on_pick_job(self, fn: Callable[[JobT], None]) -> None:
        self.on_pick_job = fn  # O(1) tiempo, O(1) espacio

    def set_current_job_id(self, job_id: Optional[str]) -> None:
        self.current_job_id = None if job_id is None else str(job_id)

    # -------------------------
    # Datos / Ordenamiento
    # -------------------------
    def set_jobs(self, jobs: List[JobT], keep_selection: bool = True) -> None:
        """Carga/ordena jobs y preserva la selección por id cuando sea posible."""
        prev_id = self._selected_id if keep_selection else None
        self._jobs = list(jobs) if jobs else []

        # Orden seguro
        if self._sort_key == "priority":
            self._jobs.sort(key=lambda j: getattr(j, "priority", 0), reverse=self._sort_desc)

        elif self._sort_key == "deadline":
            from datetime import datetime

            def _deadline_key(j):
                # 1) Si existe key_deadline(), úsalo
                kd = getattr(j, "key_deadline", None)
                if callable(kd):
                    try:
                        return kd()
                    except Exception:
                        pass

                # 2) Fallback por atributo: primero 'deadline', luego 'deadline_dt'
                d = getattr(j, "deadline", None)
                if d is None:
                    d = getattr(j, "deadline_dt", None)

                if d is None:
                    # sin fecha → al final
                    return (datetime.max, -getattr(j, "priority", 0), -getattr(j, "payout", 0))

                return (d, -getattr(j, "priority", 0), -getattr(j, "payout", 0))

            self._jobs.sort(key=_deadline_key, reverse=self._sort_desc)

        # Reposicionar selección
        if not self._jobs:
            self.selected_index = 0
            self._selected_id = None
            return

        idx = 0
        if prev_id is not None:
            for i, jb in enumerate(self._jobs):
                if getattr(jb, "id", None) == prev_id:
                    idx = i
                    break
        self.selected_index = idx
        self._selected_id = getattr(self._jobs[idx], "id", None)
        # O(n log n) tiempo por el sort; O(n) por la copia; espacio adicional O(1).

    # -------------------------
    # Interacción (input)
    # -------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        # Teclado
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and self._jobs or event.key == pygame.K_w and self._jobs:
                self.selected_index = max(0, self.selected_index - 1)
                self._sync_selected_id()
                return
            if event.key == pygame.K_DOWN and self._jobs or event.key == pygame.K_s and self._jobs:
                self.selected_index = min(len(self._jobs) - 1, self.selected_index + 1)
                self._sync_selected_id()
                return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self._jobs:
                self._pick_current()
                return

            # Ordenamientos
            if event.key == pygame.K_p:
                if self._sort_key != "priority":
                    self._sort_key = "priority"; self._sort_desc = True
                else:
                    self._sort_desc = not self._sort_desc
                self.set_jobs(self._jobs, keep_selection=True)
                return

            if event.key == pygame.K_d:
                if self._sort_key != "deadline":
                    self._sort_key = "deadline"; self._sort_desc = False  # más próximo primero
                else:
                    self._sort_desc = not self._sort_desc
                self.set_jobs(self._jobs, keep_selection=True)
                return

        # Mouse: selección por fila + doble clic
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._jobs:
            mx, my = event.pos
            if self.list_rect.collidepoint(mx, my):
                # Calcula fila según el layout de _draw_jobs_list
                top = self.list_rect.y + 6 + self.font.get_height() + 4 + 6
                if my >= top:
                    row = (my - top) // self.row_h
                    max_rows = max(0, (self.list_rect.bottom - top) // self.row_h)
                    idx = int(row)
                    if 0 <= idx < min(len(self._jobs), max_rows):
                        self.selected_index = idx
                        self._sync_selected_id()

                        now = pygame.time.get_ticks()
                        if now - self._last_click_ts <= self.double_click_ms:
                            self._pick_current()
                        self._last_click_ts = now
        # O(1) por evento; espacio O(1).

    def _sync_selected_id(self) -> None:
        if self._jobs:
            self._selected_id = getattr(self._jobs[self.selected_index], "id", None)
        else:
            self._selected_id = None
        # O(1), O(1)

    def _pick_current(self) -> None:
        if not self._jobs:
            return
        job = self._jobs[self.selected_index]
        # Normaliza a string para que siempre matchee en el draw
        self.current_job_id = str(getattr(job, "id", ""))  # O(1), O(1)
        if callable(self.on_pick_job):
            try:
                self.on_pick_job(job)
            except Exception:
                pass

    # -------------------------
    # Dibujo
    # -------------------------
    def draw(self, screen: pygame.Surface) -> None:
        r = self.panel_rect
        # Panel
        pygame.draw.rect(screen, self.col_bg_panel, r, border_radius=16)
        pygame.draw.rect(screen, self.col_bd_panel, r, width=1, border_radius=16)

        # Header
        title = self.font.render("Inventario", True, self.col_text_title)
        screen.blit(title, (r.x + self.padding, r.y + self.padding))

        # Pill orden
        label_map = {"priority": "Prioridad", "deadline": "Deadline"}
        if self._sort_key in label_map:
            arrow = "↓" if self._sort_desc else "↑"
            txt = f"Orden: {label_map[self._sort_key]} {arrow}"
            pill = self.font.render(txt, True, self.col_text_label)
            pad = 8
            pr = pill.get_rect()
            pr.inflate_ip(2 * pad, 2 * pad)
            pr.top = r.y + self.padding - 4
            pr.right = r.right - self.padding
            pygame.draw.rect(screen, self.col_pill_bg, pr, border_radius=10)
            pygame.draw.rect(screen, self.col_pill_bd, pr, width=1, border_radius=10)
            screen.blit(pill, (pr.x + pad, pr.y + pad))

        # Separador
        y_sep = r.y + self.padding + self.header_h - 6
        pygame.draw.line(screen, self.col_sep, (r.x + self.padding, y_sep), (r.right - self.padding, y_sep), 1)

        # Lista
        self._draw_jobs_list(screen)

        # Footer / ayudas
        foot_y = r.bottom - self.footer_h
        pygame.draw.line(screen, self.col_sep, (r.x + self.padding, foot_y), (r.right - self.padding, foot_y), 1)
        helps = "P: Prioridad  |  D: Deadline  |  ↑/↓: Navegar  |  ENTER: Seleccionar"
        help_surf = self.font.render(helps, True, self.col_text_dim)
        screen.blit(help_surf, (r.x + self.padding, foot_y + (self.footer_h - help_surf.get_height()) // 2))
        # O(m) tiempo (m=filas visibles); O(1) espacio.

    def _draw_jobs_list(self, screen: pygame.Surface) -> None:
        area = self.list_rect
        pygame.draw.rect(screen, self.col_list_bg, area, border_radius=10)

        # Encabezados
        hdr_y = area.y + 6
        col_id_x   = area.x + 10
        col_pri_x  = area.x + int(area.w * 0.45)
        col_dead_x = area.x + int(area.w * 0.65)

        def T(s, c=(60, 60, 65)):
            return self.font.render(s, True, c)

        screen.blit(T("Job"),      (col_id_x, hdr_y))
        screen.blit(T("Pri"),      (col_pri_x, hdr_y))
        screen.blit(T("Deadline"), (col_dead_x, hdr_y))

        # Línea bajo cabecera
        y = hdr_y + self.font.get_height() + 4
        pygame.draw.line(screen, (215, 220, 228), (area.x + 6, y), (area.right - 6, y), 1)
        y += 6

        # Clamp selección
        if self._jobs:
            self.selected_index = max(0, min(self.selected_index, len(self._jobs) - 1))
        else:
            self.selected_index = 0

        # Render filas visibles
        max_rows = max(0, (area.bottom - y) // self.row_h)
        end_idx = min(len(self._jobs), max_rows)

        for i in range(end_idx):
            job = self._jobs[i]
            row_rect = pygame.Rect(area.x + 4, y, area.w - 8, self.row_h - 2)

            is_selected = (i == self.selected_index)
            cur_id = None if self.current_job_id is None else str(self.current_job_id)
            is_current = (str(getattr(job, "id", "")) == cur_id)

            # --- Fondo con prioridad: CURRENT > SELECTED ---
            if is_current and is_selected:
                # current + seleccionado → verde (gana el current)
                pygame.draw.rect(screen, self.col_row_current_bg, row_rect, border_radius=6)
                pygame.draw.rect(screen, self.col_row_current_bd, row_rect, width=1, border_radius=6)
            elif is_current:
                # solo current → verde
                pygame.draw.rect(screen, self.col_row_current_bg, row_rect, border_radius=6)
                pygame.draw.rect(screen, self.col_row_current_bd, row_rect, width=1, border_radius=6)
            elif is_selected:
                # solo seleccionado → azul
                pygame.draw.rect(screen, self.col_row_sel_bg, row_rect, border_radius=6)
                pygame.draw.rect(screen, self.col_row_sel_bd, row_rect, width=1, border_radius=6)

            # Indicador de 'current' (estrella) y corrimiento del ID
            if is_current:
                mark = self.font.render("*", True, (20, 20, 30))
                screen.blit(mark, (row_rect.x + 6, y))
                id_x = area.x + 10 + 16
            else:
                id_x = area.x + 10


            # ID
            screen.blit(T(str(getattr(job, "id", "")), (25, 25, 30)), (id_x, y))
            # Prioridad
            screen.blit(T(str(getattr(job, "priority", 0)), (35, 35, 40)), (col_pri_x, y))

            # Deadline robusto
            # Deadline robusto (atributo 'deadline' o 'deadline_dt')
            from datetime import datetime as _dt_type

            dline = None

            # Métodos opcionales (si existieran en tu Job)
            ds = getattr(job, "deadline_str", None)
            if callable(ds):
                try:
                    dline = ds()
                except Exception:
                    dline = None

            # Atributos
            if dline is None:
                ddt = getattr(job, "deadline", None)
                if ddt is None:
                    ddt = getattr(job, "deadline_dt", None)
                if isinstance(ddt, _dt_type):
                    try:
                        dline = ddt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        dline = str(ddt)[:16]

            if dline is None:
                dline = "—"

            screen.blit(T(dline, (35, 35, 40)), (col_dead_x, y))
            y += self.row_h
        # O(m) tiempo (m=filas renderizadas); O(1) espacio.

    # -------------------------
    # Utilidades
    # -------------------------
    def selected_job_id(self) -> Optional[str]:
        return self._selected_id  # O(1), O(1)


