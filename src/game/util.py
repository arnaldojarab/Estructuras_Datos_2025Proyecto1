def format_mmss(total_seconds: float) -> str:
    s = max(0, int(total_seconds))
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"

class CountdownTimer:
    def __init__(self, seconds: float):
        self.initial = float(seconds)
        self.time_left = float(seconds)

    def reset(self):
        self.time_left = self.initial

    def tick(self, dt: float):
        self.time_left = max(0.0, self.time_left - dt)

    def finished(self) -> bool:
        return self.time_left <= 0.0
