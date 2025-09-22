from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timezone

@dataclass(slots=True)
class Job:
    id: str
    pickup: Tuple[int, int]          # (x, y)
    dropoff: Tuple[int, int]         # (x, y)
    payout: float
    deadline: datetime               # naive (UTC-normalized) para cálculos simples
    weight: float
    priority: int                    # 0 = normal; mayor => más urgente
    release_time: int                # segundos desde t=0 del juego

    # ---------- Constructores ----------
    @staticmethod
    def _parse_deadline(value: str) -> datetime:
        """
        Admite ISO 8601: 'YYYY-MM-DDTHH:MM:SS' opcionalmente con 'Z' o '+/-HH:MM'.
        Normaliza a UTC y retorna naive (tzinfo=None) para facilitar comparaciones.
        """
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Job":
        return cls(
            id=d["id"],
            pickup=tuple(d["pickup"]),
            dropoff=tuple(d["dropoff"]),
            payout=float(d["payout"]),
            deadline=cls._parse_deadline(d["deadline"]),
            weight=float(d["weight"]),
            priority=int(d["priority"]),
            release_time=int(d["release_time"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pickup": list(self.pickup),
            "dropoff": list(self.dropoff),
            "payout": self.payout,
            "deadline": self.deadline.strftime("%Y-%m-%dT%H:%M:%S"),
            "weight": self.weight,
            "priority": self.priority,
            "release_time": self.release_time,
        }

    # ---------- Checks ----------
    def is_released(self, game_seconds: float) -> bool:
        """¿Ya puede aparecer según release_time?"""
        return game_seconds >= self.release_time

    def is_overdue(self, now_dt: datetime) -> bool:
        """¿Se pasó el deadline (now_dt naive UTC-normalized)?"""
        return now_dt > self.deadline

    def seconds_to_deadline(self, now_dt: datetime) -> float:
        """Segundos hasta el deadline (negativo si ya venció)."""
        return (self.deadline - now_dt).total_seconds()

    # ---------- Utilidades/heurísticas ----------
    @staticmethod
    def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def approx_distance_route(self, player_pos: Tuple[int, int]) -> int:
        """Distancia Manhattan: jugador -> pickup -> dropoff."""
        return self.manhattan(player_pos, self.pickup) + self.manhattan(self.pickup, self.dropoff)

    def value_ratio(self, player_pos: Tuple[int, int]) -> float:
        """Heurística: payout / distancia estimada (mayor es mejor)."""
        d = max(1, self.approx_distance_route(player_pos))
        return self.payout / d

    # ---------- Claves para ordenar/heap ----------
    def key_priority_then_deadline(self) -> tuple:
        """Para seleccionar ofertas: prioridad DESC, luego deadline ASC."""
        return (-self.priority, self.deadline)

    def key_deadline(self) -> tuple:
        """Para vistas por urgencia temporal: deadline ASC; empates por prioridad/payout."""
        return (self.deadline, -self.priority, -self.payout)

    # ---------- Validación mínima ----------
    def validate(self) -> None:
        assert isinstance(self.pickup, tuple) and len(self.pickup) == 2
        assert isinstance(self.dropoff, tuple) and len(self.dropoff) == 2
        assert self.payout >= 0
        assert self.weight >= 0
