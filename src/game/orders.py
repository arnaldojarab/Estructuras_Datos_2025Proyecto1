from dataclasses import dataclass

@dataclass
class Order:
    id: str
    pickup: tuple
    dropoff: tuple
    payout: float
    deadline: int
    weight: int
    priority: int
    release_time: int
