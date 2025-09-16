from src.game.api_client import APIClient
import os

def test_local_fallback():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cli = APIClient(base_dir)
    m = cli.get_map()
    assert "width" in m and "height" in m
