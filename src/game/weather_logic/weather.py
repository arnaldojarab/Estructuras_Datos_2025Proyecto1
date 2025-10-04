import random
import os
from ..api_client import APIClient
from .weather_visuals import WeatherVisuals


class WeatherManager:
    """
    Lógica del clima: ráfagas, condiciones actuales y transiciones.
    """

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

    def __init__(self, window_w, window_h):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", ".."))
        api = APIClient(base_dir)

        payload = api.get_weather()
        data = payload.get("data", {})

        # Condición inicial
        initial = data.get("initial", {"condition": "clear", "intensity": 0.0})
        self.current_condition = initial["condition"]
        self.current_intensity = float(initial.get("intensity", 0.0))

        # Transiciones (Markov)
        self.transition_matrix = data.get("transition", {})

        # Temporizadores internos
        self.burst_duration = self._random_burst_duration()
        self.burst_elapsed = 0.0  # acumulado con dt

        # Transición suave
        self.transitioning = False
        self.transition_elapsed = 0.0
        self.transition_duration = 0.0
        self.from_multiplier = self.BASE_MULTIPLIERS[self.current_condition]
        self.to_multiplier = self.from_multiplier

        self.visuals = WeatherVisuals(window_w, window_h)

    # --------------------------
    # Internos
    # --------------------------
    def _random_burst_duration(self) -> float:
        return random.uniform(60, 90)

    def _choose_next_condition(self) -> str:
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
        self.transitioning = True
        self.transition_elapsed = 0.0
        self.transition_duration = random.uniform(3, 5)

        self.from_multiplier = self.BASE_MULTIPLIERS[self.current_condition]
        self.to_multiplier = self.BASE_MULTIPLIERS[next_condition]

        self.visuals.handle_condition_change(next_condition)
        self.current_condition = next_condition

    # --------------------------
    # API pública
    # --------------------------
    def update(self, dt: float):
        # Avanzar tiempo de ráfaga
        self.burst_elapsed += dt

        # Si la ráfaga terminó, escoger nuevo clima
        if not self.transitioning and self.burst_elapsed >= self.burst_duration:
            next_condition = self._choose_next_condition()
            self._start_transition(next_condition)
            self.burst_elapsed = 0.0
            self.burst_duration = self._random_burst_duration()

        # Revisar transición
        if self.transitioning:
            self.transition_elapsed += dt
            if self.transition_elapsed >= self.transition_duration:
                self.transitioning = False

        self.visuals.update(dt, self.current_condition, self.transitioning)

    def current_multiplier(self) -> float:
        if not self.transitioning:
            return self.BASE_MULTIPLIERS[self.current_condition]

        t = self.transition_elapsed / self.transition_duration
        t = min(max(t, 0.0), 1.0)
        return (1 - t) * self.from_multiplier + t * self.to_multiplier

    def debug_info(self) -> dict:
        return {
            "condition": self.current_condition,
            "multiplier": round(self.current_multiplier(), 2),
            "time_left": round(self.burst_duration - self.burst_elapsed, 1),
            "transitioning": self.transitioning,
        }

    def draw_weather_overlay(self, screen, player, dt):
        self.visuals.draw_overlay(screen, player, dt, self.current_condition)

    def reset(self, window_w=None, window_h=None):
        """
        Reinicia el WeatherManager y su parte visual.
        """
        window_w = window_w or self.visuals.window_w
        window_h = window_h or self.visuals.window_h

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", ".."))
        api = APIClient(base_dir)
        payload = api.get_weather()
        data = payload.get("data", {})

        # Condición inicial
        initial = data.get("initial", {"condition": "clear", "intensity": 0.0})
        self.current_condition = initial["condition"]
        self.current_intensity = float(initial.get("intensity", 0.0))

        # Transiciones (Markov)
        self.transition_matrix = data.get("transition", {})

        # Temporizadores
        self.burst_duration = self._random_burst_duration()
        self.burst_elapsed = 0.0

        # Transición
        self.transitioning = False
        self.transition_elapsed = 0.0
        self.transition_duration = 0.0
        self.from_multiplier = self.BASE_MULTIPLIERS[self.current_condition]
        self.to_multiplier = self.from_multiplier

        self.visuals = WeatherVisuals(window_w, window_h)

    def get_current_condition(self):
        return self.current_condition

    # --------------------------
    # Guardar / Cargar estado
    # --------------------------
    def save_state(self) -> dict:
        base_state = {
            "current_condition": self.current_condition,
            "current_intensity": self.current_intensity,
            "burst_remaining": max(0.0, self.burst_duration - self.burst_elapsed),
            "transitioning": self.transitioning,
            "transition_progress": 0 if not self.transitioning else self.transition_elapsed / self.transition_duration,
            "from_multiplier": self.from_multiplier,
            "to_multiplier": self.to_multiplier,
            "burst_duration": self.burst_duration,
        }
        base_state["visuals"] = self.visuals.save_state()
        return base_state

    def load_state(self, state: dict):
        try:
            if not isinstance(state, dict):
                return False
            self.current_condition = state["current_condition"]
            self.current_intensity = state.get("current_intensity", 0.0)
            self.transitioning = state.get("transitioning", False)
            self.from_multiplier = state.get("from_multiplier", self.BASE_MULTIPLIERS[self.current_condition])
            self.to_multiplier = state.get("to_multiplier", self.BASE_MULTIPLIERS[self.current_condition])
            self.burst_duration = state.get("burst_duration", self._random_burst_duration())
            burst_remaining = state.get("burst_remaining", self.burst_duration)
            self.burst_elapsed = self.burst_duration - burst_remaining

            if self.transitioning:
                progress = state.get("transition_progress", 0.0)
                self.transition_elapsed = progress * self.transition_duration

            self.visuals.load_state(state.get("visuals", {}))
            return True
        except Exception:
            return False