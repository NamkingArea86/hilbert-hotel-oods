import numpy as np

TABLE_A_K = [1_000, 10_000, 100_000]
TABLE_A_N = 10
TABLE_A_V = 32

TABLE_B_N = [5, 10, 20]
TABLE_B_K = 10_000
TABLE_B_V = 32

TABLE_C_V = [1, 8, 32]
TABLE_C_N = 10
TABLE_C_K = 10_000

SALT_LIST = ["salt_0", "salt_1", "salt_2"]

def generate_guests(K: int, salt_str: str = "salt_0"):
    """
    สร้างรายการแขก K คน กระจายใน 10 ช่องทาง (c = 1 ถึง 10)
    โดยแต่ละช่องทางมีแขกต่อเนื่องเรียงลำดับ s
    """
    guests = []
    num_channels = 10
    base_per_channel = K // num_channels
    remainder = K % num_channels

    for c in range(1, num_channels + 1):
        count = base_per_channel + (1 if c <= remainder else 0)
        for s in range(1, count + 1):
            guests.append((c, s))

    return guests