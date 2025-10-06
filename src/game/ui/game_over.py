import pygame
from typing import List, Dict, Optional
import json
import os

from .. import settings 

# ---- Layout ratios (screen-height relative) ----
GO_TITLE_Y_RATIO = 0.12
GO_ASK_PROMPT_Y_RATIO = 0.35
GO_ASK_BUTTONS_Y_RATIO = 0.52
GO_NAME_PROMPT_Y_RATIO = 0.32
GO_NAME_BOX_Y_RATIO = 0.45
GO_NAME_HINT_Y_RATIO = 0.65
GO_TABLE_TOP_Y_RATIO = 0.30
GO_CONTINUE_BTN_Y_RATIO = 0.82

# ---- Buttons (ASK + Continue) ----
GO_ASK_BUTTON_SPACING = 140
GO_BUTTON_PADDING_X = 28
GO_BUTTON_PADDING_Y = 12
GO_BUTTON_BORDER_RADIUS = 10

# ---- Name input box ----
GO_NAME_BOX_WIDTH = 360
GO_NAME_BOX_HEIGHT = 72
GO_NAME_BOX_BORDER_RADIUS = 8

# ---- Table ----
GO_TABLE_PAD_X = 30
GO_TABLE_HEADER_HEIGHT = 50
GO_TABLE_HEADER_BORDER_RADIUS = 8
GO_TABLE_ROW_HEIGHT = 46
GO_TABLE_ROW_GAP = 8
GO_TABLE_ROW_BORDER_RADIUS = 6


