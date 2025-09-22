from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Dict
from .job import Job

@dataclass
class HistoryEntry:
    job_id: str
    accepted: bool
    onTime: bool = False  # se actualizará a True cuando se entregue a tiempo

class OrderManager:
    """
    Estructuras de ejecución (simplificadas):
      1) release_queue: cola (deque) con IDs ordenados por release_time
         - Métodos: fill_release_queue_from_repo(), pop_next_job()
         - Cuando queda vacía, se recarga (repiten los mismos trabajos)
      2) history: lista de HistoryEntry (accepted, onTime, job_id)
      3) inventory: lista de IDs aceptados pero no entregados

    Además:
      - currentJob_id: ID del job activo
      - repo: objeto con get(job_id)->Job y snapshot_ids()->list[str] (JobLoader)
    """

    def __init__(self, repo) -> None:
        self.repo = repo

        # 1) Cola de lanzamiento por release_time (IDs)
        self.release_queue: Deque[str] = deque()
        self._base_ids_sorted: List[str] = []  # respaldo para recargar cuando se vacíe

        # 2) Historial
        self.history: List[HistoryEntry] = []

        # 3) Inventario (IDs aceptados, aún sin entregar)
        self.inventory: List[str] = []

        # Job actual
        self.currentJob_id: Optional[str] = None

    # ---------- (1) Cola por release_time ----------
    def fill_release_queue_from_repo(self) -> None:
        """
        Obtiene todos los jobs del repo, los ordena por release_time ascendente
        y llena la cola. También guarda ese orden base para recargar cuando se vacíe.
        """
        ids = self.repo.snapshot_ids()  # lista de IDs disponibles
        ids.sort(key=lambda jid: self.repo.get(jid).release_time)
        self._base_ids_sorted = ids[:]              # guardamos orden base
        self.release_queue = deque(ids)             # cola inicial

    def _reload_release_queue_if_empty(self) -> None:
        """Si la cola está vacía, recárgala con el orden base (repetición cíclica)."""
        if not self.release_queue and self._base_ids_sorted:
            self.release_queue = deque(self._base_ids_sorted)

    def pop_next_job(self) -> Optional[Job]:
        """
        Saca el primer ID de la cola y retorna el Job completo.
        Si la cola está vacía, se recarga con el orden base y vuelve a intentar.
        """
        if not self.release_queue:
            self._reload_release_queue_if_empty()
        if not self.release_queue:
            return None  # no hay datos

        jid = self.release_queue.popleft()
        # mantener ciclo: el mismo ID volverá a aparecer al recargar
        return self.repo.get(jid)

    # ---------- (2) Historial ----------
    def record_offer_result(self, job_id: str, accepted: bool, onTime=False) -> None:
        self.history.append(HistoryEntry(job_id=job_id, accepted=accepted, onTime=onTime))

    def mark_delivered(self, job_id: str, delivered_on_time: bool) -> bool:
        """
        Marca como entregado: saca del inventario y actualiza onTime en el historial.
        """
        try:
            self.inventory.remove(job_id)
        except ValueError:
            return False

        # Busca en historial la última entrada del mismo job_id que tenga accepted=True
        for entry in reversed(self.history):
            if entry.job_id == job_id and entry.accepted:
                entry.onTime = delivered_on_time
                break

        # Si el entregado era el actual, selecciona otro o None
        if self.currentJob_id == job_id:
            self.currentJob_id = self.inventory[0] if self.inventory else None
        return True

    # ---------- (3) Inventario ----------
    def accept_job(self, job_id: str) -> None:
        """
        Añade un job aceptado al inventario (si no estaba). No valida pesos/capacidad aquí.
        """
        if job_id not in self.inventory:
            self.inventory.append(job_id)
        # Si no hay current, lo selecciona por conveniencia
        if self.currentJob_id is None:
            self.currentJob_id = job_id

    # ---------- Current job ----------
    def set_current_job(self, job_id: Optional[str]) -> bool:
        if job_id is None:
            self.currentJob_id = None
            return True
        if job_id in self.inventory:
            self.currentJob_id = job_id
            return True
        return False

    def current_job(self) -> Optional[Job]:
        return self.repo.get(self.currentJob_id) if self.currentJob_id else None

    # ---------- Helpers de lectura ----------
    def inventory_jobs(self) -> List[Job]:
        return [self.repo.get(jid) for jid in self.inventory]

    def history_summary(self) -> List[Dict]:
        """
        Resumen útil para UI/depuración.
        """
        return [{"id": h.job_id, "accepted": h.accepted, "onTime": h.onTime} for h in self.history]
