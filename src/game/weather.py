# Placeholder for weather Markov/interpolation system
class WeatherManager:
    def __init__(self, data):
        self.states = data.get("states", [])
        self.transition = data.get("transition", [])
        self.multipliers = data.get("multipliers", {})
        self.current = self.states[0] if self.states else "clear"

    def multiplier(self):
        return self.multipliers.get(self.current, 1.0)