class GameOverLogic:
    def __init__(self, hud_font: pygame.font.Font, small_font: pygame.font.Font):
        self.hud_font = hud_font
        self.small_font = small_font
        self.title_font = pygame.font.Font(settings.UI_FONT_NAME, settings.MENU_TITLE_FONT_SIZE)
        self.title = "GAME OVER"
        self.win = False

        self._phase: Optional[str] = None      # "ASK" | "NAME" | "TABLE"
        self._choice_idx: int = 0              # 0 => "Sí", 1 => "No"
        self._name_buf: str = ""               # typed name (1..4)
        self._user_score: float = 0.0
        self._rows: List[Dict] = []
        self._continue_rect: Optional[pygame.Rect] = None
        self._done: bool = False

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_path = os.path.normpath(os.path.join(base_dir, "..", "..", "..", "data", "puntajes.json"))

        self._base_scores: List[Dict[str, object]] = []

        self._base_scores = self._load_scores()

    # -------- Public API --------

    def enter(self, score: float) -> None:
        self._phase = "ASK"
        self._choice_idx = 0
        self._name_buf = ""
        self._user_score = round(float(score), settings.GO_SCORE_DECIMALS)
        # refresh base scores from JSON
        self._base_scores = self._load_scores()
        self._rows = []
        self._continue_rect = None
        self._done = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._phase is None or self._done:
            return

        if event.type == pygame.KEYDOWN:
            if self._phase == "ASK":
                self._handle_ask_keydown(event)
            elif self._phase == "NAME":
                self._handle_name_keydown(event)
            elif self._phase == "TABLE":
                self._handle_table_keydown(event)

        elif event.type == pygame.MOUSEBUTTONDOWN and self._phase == "TABLE":
            if event.button == 1 and self._continue_rect and self._continue_rect.collidepoint(event.pos):
                self._done = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        W, H = screen.get_width(), screen.get_height()

        # Opaque full-screen panel
        pygame.draw.rect(screen, settings.MENU_BG, pygame.Rect(0, 0, W, H))

        # Title
        if self.win:
            title_surf = self.title_font.render(self.title, True, settings.TEXT_GREEN)
        else:
          title_surf = self.title_font.render(self.title, True, settings.TEXT_RED)

        screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, int(H * GO_TITLE_Y_RATIO)))

        # Phase-specific rendering
        if self._phase == "ASK":
            self._draw_ask(screen, W, H)
        elif self._phase == "NAME":
            self._draw_name(screen, W, H)
        elif self._phase == "TABLE":
            self._draw_table(screen, W, H)

    def is_done(self) -> bool:
        return self._done

    # -------- Internal handlers --------

    def _handle_ask_keydown(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._choice_idx = 1 - self._choice_idx 
        elif event.key == pygame.K_RETURN:
            if self._choice_idx == 1:  # "No"
                self._done = True
            else:
                self._phase = "NAME"

    def _handle_name_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_BACKSPACE:
            self._name_buf = self._name_buf[:-1]
        elif event.key == pygame.K_RETURN:
            if len(self._name_buf) >= 1:
                name = self._name_buf
                if len(name) < 4:
                    name = name + (" " * (4 - len(name)))
                self._prepare_rows(name, self._user_score)
                self._append_and_save(name, self._user_score)
                self._phase = "TABLE"
        else:
            ch = event.unicode
            if ch and ch not in ("\r", "\n"):
                if len(self._name_buf) < 4:
                    self._name_buf += ch

    def _handle_table_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_RETURN:
            self._done = True

    def set_title(self, title: str, win: bool):
        self.title = title
        self.win = win

    # -------- Data prep --------

    def _load_scores(self) -> List[Dict[str, object]]:
        try:
            if not os.path.exists(self.storage_path):
                return []
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save_scores(self, rows: List[Dict[str, object]]) -> None:
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _append_and_save(self, name: str, score: float) -> None:
        current = self._load_scores()
        current.append({"name": name, "score": float(round(score, settings.GO_SCORE_DECIMALS))})
        self._save_scores(current)
        self._base_scores = current

    def _prepare_rows(self, player_name: str, player_score: float) -> None:
        base = list(self._base_scores)
        base.sort(key=lambda r: r["score"], reverse=True)

        candidate = base + [{"name": player_name, "score": player_score, "is_player": True}]
        candidate.sort(key=lambda r: r["score"], reverse=True)

        top3 = candidate[:3]
        makes_top3 = any(r.get("is_player") for r in top3)
        rows: List[Dict] = []

        if makes_top3:
            for idx, r in enumerate(top3, start=1):
                rows.append({
                    "rank": idx,
                    "name": r["name"],
                    "score": r["score"],
                    "is_player": r.get("is_player", False),
                })
        else:
            player_rank = next((idx for idx, r in enumerate(candidate, start=1) if r.get("is_player")), None)

            for idx, r in enumerate(top3, start=1):
                rows.append({
                    "rank": idx,
                    "name": r["name"],
                    "score": r["score"],
                    "is_player": False,
                })
            rows.append({"rank": None, "name": "...", "score": None, "is_player": False})
            rows.append({"rank": player_rank, "name": player_name, "score": player_score, "is_player": True})

        self._rows = rows
        self._continue_rect = None  # will be set during draw

    # -------- Rendering helpers --------

    def _draw_ask(self, screen: pygame.Surface, W: int, H: int) -> None:
      prompt = "¿Desea guardar su puntaje?"
      prompt_surf = self.hud_font.render(prompt, True, settings.GO_TEXT_COLOR)
      screen.blit(prompt_surf, (W // 2 - prompt_surf.get_width() // 2, int(H * GO_ASK_PROMPT_Y_RATIO)))

      labels = ["Sí", "No"]
      y = int(H * GO_ASK_BUTTONS_Y_RATIO)
      center_x = W // 2

      mouse_pos = pygame.mouse.get_pos()
      mouse_pressed = pygame.mouse.get_pressed(num_buttons=3)

      hover_idx = None  # track which button is hovered this frame

      for i, label in enumerate(labels):
          text = self.hud_font.render(label, True, settings.TEXT_DARK)
          box_w = text.get_width() + GO_BUTTON_PADDING_X * 2
          box_h = text.get_height() + GO_BUTTON_PADDING_Y * 2
          x = center_x + (i - 0.5) * GO_ASK_BUTTON_SPACING - box_w // 2
          rect = pygame.Rect(int(x), y, int(box_w), int(box_h))

          # Hover detection
          is_hovered = rect.collidepoint(mouse_pos)
          if is_hovered:
              hover_idx = i

          selected = is_hovered or (i == self._choice_idx)
          bg = settings.GO_BUTTON_BG_SELECTED if selected else settings.BUTTON_BG
          pygame.draw.rect(screen, bg, rect, border_radius=GO_BUTTON_BORDER_RADIUS)
          screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

          if is_hovered and mouse_pressed[0]:
              if i == 1:  # "No"
                  self._done = True
              else:       # "Sí"
                  self._phase = "NAME"

      if hover_idx is not None:
          self._choice_idx = hover_idx



    def _draw_name(self, screen: pygame.Surface, W: int, H: int) -> None:
        prompt = "Ingrese su nombre (1–4):"
        prompt_surf = self.hud_font.render(prompt, True, settings.GO_TEXT_COLOR)
        screen.blit(prompt_surf, (W // 2 - prompt_surf.get_width() // 2, int(H * GO_NAME_PROMPT_Y_RATIO)))

        # Input box
        rect = pygame.Rect(W // 2 - GO_NAME_BOX_WIDTH // 2, int(H * GO_NAME_BOX_Y_RATIO),
                           GO_NAME_BOX_WIDTH, GO_NAME_BOX_HEIGHT)
        pygame.draw.rect(screen, (240, 240, 240), rect, border_radius=GO_NAME_BOX_BORDER_RADIUS)

        text_surf = self.hud_font.render(self._name_buf, True, settings.TEXT_DARK if self._name_buf else settings.TEXT_DARK)
        screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

        hint = "Enter para confirmar"
        hint_surf = self.small_font.render(hint, True, settings.GO_TEXT_COLOR)
        screen.blit(hint_surf, (W // 2 - hint_surf.get_width() // 2, int(H * GO_NAME_HINT_Y_RATIO)))

    def _draw_table(self, screen: pygame.Surface, W: int, H: int) -> None:
        header = ["#", "Nombre", "Puntaje"]
        header_surfs = [self.hud_font.render(h, True, settings.GO_TEXT_COLOR) for h in header]

        # Measure columns
        col_w = [max(s.get_width(), 60) for s in header_surfs]
        for r in self._rows:
            rank_txt = "-" if r["rank"] is None else str(r["rank"])
            name_txt = r["name"]
            score_txt = "" if r["score"] is None else f"{r['score']:.{settings.GO_SCORE_DECIMALS}f}"
            col_w[0] = max(col_w[0], self.hud_font.render(rank_txt, True, (0, 0, 0)).get_width())
            col_w[1] = max(col_w[1], self.hud_font.render(name_txt, True, (0, 0, 0)).get_width())
            col_w[2] = max(col_w[2], self.hud_font.render(score_txt, True, (0, 0, 0)).get_width())

        total_w = col_w[0] + col_w[1] + col_w[2] + GO_TABLE_PAD_X * 4
        x0 = W // 2 - total_w // 2
        y0 = int(H * GO_TABLE_TOP_Y_RATIO)

        # Header
        header_rect = pygame.Rect(x0, y0, total_w, GO_TABLE_HEADER_HEIGHT)
        pygame.draw.rect(screen, settings.GO_HEADER_BG, header_rect, border_radius=GO_TABLE_HEADER_BORDER_RADIUS)
        cx = x0 + GO_TABLE_PAD_X
        for i, surf in enumerate(header_surfs):
            screen.blit(surf, (cx, y0 + (GO_TABLE_HEADER_HEIGHT - surf.get_height()) // 2))
            cx += col_w[i] + GO_TABLE_PAD_X

        # Rows
        y = y0 + GO_TABLE_HEADER_HEIGHT + 10
        for r in self._rows:
            is_player = r["is_player"]
            bg = settings.GO_HIGHLIGHT_ROW if is_player else settings.GO_TEXT_COLOR
            row_rect = pygame.Rect(x0, y, total_w, GO_TABLE_ROW_HEIGHT)
            pygame.draw.rect(screen, bg, row_rect, border_radius=GO_TABLE_ROW_BORDER_RADIUS)

            rank_txt = "-" if r["rank"] is None else str(r["rank"])
            name_txt = r["name"]
            score_txt = "" if r["score"] is None else f"{r['score']:.{settings.GO_SCORE_DECIMALS}f}"

            rank_s = self.hud_font.render(rank_txt, True, (0, 0, 0))
            name_s = self.hud_font.render(name_txt, True, (0, 0, 0))
            score_col = (100, 100, 100) if r["score"] is None else (0, 0, 0)
            score_s = self.hud_font.render(score_txt, True, score_col)

            cx = x0 + GO_TABLE_PAD_X
            screen.blit(rank_s, (cx, y + (GO_TABLE_ROW_HEIGHT - rank_s.get_height()) // 2))
            cx += col_w[0] + GO_TABLE_PAD_X
            screen.blit(name_s, (cx, y + (GO_TABLE_ROW_HEIGHT - name_s.get_height()) // 2))
            cx += col_w[1] + GO_TABLE_PAD_X
            screen.blit(score_s, (cx, y + (GO_TABLE_ROW_HEIGHT - score_s.get_height()) // 2))

            y += GO_TABLE_ROW_HEIGHT + GO_TABLE_ROW_GAP

        # Continue button
        btn_label = "Continuar"
        btn_surf = self.hud_font.render(btn_label, True, settings.TEXT_DARK)
        btn_w = btn_surf.get_width() + GO_BUTTON_PADDING_X * 2
        btn_h = btn_surf.get_height() + GO_BUTTON_PADDING_Y * 2
        btn_x = W // 2 - btn_w // 2
        btn_y = int(H * GO_CONTINUE_BTN_Y_RATIO) + 40
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        screen.blit(btn_surf, (btn_rect.centerx - btn_surf.get_width() // 2,
                               btn_rect.centery - btn_surf.get_height() // 2))
        self._continue_rect = btn_rect

        # Hover detection
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = btn_rect.collidepoint(mouse_pos)

        # Use selected background on hover
        bg = settings.BTN_BG_HOVER if is_hovered else settings.BUTTON_BG
        pygame.draw.rect(screen, bg, btn_rect, border_radius=GO_BUTTON_BORDER_RADIUS)

        screen.blit(
            btn_surf,
            (btn_rect.centerx - btn_surf.get_width() // 2,
            btn_rect.centery - btn_surf.get_height() // 2)
        )
        self._continue_rect = btn_rect

