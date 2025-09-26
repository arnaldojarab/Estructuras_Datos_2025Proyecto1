from collections import deque
import pygame

from . import settings

class Player:
    def __init__(self, cell_pos):
        ts = settings.TILE_SIZE
        # Centro del tile inicial
        self.x = cell_pos[0] * ts + ts // 2
        self.y = cell_pos[1] * ts + ts // 2
        # Radio proporcional al tamaño del tile (ajusta si quieres más/menos “gordo”)
        self.radius = int(ts * 0.35)
         # --- resistencia ---
        self.stamina = 100        # valor inicial
        self.exhausted = False    # estado actual

         # --- historial de posiciones para "Ctrl+Z" ---
        self._pos_history = deque(maxlen=50)  # ring buffer
        self._snapshot_timer = 0.0
        self._snapshot_every = 1.5           # segundos entre snapshots
        self._pos_history.append((self.x, self.y))  # punto de partida

    def _collides_at(self, nx, ny, game_map):
        """
        ¿Colisiona el círculo del jugador centrado en (nx, ny) con algún tile bloqueado?
        Revisamos los tiles del AABB que envuelve al círculo.
        """
        ts = settings.TILE_SIZE
        left_tx   = int((nx - self.radius) // ts)
        right_tx  = int((nx + self.radius) // ts)
        top_ty    = int((ny - self.radius) // ts)
        bottom_ty = int((ny + self.radius) // ts)

        for ty in range(top_ty, bottom_ty + 1):
            for tx in range(left_tx, right_tx + 1):
                if game_map.is_blocked(tx, ty):
                    return True
        return False

    def move_with_collision(self, dx, dy, game_map, stamina_cost=0.1):
        """
        Movimiento con separación de ejes (X luego Y) para permitir “deslizamiento” suave
        al chocar con paredes. Bloquea el eje donde habría colisión.
        """
        #if self.exhausted:
            #return  # no se mueve si está exhausto

        old_x, old_y = self.x, self.y

        # Movimiento eje X
        nx = self.x + dx
        if not self._collides_at(nx, self.y, game_map):
            self.x = nx

        # Movimiento eje Y
        ny = self.y + dy
        if not self._collides_at(self.x, ny, game_map):
            self.y = ny

        # Si efectivamente se movió, baja resistencia
        if (self.x, self.y) != (old_x, old_y):
            self.stamina = max(0, self.stamina - stamina_cost)
            if self.stamina <= 0:
                self.exhausted = True

    def update(self, dt, peso):
        """
        Recupera stamina con el tiempo.
        dt: delta time en segundos
        """
        if peso > 4:
            recover_rate = 3 * dt
        else:
            recover_rate = 5 * dt  # puntos por segundo (ajusta)

        

        if self.exhausted:
            # Solo recupera hasta 30%
            if self.stamina < 30:
                self.stamina = min(30, self.stamina + recover_rate)
            if self.stamina >= 30:
                self.exhausted = False
        else:
            # Recupera poco a poco hasta 100
            if self.stamina < 100:
                self.stamina = min(100, self.stamina + recover_rate * 0.5)

        self._snapshot_timer += dt
        if self._snapshot_timer >= self._snapshot_every:
            self._snapshot_timer = 0.0
            last = self._pos_history[-1] if self._pos_history else None
            moved = (not last) or (abs(self.x - last[0]) + abs(self.y - last[1]) >= 1.0)
            if moved:
                self._pos_history.append((self.x, self.y))

    def draw_stamina(self, screen):
        bar_w, bar_h = 120, 14   # tamaño de la barra
        margin = 10              # margen desde los bordes

        # Calcular coordenadas (arriba a la derecha)
        x = screen.get_width() - bar_w - margin
        y = margin

        # fondo gris
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_w, bar_h))

        # parte proporcional
        fill_w = int(bar_w * (self.stamina / 100))
        color = (200, 50, 50) if self.exhausted else (50, 200, 50)
        pygame.draw.rect(screen, color, (x, y, fill_w, bar_h))

        # borde
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_w, bar_h), 2)



    def draw(self, screen):
        pygame.draw.circle(screen, (200, 230, 255), (int(self.x), int(self.y)), self.radius)


    def get_speed(self, peso_total):
        speed = 1
        if self.stamina < 30:
            speed = speed * 0.8
        if self.exhausted:
            speed = speed * 0
        else:
            speed = speed * 1

        Mpeso = max(0.8, 1 - 0.03 * peso_total )

        speed * Mpeso
        

        return speed
    

    def reset(self):
        self.grid_pos = (1, 1)
        self.pixel_pos = [
            self.grid_pos[0] * settings.TILE_SIZE,
            self.grid_pos[1] * settings.TILE_SIZE,
        ]
        self.stamina = 100
        ts = settings.TILE_SIZE
        start_cx = 1 * ts + ts // 2
        start_cy = 1 * ts + ts // 2
        self.x = start_cx
        self.y = start_cy

        # reset del historial
        self._pos_history.clear()
        self._pos_history.append((self.x, self.y))
        self._snapshot_timer = 0.0

    def undo_position(self):
        """
        Retrocede a la posición previa del historial.
        Evita quedarse en el mismo punto si el último snapshot == posición actual.
        """
        if len(self._pos_history) > 1:
            # descarta el snapshot más reciente (pos actual o casi actual)
            self._pos_history.pop()
            x, y = self._pos_history[-1]
            self.x, self.y = x, y
