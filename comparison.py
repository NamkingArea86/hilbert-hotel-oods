# ==================================================
# comparison.py — เปรียบเทียบ Consistent Hashing vs Hash Mod N
# ==================================================

import time
import tracemalloc
import numpy as np
import csv
from pathlib import Path

# ===== นำเข้าจากส่วนกลาง =====
from common import hash_to_64bit

# จะนำเข้าจากเพื่อนเมื่อพร้อม
# from hotel_system import HotelSystem

# ==================================================
# 1. ฟังก์ชันสร้างข้อมูลทดลอง
# ==================================================
def generate_guests(K: int, salt: int = 0):
    """
    สร้างรายการคู่ (c, s) จำนวน K ชุด
    salt เปลี่ยนค่า = ชุดข้อมูลใหม่ ไม่ซ้ำเดิม
    """
    rng = np.random.default_rng(seed=salt)
    guests = []
    for _ in range(K):
        c = int(rng.integers(1, 1_000_000))
        s = int(rng.integers(1, 1_000_000))
        guests.append((c, s))
    return guests


# ==================================================
# 2. วิธีที่ 2: Hash Mod N (เขียนเสร็จแล้ว ไม่ต้องรอใคร)
# ==================================================
def hash_mod_N(c: int, s: int, node_list: list[str]) -> str:
    """
    คำนวณหาอาคารด้วยวิธี hash % N
    node_list = รายชื่ออาคาร เรียงลำดับคงที่
    """
    text = f"guest:{c}:{s}"
    pos = hash_to_64bit(text)
    idx = pos % len(node_list)
    return node_list[idx]


# ==================================================
# 3. รันทดลอง Consistent Hashing (รอเชื่อมต่อกับ HotelSystem)
# ==================================================
def run_consistent_hashing(guests, initial_nodes, virtual_per_node):
    """
    ทดสอบระบบ Consistent Hashing
    วัดเวลา, หน่วยความจำ, อัตราการย้ายแขก
    """
    # TODO: นำเข้า HotelSystem จากคนที่ 1-3
    # system = HotelSystem(initial_nodes, virtual_per_node)
    
    # === ชั่วคราว ===
    print(f"[Consistent] K={len(guests)}, N={len(initial_nodes)}, V={virtual_per_node} — รอเชื่อม HotelSystem")
    
    return {
        "time_sec": None,
        "peak_mem_MiB": None,
        "add_moved_count": None,
        "add_moved_rate": None,
        "remove_moved_count": None,
        "remove_moved_rate": None,
        "load_stats": None
    }


# ==================================================
# 4. รันทดลอง Hash Mod N (ทำเสร็จแล้ว)
# ==================================================
def run_hash_mod_N(guests, initial_nodes):
    """
    ทดสอบวิธีเปรียบเทียบ: hash % N
    """
    tracemalloc.start()
    t_start = time.perf_counter()

    # 1. ก่อนเปลี่ยนจำนวนอาคาร
    assign_initial = {}
    for c, s in guests:
        assign_initial[(c, s)] = hash_mod_N(c, s, initial_nodes)

    # 2. เพิ่มอาคาร 1 หลัง
    nodes_add = initial_nodes + [f"Building_{len(initial_nodes)+1}"]
    moved_add = 0
    for c, s in guests:
        old = assign_initial[(c, s)]
        new = hash_mod_N(c, s, nodes_add)
        if old != new:
            moved_add += 1

    # 3. ลบอาคารหลังแรก
    nodes_remove = initial_nodes[1:]
    moved_remove = 0
    for c, s in guests:
        old = assign_initial[(c, s)]
        new = hash_mod_N(c, s, nodes_remove)
        if old != new:
            moved_remove += 1

    t_end = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "time_sec": t_end - t_start,
        "peak_mem_MiB": peak_mem / (1024 * 1024),
        "add_moved_count": moved_add,
        "add_moved_rate": moved_add / len(guests) if guests else 0,
        "remove_moved_count": moved_remove,
        "remove_moved_rate": moved_remove / len(guests) if guests else 0
    }


