# src/game/api_client.py
# Cliente de API con urllib.request y fallback local a /data
import json
import os
import urllib.request
from urllib.error import URLError, HTTPError


API_CITY_MAP_URL = (
    "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/map"
)


class APIClient:
    def __init__(self, base_dir: str):
        """
        base_dir: ruta absoluta a la carpeta raíz del proyecto (la que contiene /data)
        """
        self.base_dir = base_dir

    def _fetch_json(self, url: str, timeout: float = 8.0) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "CourierQuest/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Carga directo como dict (igual que tu ejemplo)
            return json.load(response)

    def _load_local(self, name: str) -> dict:
        """
        Fallback local: intenta leer /data/<name>.json
        """
        path = os.path.join(self.base_dir, "data", f"{name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_map(self) -> dict:
        """
        Devuelve el mapa como dict. Primero intenta API; si falla, usa data/ciudad.json
        Estructura esperada (nuevo formato):
        {
          "version": "...",
          "data": {
            "version": "...",
            "city_name": "...",
            "width": int,
            "height": int,
            "goal": float,
            "max_time": int,
            "tiles": [[str, ...], ...],
            "legend": { "C": {...}, "B": {...}, "P": {...} }
          }
        }
        """
        try:
            return self._fetch_json(API_CITY_MAP_URL)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            # Fallback local
            return self._load_local("ciudad")

    # Placeholders por si luego agregas más endpoints:
    def get_jobs(self) -> dict:
        return self._load_local("pedidos")

    def get_weather(self) -> dict:
        return self._load_local("weather")