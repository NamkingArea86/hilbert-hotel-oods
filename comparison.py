import time
import tracemalloc
import csv
import numpy as np
from common import hash_to_64bit
from hotel_system import HotelSystem
from data_generator import (
    generate_guests,
    TABLE_A_K, TABLE_A_N, TABLE_A_V,
    TABLE_B_N, TABLE_B_K, TABLE_B_V,
    TABLE_C_V, TABLE_C_N, TABLE_C_K,
    SALT_LIST
)

def hash_mod_N(c: int, s: int, node_list: list, salt: str = "") -> str:
    text = f"guest:{c}:{s}"
    pos = hash_to_64bit(text, salt=salt)
    idx = pos % len(node_list)
    return node_list[idx]

def run_mod_n_benchmark(guests, initial_nodes, salt):
    # 1. วัดเวลา
    t0 = time.perf_counter()
    mod_assign = {g: hash_mod_N(g[0], g[1], initial_nodes, salt) for g in guests}
    t_assign = time.perf_counter() - t0

    # ค้นหา 1,000 ครั้ง
    t0 = time.perf_counter()
    sample_guests = guests[:1000] if len(guests) >= 1000 else guests
    for g in sample_guests:
        _ = mod_assign.get(g)
    t_search_avg = (time.perf_counter() - t0) / len(sample_guests) if sample_guests else 0

    # เพิ่ม 1 อาคาร จากสถานะเริ่มต้น
    nodes_add = initial_nodes + [f"Building_{len(initial_nodes)+1}"]
    t0 = time.perf_counter()
    add_moved = sum(1 for g in guests if mod_assign[g] != hash_mod_N(g[0], g[1], nodes_add, salt))
    t_add = time.perf_counter() - t0

    # ลบ 1 อาคาร จากสถานะเริ่มต้น
    nodes_remove = initial_nodes[1:]
    t0 = time.perf_counter()
    remove_moved = sum(1 for g in guests if mod_assign[g] != hash_mod_N(g[0], g[1], nodes_remove, salt))
    t_remove = time.perf_counter() - t0

    # 2. วัดหน่วยความจำแยกต่างหาก
    tracemalloc.start()
    m0, p0 = tracemalloc.get_traced_memory()
    mod_assign_mem = {g: hash_mod_N(g[0], g[1], initial_nodes, salt) for g in guests}
    curr_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "assign_time": t_assign,
        "search_time_per_op": t_search_avg,
        "add_time": t_add,
        "add_moved_count": add_moved,
        "add_moved_rate": (add_moved / len(guests) * 100) if guests else 0,
        "remove_time": t_remove,
        "remove_moved_count": remove_moved,
        "remove_moved_rate": (remove_moved / len(guests) * 100) if guests else 0,
        "curr_mem_mib": (curr_mem - m0) / (1024 * 1024),
        "peak_mem_mib": peak_mem / (1024 * 1024)
    }

def run_consistent_hashing_benchmark(guests, initial_nodes, V, salt):
    # 1. วัดเวลา
    t0 = time.perf_counter()
    system = HotelSystem(initial_nodes, V, salt=salt)
    t_ring_init = time.perf_counter() - t0

    t0 = time.perf_counter()
    for c, s in guests:
        system.add_guest(c, s)
    t_assign = time.perf_counter() - t0

    t0 = time.perf_counter()
    sample_guests = guests[:1000] if len(guests) >= 1000 else guests
    for c, s in sample_guests:
        _ = system.lookup_by_guest(c, s)
    t_search_avg = (time.perf_counter() - t0) / len(sample_guests) if sample_guests else 0

    t0 = time.perf_counter()
    _ = system.guest_manager.get_all_occupied_rooms_sorted()
    t_sort = time.perf_counter() - t0

    # เพิ่ม 1 อาคาร
    t0 = time.perf_counter()
    add_rep = system.add_building(f"Building_{len(initial_nodes)+1}")
    t_add = time.perf_counter() - t0

    # สร้างระบบใหม่เพื่อลบ 1 อาคารจากสถานะเริ่มต้น
    sys_remove = HotelSystem(initial_nodes, V, salt=salt)
    for c, s in guests:
        sys_remove.add_guest(c, s)
    t0 = time.perf_counter()
    remove_rep = sys_remove.remove_building(initial_nodes[0])
    t_remove = time.perf_counter() - t0

    load_stats = system.get_load_stats()

    # 2. วัดหน่วยความจำแยกต่างหาก
    tracemalloc.start()
    m0, p0 = tracemalloc.get_traced_memory()
    sys_mem = HotelSystem(initial_nodes, V, salt=salt)
    for c, s in guests:
        sys_mem.add_guest(c, s)
    curr_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "ring_init_time": t_ring_init,
        "assign_time": t_assign,
        "search_time_per_op": t_search_avg,
        "sort_time": t_sort,
        "add_time": t_add,
        "add_moved_count": add_rep.moved_count,
        "add_moved_rate": add_rep.moved_rate_percentage or 0,
        "remove_time": t_remove,
        "remove_moved_count": remove_rep.moved_count,
        "remove_moved_rate": remove_rep.moved_rate_percentage or 0,
        "cv": load_stats["cv"],
        "curr_mem_mib": (curr_mem - m0) / (1024 * 1024),
        "peak_mem_mib": peak_mem / (1024 * 1024)
    }

