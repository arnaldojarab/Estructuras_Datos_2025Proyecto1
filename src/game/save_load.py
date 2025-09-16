# Placeholder save/load/undo
import os, gzip, pickle

def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wb") as f:
        pickle.dump(state, f)

def load_state(path):
    with gzip.open(path, "rb") as f:
        return pickle.load(f)
