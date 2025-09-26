import time

class Cloud:
    def __init__(self, img_white, img_gray, x, y, speed, variant_index=0):
        self.img_white = img_white
        self.img_gray = img_gray
        self.x = x
        self.y = y
        self.speed = speed
        self.variant_index = variant_index

        self.alpha_white = 0
        self.alpha_gray = 0

        self._transitioning = False
        self._t_start = 0
        self._t_duration = 0
        self._from_white = 0
        self._to_white = 0
        self._from_gray = 0
        self._to_gray = 0
        self._t_elapsed = 0  # Tiempo transcurrido de la transición

    def start_transition(self, to_white, to_gray, duration=3, elapsed=0):
        """
        Inicia una transición de alpha. 
        Si 'elapsed' > 0, continúa desde ese tiempo transcurrido.
        """
        self._transitioning = True
        self._t_start = time.time() - elapsed
        self._t_duration = duration
        self._from_white = self.alpha_white
        self._from_gray = self.alpha_gray
        self._to_white = to_white
        self._to_gray = to_gray
        self._t_elapsed = elapsed

    def update(self, dt):
        self.x += self.speed * dt

        if self._transitioning:
            t = (time.time() - self._t_start) / self._t_duration
            if t >= 1:
                t = 1
                self._transitioning = False
            self.alpha_white = int((1 - t) * self._from_white + t * self._to_white)
            self.alpha_gray = int((1 - t) * self._from_gray + t * self._to_gray)
            self._t_elapsed = t * self._t_duration  # guardar progreso

    def draw(self, screen):
        if self.alpha_white > 0:
            img = self.img_white.copy()
            img.set_alpha(self.alpha_white)
            screen.blit(img, (self.x, self.y))
        if self.alpha_gray > 0:
            img = self.img_gray.copy()
            img.set_alpha(self.alpha_gray)
            screen.blit(img, (self.x, self.y))

    def is_fully_transparent(self):
        return self.alpha_white == 0 and self.alpha_gray == 0 and not self._transitioning

    # --- SERIALIZACIÓN ---
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "speed": self.speed,
            "alpha_white": self.alpha_white,
            "alpha_gray": self.alpha_gray,
            "_transitioning": self._transitioning,
            "_from_white": self._from_white,
            "_to_white": self._to_white,
            "_from_gray": self._from_gray,
            "_to_gray": self._to_gray,
            "_t_duration": self._t_duration,
            "_t_elapsed": self._t_elapsed,
            "variant_index": self.variant_index
        }

    @classmethod
    def from_dict(cls, data, img_white, img_gray):
        cloud = cls(img_white, img_gray, data["x"], data["y"], data["speed"], data.get("variant_index", 0))
        cloud.alpha_white = data["alpha_white"]
        cloud.alpha_gray = data["alpha_gray"]
        cloud._transitioning = data["_transitioning"]
        cloud._from_white = data["_from_white"]
        cloud._to_white = data["_to_white"]
        cloud._from_gray = data["_from_gray"]
        cloud._to_gray = data["_to_gray"]
        cloud._t_duration = data["_t_duration"]
        cloud._t_elapsed = data["_t_elapsed"]

        if cloud._transitioning:
            cloud.start_transition(cloud._to_white, cloud._to_gray, duration=cloud._t_duration, elapsed=cloud._t_elapsed)

        return cloud