def run_all_experiments():
    raw_results = []

    print("=== กำลังทดลอง Table A (ขนาดข้อมูล K) ===")
    nodes_a = [f"B_{i+1}" for i in range(TABLE_A_N)]
    for K in TABLE_A_K:
        for salt in SALT_LIST:
            guests = generate_guests(K, salt)
            res_ch = run_consistent_hashing_benchmark(guests, nodes_a, TABLE_A_V, salt)
            res_mod = run_mod_n_benchmark(guests, nodes_a, salt)
            raw_results.append({
                "group": "A", "K": K, "N": TABLE_A_N, "V": TABLE_A_V, "salt": salt,
                "ch_assign_time": res_ch["assign_time"], "mod_assign_time": res_mod["assign_time"],
                "ch_search_time": res_ch["search_time_per_op"], "mod_search_time": res_mod["search_time_per_op"],
                "ch_sort_time": res_ch["sort_time"],
                "ch_add_rate": res_ch["add_moved_rate"], "mod_add_rate": res_mod["add_moved_rate"],
                "ch_peak_mem": res_ch["peak_mem_mib"], "mod_peak_mem": res_mod["peak_mem_mib"],
                "ch_cv": res_ch["cv"]
            })
        print(f"  K={K} เสร็จสมบูรณ์")

    print("=== กำลังทดลอง Table B (จำนวนอาคาร N) ===")
    for N in TABLE_B_N:
        nodes_b = [f"B_{i+1}" for i in range(N)]
        for salt in SALT_LIST:
            guests = generate_guests(TABLE_B_K, salt)
            res_ch = run_consistent_hashing_benchmark(guests, nodes_b, TABLE_B_V, salt)
            res_mod = run_mod_n_benchmark(guests, nodes_b, salt)
            raw_results.append({
                "group": "B", "K": TABLE_B_K, "N": N, "V": TABLE_B_V, "salt": salt,
                "ch_add_rate": res_ch["add_moved_rate"], "mod_add_rate": res_mod["add_moved_rate"],
                "ch_remove_rate": res_ch["remove_moved_rate"], "mod_remove_rate": res_mod["remove_moved_rate"],
                "ch_add_time": res_ch["add_time"], "mod_add_time": res_mod["add_time"],
                "ch_peak_mem": res_ch["peak_mem_mib"], "mod_peak_mem": res_mod["peak_mem_mib"],
                "ch_cv": res_ch["cv"]
            })
        print(f"  N={N} เสร็จสมบูรณ์")

    print("=== กำลังทดลอง Table C ( virtual node V) ===")
    nodes_c = [f"B_{i+1}" for i in range(TABLE_C_N)]
    for V in TABLE_C_V:
        for salt in SALT_LIST:
            guests = generate_guests(TABLE_C_K, salt)
            res_ch = run_consistent_hashing_benchmark(guests, nodes_c, V, salt)
            res_mod = run_mod_n_benchmark(guests, nodes_c, salt)
            raw_results.append({
                "group": "C", "K": TABLE_C_K, "N": TABLE_C_N, "V": V, "salt": salt,
                "ch_cv": res_ch["cv"],
                "ch_curr_mem": res_ch["curr_mem_mib"], "ch_peak_mem": res_ch["peak_mem_mib"],
                "ch_add_rate": res_ch["add_moved_rate"], "mod_add_rate": res_mod["add_moved_rate"]
            })
        print(f"  V={V} เสร็จสมบูรณ์")

    # ส่งออก CSV
    fieldnames = []
    for row in raw_results:
        for k in row.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open("experiment_results.csv", mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raw_results)

    print("✅ บันทึกผลการทดลองทั้งหมดลงไฟล์ experiment_results.csv สำเร็จ")

if __name__ == "__main__":
    run_all_experiments()