# ==================================================
# 5. คำนวณค่าสถิติ
# ==================================================
def median(values):
    """ค่ามัธยฐาน — ใช้แทนค่าเฉลี่ยเพื่อลดความผันแปร"""
    return round(np.median(values), 6)


# ==================================================
# 6. ชุดทดลองหลัก — ตาราง A / B / C
# ==================================================
def run_all_experiments():
    """
    ตาราง A: เปลี่ยน K (จำนวนแขก)
    ตาราง B: เปลี่ยน N (จำนวนอาคาร)
    ตาราง C: เปลี่ยน V (จำนวน Virtual Node)
    """
    # ===== ค่าคงที่ทดลอง =====
    TABLE_A_K = [1_000, 10_000, 100_000]
    TABLE_B_N = [4, 8, 16, 32]
    TABLE_C_V = [1, 8, 32]
    SALT_LIST = [0, 1, 2]  # ทดลองซ้ำ 3 รอบ

    results = []

    # ===== ตาราง A =====
    print("=== กำลังทดลอง: ตาราง A ===")
    N_fixed = 8
    V_fixed = 8
    nodes_A = [f"B{i+1}" for i in range(N_fixed)]

    for K in TABLE_A_K:
        cons_time = []
        cons_rate = []
        mod_time = []
        mod_rate = []

        for salt in SALT_LIST:
            guests = generate_guests(K, salt)
            r_mod = run_hash_mod_N(guests, nodes_A)
            r_cons = run_consistent_hashing(guests, nodes_A, V_fixed)

            mod_time.append(r_mod["time_sec"])
            mod_rate.append(r_mod["add_moved_rate"] * 100)

        results.append({
            "group": "A",
            "K": K, "N": N_fixed, "V": V_fixed,
            "cons_time": median(cons_time) if cons_time else "รอ",
            "cons_rate_add": median(cons_rate) if cons_rate else "รอ",
            "mod_time": median(mod_time),
            "mod_rate_add": median(mod_rate)
        })
        print(f"  K={K} ✅")

    # ===== ตาราง B =====
    print("=== กำลังทดลอง: ตาราง B ===")
    K_fixed = 10_000
    V_fixed = 8

    for N in TABLE_B_N:
        nodes_B = [f"B{i+1}" for i in range(N)]
        mod_add = []
        mod_remove = []

        for salt in SALT_LIST:
            guests = generate_guests(K_fixed, salt)
            r_mod = run_hash_mod_N(guests, nodes_B)
            mod_add.append(r_mod["add_moved_rate"] * 100)
            mod_remove.append(r_mod["remove_moved_rate"] * 100)

        results.append({
            "group": "B",
            "K": K_fixed, "N": N, "V": V_fixed,
            "cons_rate_add": "รอ",
            "cons_rate_remove": "รอ",
            "mod_rate_add": median(mod_add),
            "mod_rate_remove": median(mod_remove)
        })
        print(f"  N={N} ✅")

    # ===== ตาราง C =====
    print("=== กำลังทดลอง: ตาราง C ===")
    K_fixed = 10_000
    N_fixed = 8
    nodes_C = [f"B{i+1}" for i in range(N_fixed)]

    for V in TABLE_C_V:
        results.append({
            "group": "C",
            "K": K_fixed, "N": N_fixed, "V": V,
            "cv": "รอ",
            "mem_MiB": "รอ"
        })
        print(f"  V={V} ✅")

    # ===== บันทึกผล =====
    with open("experiment_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print("\n✅ บันทึกผลที่ experiment_results.csv")
    return results


# ==================================================
# 7. จุดเริ่มต้นรัน
# ==================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  โครงงาน Distributed Hilbert Hotel")
    print("  เปรียบเทียบ Consistent Hashing vs Hash Mod N")
    print("=" * 50)
    print()

    run_all_experiments()

    print("\n📝 หมายเหตุ: ส่วน Consistent Hashing แสดง 'รอ' จนกว่าจะนำเข้า HotelSystem ได้")
    print("   ส่วน Hash Mod N ทำงานสมบูรณ์แล้ว ✅")