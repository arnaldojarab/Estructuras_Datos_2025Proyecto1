from pathlib import Path
import pygame

class SoundManager:
    def __init__(self):
        # ../assets/sfx relativo a ESTE archivo (sounds.py)
        # si sounds.py está en tu_paquete/audio/sounds.py,
        # esto apunta a tu_paquete/assets/sfx
        self.sfx_dir = Path(__file__).resolve().parent.parent / "assets" / "sfx"

        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._load("undo", "undo.ogg")  # asegúrate de tener ../assets/sfx/trumpet.ogg

    def _load(self, key: str, filename: str) -> None:
        path = self.sfx_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"SFX no encontrado: {path}")
        # str(path) por compatibilidad con pygame < 2.5
        self._cache[key] = pygame.mixer.Sound(str(path))

    def play(self, key: str, *, fade_ms: int = 0) -> None:
        s = self._cache.get(key)
        if s:
            s.play(fade_ms=fade_ms)

    def set_master_volume(self, v: float) -> None:
        for s in self._cache.values():
            s.set_volume(v)