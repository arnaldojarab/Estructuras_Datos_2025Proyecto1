# Global tunables
TILE_SIZE = 22
FPS = 60

SPRITES = {
    "C": "street.png",
    "B": "building.png",
    "P": "park.png",
}

# Movement & stamina
BASE_SPEED = 3.0  # celdas/seg
STAMINA_MAX = 100
STAMINA_CONSUME_PER_CELL = 0.5
STAMINA_RECOVERY_IDLE = 5.0  # por segundo

# --- UI / MENÚ ---
MENU_PANEL_WIDTH = 320
MENU_BG = (40, 40, 48)         # fondo general (opcional)
MENU_PANEL_GRAY = (90, 90, 95) # panel vertical
BTN_BG = (180, 180, 185)
BTN_BG_HOVER = (210, 210, 215)
BTN_TEXT = (20, 20, 24)
UI_FONT_NAME = None            # None = fuente por defecto de pygame
UI_FONT_SIZE = 28

# --- TIMER ---
TIMER_START_SECONDS = 60  # 10 minutos TODO modificar por ahora 60 segundos
TIMER_TEXT = (240, 240, 240)

# --- Tipografía ---
STATS_FONT_SIZE = 20