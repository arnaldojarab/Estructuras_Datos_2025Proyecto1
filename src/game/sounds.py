from pathlib import Path
import pygame

class SoundManager:
    def __init__(self, default_volume: float = 0.30):  # 0.30 = 30% (cámbialo a 0.20 si quieres 20%)
        # ../assets/sfx relativo a ESTE archivo (sounds.py)
        self.sfx_dir = Path(__file__).resolve().parent.parent / "assets" / "sfx"

        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._current_volume: float = float(default_volume)

        self._load("undo", "undo.ogg")  # asegúrate de tener ../assets/sfx/undo.ogg
        self.set_master_volume(self._current_volume)  # aplica el volumen por defecto

    def _load(self, key: str, filename: str) -> None:
        path = self.sfx_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"SFX no encontrado: {path}")
        snd = pygame.mixer.Sound(str(path))
        # si ya tenemos un volumen actual, aplícalo al nuevo sonido
        snd.set_volume(self._current_volume)
        self._cache[key] = snd

    def play(self, key: str, *, fade_ms: int = 0) -> None:
        s = self._cache.get(key)
        if s:
            s.play(fade_ms=fade_ms)

    def set_master_volume(self, v: float) -> None:
        # clamp 0.0–1.0
        v = max(0.0, min(1.0, float(v)))
        self._current_volume = v
        for s in self._cache.values():
            s.set_volume(v)

    def set_master_volume_percent(self, percent: float) -> None:
        self.set_master_volume(float(percent) / 100.0)
