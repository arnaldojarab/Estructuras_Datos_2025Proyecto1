# src/game/weather.py
import random
import time

from .api_client import APIClient
import os


class WeatherManager:
    """
    Sistema dinámico de clima basado en ráfagas y transiciones Markovianas.
    - Usa los datos de la API city/weather
    - Mantiene estado actual y siguiente
    - Ofrece un multiplicador progresivo (interpolado) para aplicarse a la velocidad del jugador
    """

    # Multiplicadores base para cada condición
    BASE_MULTIPLIERS = {
        "clear": 1.00,
        "clouds": 0.98,
        "rain_light": 0.90,
        "rain": 0.85,
        "storm": 0.75,
        "fog": 0.88,
        "wind": 0.92,
        "heat": 0.90,
        "cold": 0.92,
    }

    def __init__(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        api = APIClient(base_dir)

        payload= api.get_weather()

        data = payload.get("data", {})

        # Condición inicial
        initial = data.get("initial", {"condition": "clear", "intensity": 0.0})
        self.current_condition = initial["condition"]
        self.current_intensity = float(initial.get("intensity", 0.0))

        # Transiciones (Markov)
        self.transition_matrix = data.get("transition", {})

        # Timer de ráfaga
        self.burst_duration = self._random_burst_duration()
        self.burst_start = time.time()

        # Transición suave
        self.transitioning = False
        self.transition_start = 0
        self.transition_duration = 0
        self.from_multiplier = self.BASE_MULTIPLIERS[self.current_condition]
        self.to_multiplier = self.from_multiplier

    # --------------------------
    # Internos
    # --------------------------
    def _random_burst_duration(self) -> float:
        """Duración aleatoria de 45–60 segundos"""
        return random.uniform(10, 11)

    def _choose_next_condition(self) -> str:
        """Elige siguiente condición según matriz de transición de Markov"""
        probs = self.transition_matrix.get(self.current_condition, {})
        if not probs:
            return "clear"
        r = random.random()
        cumulative = 0.0
        for cond, p in probs.items():
            cumulative += p
            if r <= cumulative:
                return cond
        return list(probs.keys())[0]

    def _start_transition(self, next_condition: str):
        """Inicializa transición suave entre condiciones"""
        self.transitioning = True
        self.transition_start = time.time()
        self.transition_duration = random.uniform(3, 5)

        self.from_multiplier = self.BASE_MULTIPLIERS[self.current_condition]
        self.to_multiplier = self.BASE_MULTIPLIERS[next_condition]

        # Actualizar estado
        self.current_condition = next_condition

    # --------------------------
    # API pública
    # --------------------------
    def update(self):
        """Actualizar estado del clima (se llama cada frame)"""
        now = time.time()
        elapsed = now - self.burst_start

        if not self.transitioning and elapsed >= self.burst_duration:
            # Burst terminado → elegir nuevo clima
            next_condition = self._choose_next_condition()
            self._start_transition(next_condition)
            self.burst_start = now
            self.burst_duration = self._random_burst_duration()

        # Si está en transición, revisar si terminó
        if self.transitioning:
            t = (now - self.transition_start) / self.transition_duration
            if t >= 1.0:
                self.transitioning = False

    def current_multiplier(self) -> float:
        """Devuelve el multiplicador de velocidad interpolado"""
        if not self.transitioning:
            return self.BASE_MULTIPLIERS[self.current_condition]

        # Interpolación lineal
        t = (time.time() - self.transition_start) / self.transition_duration
        t = min(max(t, 0.0), 1.0)
        return (1 - t) * self.from_multiplier + t * self.to_multiplier

    def debug_info(self) -> dict:
        """Devuelve datos útiles para mostrar en pantalla"""
        return {
            "condition": self.current_condition,
            "multiplier": round(self.current_multiplier(), 2),
            "time_left": round(self.burst_duration - (time.time() - self.burst_start), 1),
            "transitioning": self.transitioning,
        }
    
    # --------------------------
    # Guardar / Cargar estado
    # --------------------------
    def save_state(self) -> dict:
        """
        Devuelve un diccionario serializable que guarda
        toda la info necesaria para continuar la partida.
        """
        return {
            "current_condition": self.current_condition,
            "current_intensity": self.current_intensity,
            "burst_remaining": max(0.0, self.burst_duration - (time.time() - self.burst_start)),
            "transitioning": self.transitioning,
            "transition_progress": 0 if not self.transitioning else (time.time() - self.transition_start) / self.transition_duration,
            "from_multiplier": self.from_multiplier,
            "to_multiplier": self.to_multiplier,
            "burst_duration": self.burst_duration,
        }

    def load_state(self, state: dict):
        """
        Restaura el estado guardado de la partida.
        """
        self.current_condition = state["current_condition"]
        self.current_intensity = state.get("current_intensity", 0.0)
        self.transitioning = state.get("transitioning", False)
        self.from_multiplier = state.get("from_multiplier", self.BASE_MULTIPLIERS[self.current_condition])
        self.to_multiplier = state.get("to_multiplier", self.BASE_MULTIPLIERS[self.current_condition])
        self.burst_duration = state.get("burst_duration", self._random_burst_duration())
        burst_remaining = state.get("burst_remaining", self.burst_duration)
        self.burst_start = time.time() - (self.burst_duration - burst_remaining)

        if self.transitioning:
            progress = state.get("transition_progress", 0.0)
            self.transition_start = time.time() - progress * self.transition_duration

