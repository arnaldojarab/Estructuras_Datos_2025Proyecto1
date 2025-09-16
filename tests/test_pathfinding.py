from src.game.pathfinding import astar

def test_astar_shape():
    path = astar((0,0), (1,1), {})
    assert path[0] == (0,0)
    assert path[-1] == (1,1)
