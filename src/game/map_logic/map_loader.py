
import json
import os
from .. import settings
from ..api_client import APIClient
from .tileRenderer import TileRenderer   


class MapLoader:
    def __init__(self):
        self.meta = {}
        self.tiles = []        # tiles[y][x] = [sym, variant]
        self.legend = {}
        self.renderer = TileRenderer()
        self._w = 0
        self._h = 0

    def load_default(self):
        """
        Intenta API y, si falla, lee /data/ciudad.json
        """
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..", ".."))
        api = APIClient(base_dir)

        try:
            data = api.get_map()
        except Exception:
            local_file = os.path.join(base_dir, "data", "ciudad.json")
            with open(local_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        self._load_from_payload(data)
        return self

    def _load_from_payload(self, payload: dict):
        """
        Normaliza tiles a formato [sym, variant].
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

        raw_tiles = data["tiles"]
        self.tiles = []
        for y, row in enumerate(raw_tiles):
            new_row = []
            for x, sym in enumerate(row):
                if isinstance(sym, list):
                    tile = sym
                else:
                    tile = [sym, None]

                # Asignamos variante solo si es None
                if tile[1] is None:
                    tile[1] = self.renderer.choose_variant(tile[0], raw_tiles, x, y)
                new_row.append(tile)
            self.tiles.append(new_row)

        self.legend = data["legend"]
        self._w, self._h = self.meta["width"], self.meta["height"]

    def draw(self, screen):
        ts = settings.TILE_SIZE
        for y, row in enumerate(self.tiles):
            for x, (sym, variant) in enumerate(row):
                surf = self.renderer.get_surface(sym, variant, self.tiles, x, y)
                if surf:
                    screen.blit(surf, (x * ts, y * ts))

    def reset(self):
        """
        Reinicia el MapLoader a estado inicial, borrando mapa y legend.
        """
        self.meta = {}
        self.tiles = []        # lista vacía de tiles
        self.legend = {}
        self._w = 0
        self._h = 0
        self.load_default()



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
        sym = self.tiles[y][x][0]  # ahora accedemos al primer elemento [sym, variant]
        info = self.legend.get(sym, {})
        return bool(info.get("blocked", False))

    def surface_weight(self, x: float, y: float) -> float:
        """
        Peso de la superficie según la posición en píxeles (x,y).
        Convierte a coordenadas de tile automáticamente.
        """
        tx = int(x // settings.TILE_SIZE)
        ty = int(y // settings.TILE_SIZE)

        if ty < 0 or ty >= self._h or tx < 0 or tx >= self._w:
            return 1.0

        sym = self.tiles[ty][tx][0]  # accedemos al símbolo
        info = self.legend.get(sym, {})
        return float(info.get("surface_weight", 1.0))
    
    def is_park(self, x: int, y: int) -> bool:
        """
        Devuelve True si el tile en (x,y) es un parque ('P').
        """

        tx = int(x // settings.TILE_SIZE)
        ty = int(y // settings.TILE_SIZE)

        if ty < 0 or ty >= self._h or tx < 0 or tx >= self._w:
            return False
        sym = self.tiles[ty][tx][0]
        return sym == "P" or (self.legend.get(sym, {}).get("name", "").lower() == "park")              

    # -------- guardar / cargar como dict --------
    def save_map(self) -> dict:
        """
        Devuelve un dict con el mapa actual, incluyendo variantes de cada tile.
        """
        return {
            "meta": self.meta,
            "tiles": self.tiles,   # cada tile es [sym, variant]
            "legend": self.legend
        }

    def load_map(self, state: dict):
        """
        Carga un mapa desde un dict previamente guardado con save_map().
        """
        try:
            if not isinstance(state, dict):
                return False
            self.meta = state.get("meta", {})
            self.tiles = state.get("tiles", [])
            self.legend = state.get("legend", {})
            self._w = self.meta.get("width", len(self.tiles[0]) if self.tiles else 0)
            self._h = self.meta.get("height", len(self.tiles) if self.tiles else 0)

            return True
        except Exception:
            return False