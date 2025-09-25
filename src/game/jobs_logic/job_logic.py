from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
import pygame

from .job_loader import JobLoader
from .job import Job

from .OrderManager import HistoryEntry
# ---- Marcadores en pantalla ----
@dataclass
class PickupMarker:
    px: int
    py: int
    job_id: str
    expires_at: float  # absoluto en segundos del reloj interno

@dataclass
class DropoffMarker:
    px: int
    py: int
    job_id: str
    due_at: float  # absoluto: si se llega antes => onTime=True


class JobLogic:
    """
    Maneja ofertas (pickup), aceptaciones (inventory) y entregas (dropoff + history).
    Mantiene y dibuja marcadores y maneja timers relativos.
    """

    # Distancias en tiles
    _PICKUP_RADIUS_TILES = 3
    _DROPOFF_RADIUS_TILES = 3

    def __init__(self, tile_size: int, max_active_offers: int = 4) -> None:
        self.tile_size = tile_size
        self.max_active_offers = max_active_offers

        # Atributos pedidos
        self.jobs = JobLoader()
        self.jobs.load_from_api()
        self.orders = self.jobs.create_order_manager()

        self._job_offer_elapsed = 3.0
        self._TIME_TO_EXPIRE = 15.0
        self._DROPOFF_LATE_AFTER = 10.0

        self._game_elapsed = 0.0

        # Estado de markers
        self._pickup_markers: List[PickupMarker] = []
        self._dropoff_markers: List[DropoffMarker] = []

        # Interno: cada cuánto intento lanzar oferta
        self._offer_interval = 5.0

        # Reputacion
        self.reputation = 70  # valor inicial

    # =================== API pública ===================

    def reset(self) -> None:
        """Limpia estado de partida (no re-fetch), reconstruye estructuras de ejecución."""
        self.orders = self.jobs.create_order_manager()
        self._pickup_markers.clear()
        self._dropoff_markers.clear()
        self._job_offer_elapsed = 3.0
        self._game_elapsed = 0.0

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        """Avanza timers, lanza ofertas, expira pickups y verifica proximidades."""
        self._game_elapsed += dt
        self._job_offer_elapsed += dt

        # Lanzar ofertas periódicamente si hay cupo de pickups activos
        while self._job_offer_elapsed >= self._offer_interval:
            if len(self._pickup_markers) < self.max_active_offers and len(self._dropoff_markers) < self.max_active_offers:
                self._launch_a_job()
            self._job_offer_elapsed -= self._offer_interval

        # Expirar pickups que no se aceptaron a tiempo
        self._expire_pickup_offers()

        # Proximidades (pickup y dropoff)
        self._check_proximity(player_x, player_y)

    def draw(self, screen: pygame.Surface) -> None:
        """Dibuja markers de pickups (amarillo) y dropoffs (verde)."""
        # Pickups
        for m in self._pickup_markers:
            pygame.draw.circle(screen, (255, 255, 0), (m.px, m.py), 6)
            pygame.draw.circle(screen, (0, 0, 0), (m.px, m.py), 6, 2)

        # Dropoffs (solamente el current)
        currentJob = self.orders.getCurrentJob()
        if currentJob:
            m = next((d for d in self._dropoff_markers if d.job_id == currentJob.id), None)
            pygame.draw.circle(screen, (0, 200, 0), (m.px, m.py), 6)
            pygame.draw.circle(screen, (0, 0, 0), (m.px, m.py), 6, 2)
            
        # Dropoffs (todos)
        # for m in self._dropoff_markers:
        #     pygame.draw.circle(screen, (0, 200, 0), (m.px, m.py), 6)
        #     pygame.draw.circle(screen, (0, 0, 0), (m.px, m.py), 6, 2)
    
    # Getters y Setters

    def getInventory(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de objetos Job actualmente en inventario."""
        out: List = []
        for jid in self.orders.inventory:
            job: Job = self.jobs.get(jid)
            out.append(job)
        return out
    
    def getInventoryIDs(self) -> List[str]:
        """Devuelve la lista de IDs de objetos Job actualmente en inventario."""
        return self.orders.inventory

    def getHistory(self) -> List[Dict[str, Any]]:
        """
        Lista de dicts con información histórica.
        Cada item: {"job": <Job as dict>, "accepted": bool, "onTime": bool}
        """
        out: List[Dict[str, Any]] = []
        for h in self.orders.history:
            job: Job = self.jobs.get(h.job_id)
            out.append({
                "job": job,
                "accepted": h.accepted,
                "onTime": h.onTime,
            })
        return out
    
    def getHistoryIDs(self) -> List[HistoryEntry]:
        """
        Lista de dicts con información histórica.
        Cada item: {"job_id": str, "accepted": bool, "onTime": bool}
        """
        return self.orders.history
    
    def getReputation(self) -> int:
        """Devuelve la reputación actual (0-100)."""
        return self.reputation
    
    def getMoney(self) -> float:
        """Devuelve el dinero ganado por entregas."""
        total = 0.0
        for h in self.orders.history:
            if h.accepted:
                job = self.jobs.get(h.job_id)
                total += job.payout
        return total
    
    def getWeight(self) -> float:
        "Devuelve el peso de los pedidos en el inventario"
        total = 0.0
        for h in self.orders.inventory:
                job = self.jobs.get(h)
                total += job.weight
        return total

    # =================== Lógica interna ===================

    def _grid_center_to_px(self, gx: int, gy: int) -> Tuple[int, int]:
        ts = self.tile_size
        return gx * ts + ts // 2, gy * ts + ts // 2

    def _launch_a_job(self) -> None:
        job = self.orders.pop_next_job()
        if not job:
            return
        gx, gy = job.pickup
        px, py = self._grid_center_to_px(gx, gy)
        expires_at = self._game_elapsed + self._TIME_TO_EXPIRE
        self._pickup_markers.append(PickupMarker(px, py, job.id, expires_at))

    def _expire_pickup_offers(self) -> None:
        """Borra pickups vencidos y registra NO aceptado en historial."""
        to_remove: List[int] = []
        for idx, m in enumerate(self._pickup_markers):
            if self._game_elapsed >= m.expires_at:
                self.orders.record_offer_result(m.job_id, accepted=False)
                print(f"Pedido expirado (agregado al historial como rechazado), id: {m.job_id}")
                self.reputation -= 5  # penalización por no aceptar
                to_remove.append(idx)
        for i in reversed(to_remove):
            self._pickup_markers.pop(i)

    def _check_proximity(self, player_x: float, player_y: float) -> None:
        ts = self.tile_size
        pgx = int(player_x // ts)
        pgy = int(player_y // ts)

        # Pickups primero (aceptar y crear dropoff)
        to_remove_pickups: List[int] = []
        for idx, m in enumerate(self._pickup_markers):
            mgx = int(m.px // ts)
            mgy = int(m.py // ts)
            dist = abs(mgx - pgx) + abs(mgy - pgy)
            if dist <= self._PICKUP_RADIUS_TILES:
                job = self.jobs.get(m.job_id)
                # Aceptar en inventario
                self.orders.accept_job(job.id)
                print(f"Pedido aceptado (agregado al inventario), id: {job.id}")
                # Crear dropoff marker con due_at relativo
                dx, dy = job.dropoff
                qx, qy = self._grid_center_to_px(dx, dy)
                due_at = self._game_elapsed + self._DROPOFF_LATE_AFTER
                self._dropoff_markers.append(DropoffMarker(qx, qy, job.id, due_at))
                to_remove_pickups.append(idx)

        for i in reversed(to_remove_pickups):
            self._pickup_markers.pop(i)

        # Dropoffs (entregar y setear onTime por due_at), solo el current
        currentJob = self.orders.getCurrentJob()
        idx, m = next(((i, d) for i, d in enumerate(self._dropoff_markers) if d.job_id == (currentJob.id if currentJob else None)), (None, None))
        if idx is None or m is None:
            return
        
        to_remove_dropoffs: List[int] = []
        mgx = int(m.px // ts)
        mgy = int(m.py // ts)
        dist = abs(mgx - pgx) + abs(mgy - pgy)
        if dist <= self._DROPOFF_RADIUS_TILES:
            on_time = self._game_elapsed <= m.due_at
            self.orders.mark_delivered(m.job_id, delivered_on_time=on_time)
            print(f"Pedido entregado (removido del inventario y agregado al historial), id: {m.job_id}, onTime={on_time}")
            if on_time:
                self.reputation += 10  # recompensa por entrega a tiempo
                if self.reputation > 100:
                    self.reputation = 100
            else:
                self.reputation -= 10   # penalización por entrega tarde
            to_remove_dropoffs.append(idx)

        for i in reversed(to_remove_dropoffs):
            self._dropoff_markers.pop(i)
