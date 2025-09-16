# import json, os, pygame
# from . import settings

# class MapLoader:
#     def __init__(self):
#         self.grid = None
#         self.tile_surf = {}

#     def load_default(self):
#         data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "ciudad.json")
#         with open(data_path, "r", encoding="utf-8") as f:
#             m = json.load(f)

#         self.grid = m
#         # generar superficies simples por tipo (placeholder)
#         self.tile_surf = {
#             "R": pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE)),
#             "B": pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE)),
#             "P": pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE)),
#             "S": pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE)),
#         }
#         self.tile_surf["R"].fill((100,100,100))
#         self.tile_surf["B"].fill((60,60,80))
#         self.tile_surf["B"].fill((60,120,60))
#         self.tile_surf["S"].fill((180,160,90))

#         return self

#     def draw(self, screen):
#         tiles = self.grid["tiles"]
#         for y, row in enumerate(tiles):
#             for x, c in enumerate(row):
#                 surf = self.tile_surf.get(c)
#                 if surf:
#                     screen.blit(surf, (x*64, y*64))

# src/game/map_loader.py
# Loader del mapa adaptado al nuevo formato con 'data' y 'legend'
import json
import os
import pygame
from . import settings
from .api_client import APIClient


def _color_for_symbol(sym: str, legend: dict) -> tuple:
    """
    Colorea por tipo de tile si no hay sprites definidos.
    - street (C): gris
    - building (B): oscuro
    - park (P): verde
    - default: azul tenue
    """
    info = legend.get(sym, {})
    name = (info.get("name") or "").lower()
    if name == "street":
        return (110, 110, 110)
    if name == "building":
        return (55, 55, 75)
    if name == "park":
        return (70, 140, 70)
    return (90, 120, 160)


class MapLoader:
    """
    Carga el mapa desde la API (urllib) y hace fallback al archivo local.
    Mantiene:
      - self.meta: dict con width, height, goal, max_time, city_name, etc.
      - self.tiles: matriz 2D (lista de listas) de símbolos (p.ej. 'C','B','P')
      - self.legend: dict de propiedades por símbolo
      - helpers: is_blocked(x,y), surface_weight(x,y)
    """

    def __init__(self):
        self.meta = {}
        self.tiles = []        # 2D: tiles[y][x] -> 'C' | 'B' | 'P' | ...
        self.legend = {}       # p.ej. {'C': {'name': 'street','surface_weight':1.0}, 'B': {'name':'building','blocked':True}}
        self.tile_surf = {}    # superficies coloreadas por símbolo
        self._w = 0
        self._h = 0

    # API compa-friendly para engine actual
    def load_default(self):
        """
        Intenta API y, si falla, lee /data/ciudad.json
        Devuelve self para encadenar: MapLoader().load_default()
        """
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        api = APIClient(base_dir)
        data = api.get_map()
        self._load_from_payload(data)
        self._prepare_surfaces()
        return self

    # --------- Internos ---------

    def _load_from_payload(self, payload: dict):
        """
        Acepta el nuevo formato:
        {
          "version": "1.0",
          "data": {
            "version": "1.1",
            "city_name": "TigerCity",
            "width": 30,
            "height": 30,
            "goal": 1500.0,
            "max_time": 900,
            "tiles": [[...], ...],
            "legend": { "C": {...}, "B": {...}, "P": {...} }
          }
        }
        """
        if not isinstance(payload, dict) or "data" not in payload:
            raise ValueError("Mapa inválido: se esperaba un dict con clave 'data'.")

        data = payload["data"]
        required = ["width", "height", "tiles", "legend"]
        for k in required:
            if k not in data:
                raise ValueError(f"Mapa inválido: falta '{k}' en data.")

        self.meta = {
            "version": data.get("version"),
            "city_name": data.get("city_name"),
            "width": int(data["width"]),
            "height": int(data["height"]),
            "goal": data.get("goal"),
            "max_time": data.get("max_time"),
        }

        tiles = data["tiles"]
        if not isinstance(tiles, list) or not tiles or not isinstance(tiles[0], list):
            raise ValueError("Mapa inválido: 'tiles' debe ser una matriz (lista de listas).")

        # Validar dimensiones
        h = len(tiles)
        w = len(tiles[0])
        if h != self.meta["height"] or w != self.meta["width"]:
            # No abortamos; tomamos las dimensiones reales de tiles por seguridad.
            self.meta["width"], self.meta["height"] = w, h

        self.tiles = tiles
        self.legend = data["legend"]
        self._w, self._h = self.meta["width"], self.meta["height"]

    def _prepare_surfaces(self):
        """
        Prepara superficies por símbolo según legend (colores por tipo).
        """
        ts = settings.TILE_SIZE
        symbols = set()
        for row in self.tiles:
            for sym in row:
                symbols.add(sym)

        self.tile_surf = {}
        for sym in symbols:
            surf = pygame.Surface((ts, ts))
            surf.fill(_color_for_symbol(sym, self.legend))
            self.tile_surf[sym] = surf

    # --------- API de consulta usada por otros sistemas ---------

    @property
    def width(self) -> int:
        return self._w

    @property
    def height(self) -> int:
        return self._h

    def is_blocked(self, x: int, y: int) -> bool:
        """
        True si el tile en (x,y) está bloqueado según legend (p.ej., 'B' con blocked=True).
        """
        if y < 0 or y >= self._h or x < 0 or x >= self._w:
            return True
        sym = self.tiles[y][x]
        info = self.legend.get(sym, {})
        return bool(info.get("blocked", False))

    def surface_weight(self, x: int, y: int) -> float:
        """
        Peso de la superficie para calcular coste/velocidad (default 1.0).
        """
        if y < 0 or y >= self._h or x < 0 or x >= self._w:
            return 1.0
        sym = self.tiles[y][x]
        info = self.legend.get(sym, {})
        return float(info.get("surface_weight", 1.0))

    # --------- Render simple ---------

    def draw(self, screen):
        """
        Dibuja el mapa con superficies por símbolo. Este método asume
        que todo cabe en pantalla (puedes añadir cámara/offset si es grande).
        """
        ts = settings.TILE_SIZE
        for y, row in enumerate(self.tiles):
            for x, sym in enumerate(row):
                surf = self.tile_surf.get(sym)
                if surf:
                    screen.blit(surf, (x * ts, y * ts))
