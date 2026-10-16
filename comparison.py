# ==================================================
# comparison.py — เปรียบเทียบ Consistent Hashing vs Hash Mod N
# ==================================================

import time
import tracemalloc
import numpy as np
import csv
from pathlib import Path

from data_generator import generate_guests, TABLE_A_K, TABLE_B_N, TABLE_C_V, SALT_LIST

from common import hash_to_64bit

from hotel_system import HotelSystem

# ==================================================
# Hash Mod N 
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
# รันทดลอง Consistent Hashing (รอเชื่อมต่อกับ HotelSystem)
# ==================================================
def run_consistent_hashing(guests, initial_nodes, virtual_per_node):
    """
    ทดสอบระบบ Consistent Hashing โดยใช้ HotelSystem จริง
    """
    tracemalloc.start()
    t_start = time.perf_counter()

    # 1. สร้างระบบ
    system = HotelSystem(initial_nodes, virtual_per_node)
    
    # 2. เพิ่มแขกทั้งหมด — ข้ามรายการที่ซ้ำ
    for c, s in guests:
        if (c, s) not in system.guest_manager.guests:
            first_node = system.hash_ring.get_building_for_guest(c, s)
            system.guest_manager.add_guest(c, s, first_node)

    # 3. เพิ่มอาคารใหม่
    new_node = f"Building_{len(initial_nodes)+1}"
    add_report = system.add_building(new_node)

    # 4. ลบอาคารแรก
    remove_node = initial_nodes[0]
    remove_report = system.remove_building(remove_node)

    t_end = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 5. คำนวณสถิติความสมดุล
    count = {}
    for g in system.guest_manager.guests.values():
        count[g.node_id] = count.get(g.node_id, 0) + 1
    vals = list(count.values()) or [0]
    mean = sum(vals) / len(vals)
    var = sum((x - mean)**2 for x in vals) / len(vals)
    cv = (var**0.5 / mean) if mean > 0 else 0

    return {
        "time_sec": t_end - t_start,
        "peak_mem_MiB": peak_mem / (1024 * 1024),
        "add_moved_count": add_report.moved_count,
        "add_moved_rate": (add_report.moved_rate_percentage or 0) / 100,
        "remove_moved_count": remove_report.moved_count,
        "remove_moved_rate": (remove_report.moved_rate_percentage or 0) / 100,
        "load_stats": {
            "mean": round(mean, 2),
            "std": round(var**0.5, 2),
            "cv": round(cv, 4)
        }
    }


# ==================================================
# รันทดลอง Hash Mod N 
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
# คำนวณค่าสถิติ
# ==================================================
def median(values):
    """ค่ามัธยฐาน — ใช้แทนค่าเฉลี่ยเพื่อลดความผันแปร"""
    return round(np.median(values), 6)


# ==================================================
# ชุดทดลองหลัก — ตาราง A / B / C
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
            cons_time.append(r_cons["time_sec"])
            cons_rate.append(r_cons["add_moved_rate"] * 100) 

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
        cons_add = []
        cons_remove = []

        for salt in SALT_LIST:
            guests = generate_guests(K_fixed, salt)
            r_mod = run_hash_mod_N(guests, nodes_B)
            r_cons = run_consistent_hashing(guests, nodes_B, V_fixed) 
            mod_add.append(r_mod["add_moved_rate"] * 100)
            mod_remove.append(r_mod["remove_moved_rate"] * 100)
            cons_add.append(r_cons["add_moved_rate"] * 100)     
            cons_remove.append(r_cons["remove_moved_rate"] * 100) 

        results.append({
            "group": "B",
            "K": K_fixed, "N": N, "V": V_fixed,
            "cons_rate_add": median(cons_add),
            "cons_rate_remove": median(cons_remove),
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
        cons_cv = []
        cons_mem = []
        for salt in SALT_LIST:
            guests = generate_guests(K_fixed, salt)
            r_cons = run_consistent_hashing(guests, nodes_C, V)  # ✅ เรียก
            cons_cv.append(r_cons["load_stats"]["cv"])
            cons_mem.append(r_cons["peak_mem_MiB"])

        results.append({
            "group": "C",
            "K": K_fixed, "N": N_fixed, "V": V,
            "cv": median(cons_cv),
            "mem_MiB": median(cons_mem)
        })
        print(f"  V={V} ✅")

    # ===== บันทึกผล =====
    fieldnames = [
        "group", "K", "N", "V",
        "cons_time", "cons_rate_add", "cons_rate_remove",
        "mod_time", "mod_rate_add", "mod_rate_remove",
        "cv", "mem_MiB"
    ]
    with open("experiment_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\n✅ บันทึกผลที่ experiment_results.csv")
    return results


# ==================================================
# จุดเริ่มต้นรัน
# ==================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  โครงงาน Distributed Hilbert Hotel")
    print("  เปรียบเทียบ Consistent Hashing vs Hash Mod N")
    print("=" * 50)
    print()

    run_all_experiments()