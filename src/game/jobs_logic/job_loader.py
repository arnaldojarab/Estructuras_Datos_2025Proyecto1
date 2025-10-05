from __future__ import annotations
from typing import Dict, List, Optional, Callable
from ..api_client import APIClient
from .job import Job
from .job_manager import OrderManager
import os


class JobLoader:
    """
    Jobs + fábrica de OrderManager.
    """
    def __init__(self, api_client: Optional[APIClient] = None) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", ".."))
        self.api = api_client or APIClient(base_dir)
        self._jobs: Dict[str, Job] = {}

    # -------- Fetch + carga ----------
    def load_from_api(self) -> None:
        """
        Llama a APIClient.getJobs() y carga/normaliza los Jobs.
        - Valida cada job (Job.validate()).
        """
        jobs_raw = self.api.get_jobs()  # se espera: list[dict] con la estructura del pedido
        self._jobs.clear()
        for d in jobs_raw:
            job = Job.from_dict(d)
            job.validate()
            self._jobs[job.id] = job  # último gana

    # -------- Fábrica de OrderManager ----------
    def create_order_manager(self) -> OrderManager:
        """
        Devuelve un OrderManager nuevo, construido con un snapshot de los IDs actuales.
        No hace fetch. Usa el catálogo ya cargado.
        """
        om = OrderManager(self)  # self actúa como “repo” (tiene get())
        om.fill_release_queue_from_repo()
        return om

    def resetJobs(self) -> OrderManager:
        """
        Re-fetchea los datos (getJobs()), recarga el catálogo y devuelve
        un OrderManager NUEVO con esa instantánea.
        """
        self.load_from_api()
        return self.create_order_manager()

    # -------- Lecturas tipo “repo” (para OrderManager/UI) ----------
    def get(self, job_id: str) -> Job:
        return self._jobs[job_id]

    def exists(self, job_id: str) -> bool:
        return job_id in self._jobs

    def all_ids(self) -> List[str]:
        return list(self._jobs.keys())

    def snapshot_ids(self) -> List[str]:
        return list(self._jobs.keys())

    def size(self) -> int:
        return len(self._jobs)

    def filter_ids(self, predicate: Callable[[Job], bool]) -> List[str]:
        return [jid for jid, job in self._jobs.items() if predicate(job)]
