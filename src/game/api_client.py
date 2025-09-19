# src/game/api_client.py
# Cliente de API con urllib.request y fallback local a /data
import json
import os
import urllib.request
from urllib.error import URLError, HTTPError
from typing import Any, Dict, List


API_CITY_MAP_URL = (
    "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/map"
)

API_CITY_WEATHER_URL = (
    "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/weather"
)

API_JOBS_URL = (
    "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io/city/jobs"
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
            data = self._fetch_json(API_CITY_MAP_URL)

            # Guardar copia local actualizada
            path = os.path.join(self.base_dir, "data", "ciudad.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return data
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            # Fallback local
            return self._load_local("ciudad")


    def _normalize_jobs(self, data: Any) -> List[Dict[str, Any]]:
      """
      Devuelve SIEMPRE list[dict] con jobs, manejando distintos wrappers.
      """
      # Caso 1: ya es lista de jobs
      if isinstance(data, list):
          return data

      # Caso 2: hay un wrapper dict
      if isinstance(data, dict):
          # Desempaqueta común: muchos endpoints ponen todo bajo "data"
          payload = data.get("data", data)

          # 2a) si 'data' ya es lista -> listo
          if isinstance(payload, list):
              return payload

          # 2b) si 'data' es dict -> busca claves típicas
          if isinstance(payload, dict):
              for key in ("jobs", "pedidos", "orders", "items", "results"):
                  val = payload.get(key)
                  if isinstance(val, list):
                      return val

              # 2c) ¿viene un solo job como dict?
              required = {"id","pickup","dropoff","payout","deadline","weight","priority","release_time"}
              if required.issubset(set(payload.keys())):
                  return [payload]

          # 2d) también intentamos en el dict de primer nivel por si no estaba en 'data'
          for key in ("jobs", "pedidos", "orders", "items", "results"):
              val = data.get(key)
              if isinstance(val, list):
                  return val

          # 2e) ¿un solo job en el nivel raíz?
          required = {"id","pickup","dropoff","payout","deadline","weight","priority","release_time"}
          if required.issubset(set(data.keys())):
              return [data]

          # Si llegamos aquí, no reconocimos el esquema
          d_type = type(payload).__name__
          d_keys = list(payload.keys())[:10] if isinstance(payload, dict) else None
          raise ValueError(f"Payload de jobs no reconocido: data['data'] tipo={d_type}, keys={d_keys}")

      # Cualquier otro tipo: error
      raise ValueError(f"Payload de jobs no reconocido: tipo={type(data)}")

    """
    Cache local: guardamos /data/pedidos.json tal cual lo devuelve el API (sin normalizar) para paridad y depuración.
    Solo normalizamos al usar como fallback (si falla el API), convirtiendo a list[dict] para consumo uniforme.
    Resultado: el cache refleja el API real; get_jobs() siempre retorna una lista normalizada.
    """
    def get_jobs(self) -> List[Dict[str, Any]]:
        try:
            data = self._fetch_json(API_JOBS_URL)
            jobs = self._normalize_jobs(data)              # ← siempre list[dict]

            # Guardar copia local actualizada
            path = os.path.join(self.base_dir, "data", "pedidos.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return jobs
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
          local_raw = self._load_local("pedidos")
          return self._normalize_jobs(local_raw)
    


    def get_weather(self) -> dict:

        try:
            data = self._fetch_json(API_CITY_WEATHER_URL)

            # Guardar copia local actualizada
            path = os.path.join(self.base_dir, "data", "weather.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return data
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            # Fallback local
            return self._load_local("weather")



        #return self._load_local("weather")
    
    def get_map_local(self) -> dict:
        return self._load_local("ciudad")
        