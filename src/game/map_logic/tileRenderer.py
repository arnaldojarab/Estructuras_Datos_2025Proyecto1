# tile_renderer.py
import os
import random
import pygame
from .. import settings

class TileRenderer:
    """
    Encargada de asignar variantes a cada tile y devolver la superficie correcta.
    Mantiene cache de superficies para no recargarlas cada frame.
    """
    def __init__(self):
        self.cache = {}  # {(sym, variant): surface}
        self.assets_dir = os.path.join(os.path.dirname(__file__),"..", "..", "assets", "tiles")

    def get_surface(self, sym, variant, tiles, x=None, y=None):
        """
        Devuelve la superficie de un tile. Si variant es None, se elige automáticamente.
        """
        ##if variant is None:
        ##    variant = self.choose_variant(sym, tiles, x, y)

        key = (sym, variant)
        if key not in self.cache:
            self.cache[key] = self.load_surface(sym, variant)
        return self.cache[key]

    def choose_variant(self, sym, tiles, x, y):
        # vecinos (símbolo solamente)
        up = tiles[y-1][x][0] if y > 0 else None
        down = tiles[y+1][x][0] if y < len(tiles)-1 else None
        left = tiles[y][x-1][0] if x > 0 else None
        right = tiles[y][x+1][0] if x < len(tiles[0])-1 else None

        # Vecinos diagonales
        up_left    = tiles[y-1][x-1][0] if y > 0 and x > 0 else None
        up_right   = tiles[y-1][x+1][0] if y > 0 and x < len(tiles[0])-1 else None
        down_left  = tiles[y+1][x-1][0] if y < len(tiles)-1 and x > 0 else None
        down_right = tiles[y+1][x+1][0] if y < len(tiles)-1 and x < len(tiles[0])-1 else None

        if sym == "B":
            return self._choose_B(up, down, left, right)
        elif sym == "P":
            return self._choose_P(up, down, left, right)
        elif sym == "C":
            return self._choose_C(up, down, left, right, up_left, up_right, down_left, down_right)

    # -----------------------------------------------
    # Métodos separados para cada tipo de sym

    def _choose_B(self, up, down, left, right):
        if (up == left == "P" or up == left == "C" or up == left is None or 
            (up == "P" and left in ("C", None)) or 
            (up == "C" and left in ("P", None)) or 
            (up is None and left in ("P", "C"))):
            if down == right == "B":
                return 1

        elif (left in ("P", "C", None)) and up == right == down == "B":
            return 2

        elif (down == left == "P" or down == left == "C" or down == left is None or
            (left == "P" and down in ("C", None)) or 
            (left == "C" and down in ("P", None)) or
            (left is None and down in ("P", "C"))):
            if up == right == "B":
                return 3

        elif (down in ("P", "C", None)) and left == up == right == "B":
            return 4

        elif (down == right == "P" or down == right == "C" or down == right is None or
            (down == "P" and right in ("C", None)) or 
            (down == "C" and right in ("P", None)) or
            (down is None and right in ("P", "C"))):
            if up == left == "B":
                return 5

        elif (right in ("P", "C", None)) and up == down == left == "B":
            return 6

        elif (up == right == "C" or up == right == "P" or up == right is None or
            (up == "C" and right in ("P", None)) or 
            (up == "P" and right in ("C", None)) or
            (up is None and right in ("P", "C"))):
            if left == down == "B":
                return 7

        elif (up in ("C", "P", None)) and down == right == left == "B":
            return 8

        elif left == right == up == down == "B":
            variants = [9, 10, 11, 12, 13, 14]
            weights = [0.4, 0.4, 0.05, 0.05, 0.05, 0.05]
            return random.choices(variants, weights=weights, k=1)[0]
        return 0

    def _choose_P(self, up, down, left, right):
        if down == "P" and (up in ("B", "C", None)) and (left in ("B", "C", None)) and (right in ("B", "C", None)):
            variants = [1, 2, 3]
            weights = [0.3, 0.3, 0.3]
            return random.choices(variants, weights=weights, k=1)[0] 

        elif up == "P" and down == "P" and (left in ("B", "C", None)) and (right in ("B", "C", None)):
            variants = [4, 5, 6]
            weights = [0.3, 0.3, 0.3]
            return random.choices(variants, weights=weights, k=1)[0] 

        elif up == "P" and (down in ("B", "C", None)) and (left in ("B", "C", None)) and (right in ("B", "C", None)):
            variants = [7, 8, 9]
            weights = [0.3, 0.3, 0.3]
            return random.choices(variants, weights=weights, k=1)[0] 

        elif (up in ("B", "C", None)) and (down in ("B", "C", None)) and (left in ("B", "C", None)) and (right in ("B", "C", None)):
            variants = [10, 11, 12]
            weights = [0.3, 0.3, 0.3]
            return random.choices(variants, weights=weights, k=1)[0]
        return 0
        
    def _choose_C(self, up, down, left, right, up_left, up_right, down_left, down_right):
        # Caso 1
        if left == "C" and right == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)):
            variants = [1, 2, 3, 4]
            weights = [0.25]*4
            return random.choices(variants, weights=weights, k=1)[0]
        

        # Caso 2
        elif up_right == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)) and (left in ("C", "P", None)) and (right in ("C", "P", None)):
            return 5

        # Caso 3
        elif left == "P" and right == "P" and up == "B" and  (down in ("C", "P", None)):
            variants = [25, 6, 7, 8, 9]
            weights = [0.2]*5
            return random.choices(variants, weights=weights, k=1)[0]
        
        # Caso 4
        elif up == "B" and (down in ("C", "P", None)):
            if not (left == right == "P") and (left in ("C", "P", None)) and (right in ("C", "P", None)):
                variants = [6, 7, 8, 9]
                weights = [0.25]*4
                return random.choices(variants, weights=weights, k=1)[0]

        # Caso 5
        elif up_left == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)) and (left in ("C", "P", None)) and (right in ("C", "P", None)):
            return 10

        # Caso 6
        elif up_left == right == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)) and (left in ("C", "P", None)):
            return 11

        # Caso 7
        elif left == "B" and (right in  ("C", None)) and (up in ("C", "P", None)) and (down in ("C", "P", None)):
            variants = [12, 13, 14, 15]
            weights = [0.25]*4
            return random.choices(variants, weights=weights, k=1)[0]

        # Caso 8
        elif down_left == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)) and (left in ("C", "P", None)) and (right in ("C", "P", None)):
            return 16

        # Caso 9
        elif up == "C" and down == "B" and (left in ("C", "P", None)) and (right in ("C", "P", None)):
            variants = [17, 18, 19, 20]
            weights = [0.25]*4
            return random.choices(variants, weights=weights, k=1)[0]

        # Caso 10
        elif down_right == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)) and (left in ("C", "P", None)) and (right in ("C", "P", None)):
            return 21

        # Caso 11
        elif down_right == left == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)) and (right in ("C", "P", None)):
            return 22

        # Caso 12
        elif left == "P" and right == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)):
            variants = [23, 1, 2, 3, 4]
            weights = [0.2]*5
            return random.choices(variants, weights=weights, k=1)[0]

        # Caso 13
        elif left == "B" and right == "P" and (up in ("C", "P", None)) and (down in ("C", "P", None)):
            variants = [24, 12, 13, 14, 15]
            weights = [0.2]*5
            return random.choices(variants, weights=weights, k=1)[0]


        # Caso 14
        elif left == right == "B" and (up in ("C", "P", None)) and (down in ("C", "P", None)):
            variants = [26, 27, 28]
            weights = [0.33]*3
            return random.choices(variants, weights=weights, k=1)[0]

        # Caso 15
        elif left == right == "P" and (up in ("C", "P", None)) and (down in ("C", "P", None)):
            variants = [29, 30]
            weights = [0.5]*2
            return random.choices(variants, weights=weights, k=1)[0]

        # Caso 16
        elif (up in ("C", "P", None)) and (down in ("C", "P", None)) and \
            (left in ("C", "P", None)) and (right in ("C", "P", None)):
            # Restricciones: no tener "P" en lados opuestos
            if not (up == "P" and down == "P") and not (right == "P" and left == "P"):
                return 30
        return 0


    def load_surface(self, sym, variant):
        """
        Carga la imagen de disco y la escala según TILE_SIZE. 
        Si no hay archivo, devuelve un surface de color placeholder.
        """
        sprites = {
            "C": "street.png",
            "B": "building.png",
            "P": "park.png",
        }


        sprite_file = sprites.get(sym)
        ts = settings.TILE_SIZE
        if sprite_file:
            name, ext = os.path.splitext(sprite_file)
            variant_file = f"{name}_{variant}{ext}"  # permite variantes: p.ej park_0.png
            path = os.path.join(self.assets_dir, variant_file)
            if os.path.exists(path):
                img = pygame.image.load(path)#.convert_alpha()
                img = pygame.transform.scale(img, (ts, ts))
                return img

        # fallback a color
        color = self._color_for_symbol(sym)
        surf = pygame.Surface((ts, ts))
        surf.fill(color)
        return surf

    def _color_for_symbol(self, sym: str):
        if sym == "C":
            return (110, 110, 110)
        if sym == "B":
            return (139, 0, 0)
        if sym == "P":
            return (70, 70, 0)
        return (90, 120, 160)