from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
import pygame
import os
from collections import deque
from dataclasses import asdict

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

    def _select_Image(self, type):
        assets_dir = os.path.join(os.path.dirname(__file__), "..","..", "assets", "images")

        if type == 0:
            return pygame.image.load(os.path.join(assets_dir, "icon_0.png")).convert_alpha()
        elif type == 1:
            return pygame.image.load(os.path.join(assets_dir, "icon_1.png")).convert_alpha()


    def draw(self, screen: pygame.Surface) -> None:

        dropoff_icon = self._select_Image(0)  
        pickup_icon = self._select_Image(1) 

        # Pickups
        for m in self._pickup_markers:
            rect = pickup_icon.get_rect(center=(m.px, m.py))
            screen.blit(pickup_icon, rect)

        # Dropoffs (solamente el current)
        currentJob = self.orders.getCurrentJob()
        if currentJob:
            m = next((d for d in self._dropoff_markers if d.job_id == currentJob.id), None)
            rect = dropoff_icon.get_rect(center=(m.px, m.py))
            screen.blit(dropoff_icon, rect)
            
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

    def setCurrentJob(self, job_id: str) -> None:
        """Establece el job actual en inventario (si existe)."""
        self.orders.set_current_job(job_id)
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
                if self.reputation < 0:
                    self.reputation = 0
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
                # Aceptar en inventario}

                if(self.getWeight() < 5):
                    self.orders.accept_job(job.id)
                    print(f"Pedido aceptado (agregado al inventario), id: {job.id}")
                    # Crear dropoff marker con due_at relativo
                    dx, dy = job.dropoff
                    qx, qy = self._grid_center_to_px(dx, dy)
                    due_at = self._game_elapsed + self._DROPOFF_LATE_AFTER
                    self._dropoff_markers.append(DropoffMarker(qx, qy, job.id, due_at))
                    to_remove_pickups.append(idx)
                else:
                    print("Peso maximo alcanzado")

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
                if self.reputation < 0:
                    self.reputation = 0
            to_remove_dropoffs.append(idx)

        for i in reversed(to_remove_dropoffs):
            self._dropoff_markers.pop(i)


    def getRepSpeed(self):
        if self.reputation >= 90:
            return 1.03
        return 1.0
    def save_state(self) -> dict:
        """
        Serializa todo el estado mutable de JobLogic + JobLoader + OrderManager
        en un único diccionario.
        """
        # 1) Jobs (catálogo maestro)
        jobs_list = [job.to_dict() for job in self.jobs._jobs.values()]

        # 2) OrderManager
        orders_state = {
            "inventory": list(self.orders.inventory),  # [job_id]
            "history": [
                {"job_id": h.job_id, "accepted": h.accepted, "onTime": h.onTime}
                for h in self.orders.history
            ],
            "currentJob_id": self.orders.currentJob_id,
            "release_queue": list(self.orders.release_queue),        # [job_id] en orden
            "base_ids_sorted": list(self.orders._base_ids_sorted),  # respaldo para recarga cíclica
        }

        # 3) Markers
        markers_state = {
            "pickups": [asdict(m) for m in self._pickup_markers],     # [{px,py,job_id,expires_at}]
            "dropoffs": [asdict(m) for m in self._dropoff_markers],   # [{px,py,job_id,due_at}]
        }

        # 4) Timers/estado de gameplay (solo los necesarios)
        logic_state = {
            "game_elapsed": self._game_elapsed,
            "job_offer_elapsed": self._job_offer_elapsed,
            "reputation": self.reputation,
        }

        return {
            "jobs": jobs_list,
            "orders": orders_state,
            "markers": markers_state,
            "logic": logic_state,
        }


    def load_state(self, state: dict) -> bool:
        """
        Restaura el estado desde un diccionario generado por save_state().
        No refetchea del API. Devuelve True si tuvo éxito, False si falló.
        """
        try:
            if not isinstance(state, dict):
                return False

            # 1) Jobs -> reconstruir catálogo maestro en JobLoader
            self.jobs._jobs.clear()
            for jd in state.get("jobs", []):
                job = Job.from_dict(jd)
                job.validate()
                self.jobs._jobs[job.id] = job

            # 2) OrderManager limpio con el repo actual y luego aplicar estado
            self.orders = self.jobs.create_order_manager()

            orders_state = state.get("orders", {})
            # Inventario
            self.orders.inventory = list(orders_state.get("inventory", []))
            # Historial
            self.orders.history.clear()
            for h in orders_state.get("history", []):
                self.orders.history.append(
                    HistoryEntry(
                        job_id=h["job_id"],
                        accepted=bool(h["accepted"]),
                        onTime=bool(h["onTime"]),
                    )
                )
            # Current
            self.orders.currentJob_id = orders_state.get("currentJob_id", None)
            # Colas
            self.orders._base_ids_sorted = list(orders_state.get("base_ids_sorted", []))
            self.orders.release_queue = deque(orders_state.get("release_queue", []))

            # 3) Markers -> dataclasses
            self._pickup_markers.clear()
            for m in state.get("markers", {}).get("pickups", []):
                self._pickup_markers.append(
                    PickupMarker(
                        px=int(m["px"]),
                        py=int(m["py"]),
                        job_id=m["job_id"],
                        expires_at=float(m["expires_at"]),
                    )
                )
            self._dropoff_markers.clear()
            for m in state.get("markers", {}).get("dropoffs", []):
                self._dropoff_markers.append(
                    DropoffMarker(
                        px=int(m["px"]),
                        py=int(m["py"]),
                        job_id=m["job_id"],
                        due_at=float(m["due_at"]),
                    )
                )

            # 4) Timers/estado de gameplay: solo los que decidiste persistir
            logic_state = state.get("logic", {})
            self._game_elapsed = float(logic_state.get("game_elapsed", 0.0))
            self._job_offer_elapsed = float(logic_state.get("job_offer_elapsed", 0.0))
            self.reputation = int(logic_state.get("reputation", self.reputation))

            return True
        except Exception:
            return False
