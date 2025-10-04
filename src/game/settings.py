# Global tunables
TILE_SIZE = 20
FPS = 60

# Movement & stamina
BASE_SPEED = 3.0  # celdas/seg
STAMINA_MAX = 100
STAMINA_CONSUME_PER_CELL = 0.5
STAMINA_RECOVERY_IDLE = 5.0  # por segundo

# --- UI / MENÚ ---
MENU_TITLE_FONT_SIZE = 40
MENU_PANEL_WIDTH = 320
MENU_BG = (20, 20, 24)         # fondo general (opcional)
MENU_BG_HOVER = (53, 53, 64)
BUTTON_BG = (200, 200, 200)
BUTTON_BG_SELECTED = (255, 220, 120)
BTN_BG_HOVER = (233, 233, 233)
TEXT_LIGHT = (219, 219, 219)
TEXT_DARK = (10, 10, 10)
TEXT_RED = (214, 0, 0)
TEXT_GREEN = (0, 214, 93)
UI_FONT_NAME = None            # None = fuente por defecto de pygame
UI_FONT_SIZE = 28

# --- UI / GAME OVER ---
GO_TEXT_COLOR = (230, 230, 230)

GO_HIGHLIGHT_ROW = (255, 235, 128)       # amarillo suave (fila del jugador)
GO_HEADER_BG = (50, 50, 60)

GO_BUTTON_BG_SELECTED = (255, 220, 120)

GO_TITLE_FONT_SIZE = 35        # reutiliza fuente del HUD

# Formato de puntaje
GO_SCORE_DECIMALS = 2

# --- TIMER ---
TIMER_START_SECONDS = 60 #*10 # 10 minutos TODO modificar por ahora 60 segundos
TIMER_TEXT = (240, 240, 240)

# --- Tipografía ---
STATS_FONT_SIZE = 20

# --- Condicion Victoria y derrrota ---
META_INGRESOS = 9000.0
MIN_REPUTACION = 20