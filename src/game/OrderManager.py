# src/game/orders.py
from __future__ import annotations
import heapq
from typing import List, Tuple, Optional, Iterable, Literal, Set

OrderKey = Literal["deadline", "priority"]

class OrderManager:
    """
    Estructuras de ejecución para una partida (solo IDs).
    - upcoming_by_release: min-heap (release_time, seq, id)
    - offers_now:          min-heap (key,          seq, id) donde key = (-priority, deadline)
    - inventory:           lista de IDs aceptados
    - history:             lista de IDs entregados
    - current_id:          ID del job activo (opcional)

    'repo' debe exponer: get(job_id) -> Job
    (JobLoader cumple este contrato).
    """

    def __init__(self, repo) -> None:  # repo: objeto con get(job_id)->Job
        self.repo = repo

        # Heaps / índices
        self._upcoming_by_release: List[Tuple[int, int, str]] = []
        self._offers_now: List[Tuple[Tuple, int, str]] = []
        self._offers_set: Set[str] = set()

        # Contenedores del jugador
        self._inventory: List[str] = []
        self._history: List[str] = []
        self._current_id: Optional[str] = None

        # Secuencias para desempates estables
        self._seq_upcoming = 0
        self._seq_offers = 0

        # Invalidaciones perezosas para el heap de ofertas
        self._invalid_offers: Set[str] = set()

    # ---------- construcción / reset ----------
    def build_upcoming(self, ids: Iterable[str]) -> None:
        """Inicializa todos los índices para una nueva partida."""
        self._upcoming_by_release.clear()
        self._offers_now.clear()
        self._offers_set.clear()
        self._invalid_offers.clear()
        self._inventory.clear()
        self._history.clear()
        self._current_id = None
        self._seq_upcoming = 0
        self._seq_offers = 0

        for jid in ids:
            job = self.repo.get(jid)
            heapq.heappush(
                self._upcoming_by_release,
                (int(job.release_time), self._seq_upcoming, jid),
            )
            self._seq_upcoming += 1

    # ---------- ciclo ----------
    def tick(self, game_seconds: float) -> None:
        """
        Mueve jobs de upcoming -> offers_now cuando now >= release_time.
        No decide cuándo abrir pop-ups; solo expone ofertas disponibles.
        """
        while self._upcoming_by_release and self._upcoming_by_release[0][0] <= game_seconds:
            _, _, jid = heapq.heappop(self._upcoming_by_release)
            self._push_offer(jid)

        self._purge_offers_top()

    # ---------- ofertas ----------
    def has_offer(self) -> bool:
        self._purge_offers_top()
        return bool(self._offers_now)

    def peek_offer_id(self) -> Optional[str]:
        self._purge_offers_top()
        return self._offers_now[0][2] if self._offers_now else None

    def pop_offer_id(self) -> Optional[str]:
        self._purge_offers_top()
        if not self._offers_now:
            return None
        _, _, jid = heapq.heappop(self._offers_now)
        self._offers_set.discard(jid)
        return jid

    def accept(self, job_id: str) -> bool:
        """Acepta oferta → inventario."""
        if job_id not in self._offers_set:
            return False
        self._invalid_offers.add(job_id)
        self._offers_set.discard(job_id)
        self._purge_offers_top()

        self._inventory.append(job_id)
        if self._current_id is None:
            self._current_id = job_id
        return True

    def reject(self, job_id: str) -> bool:
        """Rechaza/descarta oferta."""
        if job_id not in self._offers_set:
            return False
        self._invalid_offers.add(job_id)
        self._offers_set.discard(job_id)
        self._purge_offers_top()
        return True

    # ---------- inventario ----------
    def current(self) -> Optional[str]:
        return self._current_id

    def set_current(self, job_id: Optional[str]) -> bool:
        if job_id is None:
            self._current_id = None
            return True
        if job_id in self._inventory:
            self._current_id = job_id
            return True
        return False

    def inventory_ids(self) -> List[str]:
        return list(self._inventory)

    def inventory_view(self, order_by: OrderKey = "deadline") -> List[str]:
        """
        Devuelve una VISTA ordenada (lista nueva) de los IDs del inventario.
        No altera el orden base elegido por el jugador.
        """
        if not self._inventory:
            return []
        if order_by == "deadline":
            return sorted(self._inventory, key=lambda jid: self.repo.get(jid).key_deadline())
        if order_by == "priority":
            return sorted(self._inventory, key=lambda jid: self.repo.get(jid).key_priority_then_deadline())
        return list(self._inventory)

    def mark_delivered(self, job_id: str) -> bool:
        """Mueve del inventario al historial (tras entregar)."""
        try:
            self._inventory.remove(job_id)
        except ValueError:
            return False
        self._history.append(job_id)
        if self._current_id == job_id:
            self._current_id = self._inventory[0] if self._inventory else None
        return True

    # ---------- historial ----------
    def history_ids(self) -> List[str]:
        return list(self._history)

    # ---------- internos ----------
    def _push_offer(self, job_id: str) -> None:
        """Inserta una oferta con clave (-priority, deadline) para min-heap."""
        job = self.repo.get(job_id)
        key = job.key_priority_then_deadline()  # (-priority, deadline)
        heapq.heappush(self._offers_now, (key, self._seq_offers, job_id))
        self._offers_set.add(job_id)
        self._seq_offers += 1

    def _purge_offers_top(self) -> None:
        """Purgado perezoso de ofertas inválidas en el tope."""
        while self._offers_now and self._offers_now[0][2] in self._invalid_offers:
            _, _, jid = heapq.heappop(self._offers_now)
            self._invalid_offers.discard(jid)
