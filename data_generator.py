import numpy as np

def generate_guests(K: int, salt: int = 0):
    rng = np.random.default_rng(seed=salt)
    guests = []
    for _ in range(K):
        c = int(rng.integers(1, 1_000_000))
        s = int(rng.integers(1, 1_000_000))
        guests.append((c, s))
    return guests

TABLE_A_K = [1_000, 10_000, 100_000]
TABLE_B_N = [4, 8, 16, 32]
TABLE_C_V = [1, 8, 32]
SALT_LIST = [0, 1, 2]