# ==========================================
# test_logic_9_1.py — ชุดทดสอบตรรกะวงแหวนเล็ก (ข้อ 9.1)
# ==========================================
import bisect
from hash_ring import HashRing, VirtualNode


class ManualHashRing(HashRing):
    """
    คลาสจำลองที่สืบทอดจาก HashRing
    เพิ่มฟังก์ชันปักตำแหน่งอาคารและค้นหาตำแหน่งแขกโดยตรงสำหรับการทดสอบข้อ 9.1
    """
    def add_manual_node(self, node_id: str, pos: int):
        """กำหนดตำแหน่งอาคารบนวงแหวนด้วยตัวเองโดยไม่ผ่าน SHA-256"""
        vnode = VirtualNode(pos=pos, node_id=node_id, j=0)
        bisect.insort(self.nodes, vnode, key=lambda v: (v.pos, v.node_id, v.j))
        self.buildings.add(node_id)

    def get_building_by_position(self, guest_pos: int) -> str:
        """ค้นหาอาคารจากตำแหน่งของแขกโดยตรง (กฎ >= และวนกลับต้นวงแหวน)"""
        if not self.nodes:
            raise ValueError("ไม่มีอาคารในระบบ")

        # หาจุดแรกที่มีตำแหน่ง >= guest_pos
        idx = bisect.bisect_left(
            self.nodes,
            (guest_pos, "", -1),
            key=lambda v: (v.pos, v.node_id, v.j)
        )

        # หากเกินจุดสุดท้าย ให้วนกลับไปจุดแรกสุดของวงแหวน (Index 0)
        if idx == len(self.nodes):
            idx = 0

        return self.nodes[idx].node_id


def run_test_9_1():
    print("=" * 70)
    print("เริ่มต้นการทดสอบตรรกะวงแหวนเล็ก ข้อ 9.1 (Ring Size = 100, V = 1)")
    print("=" * 70 + "\n")

    guest_positions = [10, 20, 25, 35, 50, 70, 90]

    # ----------------------------------------------------
    # Case 1: สถานะเริ่มต้น (วาง A ที่ 20, B ที่ 50, C ที่ 80)
    # ----------------------------------------------------
    ring_init = ManualHashRing(V=1)
    ring_init.add_manual_node("A", 20)
    ring_init.add_manual_node("B", 50)
    ring_init.add_manual_node("C", 80)
    res_init = [ring_init.get_building_by_position(pos) for pos in guest_positions]

    # ----------------------------------------------------
    # Case 2: เพิ่ม D ที่ตำแหน่ง 35
    # ----------------------------------------------------
    ring_add_d = ManualHashRing(V=1)
    ring_add_d.add_manual_node("A", 20)
    ring_add_d.add_manual_node("B", 50)
    ring_add_d.add_manual_node("C", 80)
    ring_add_d.add_manual_node("D", 35)
    res_add_d = [ring_add_d.get_building_by_position(pos) for pos in guest_positions]

    # ----------------------------------------------------
    # Case 3: ลบ B ออกจากสถานะเริ่มต้น
    # ----------------------------------------------------
    ring_rem_b = ManualHashRing(V=1)
    ring_rem_b.add_manual_node("A", 20)
    ring_rem_b.add_manual_node("C", 80)
    res_rem_b = [ring_rem_b.get_building_by_position(pos) for pos in guest_positions]

    # ----------------------------------------------------
    # แสดงผลตารางเปรียบเทียบ
    # ----------------------------------------------------
    print(f"{'ตำแหน่งแฮชแขก':^15} | {'เริ่มต้น A B C':^15} | {'เพิ่ม D ที่ 35':^15} | {'ลบ B จากเริ่มต้น':^15}")
    print("-" * 70)
    for i, pos in enumerate(guest_positions):
        print(f"{pos:^15} | {res_init[i]:^15} | {res_add_d[i]:^15} | {res_rem_b[i]:^15}")
    print("=" * 70)

    # ----------------------------------------------------
    # การตรวจสอบ Assert ตามตารางข้อ 9.1
    # ----------------------------------------------------
    expected_init  = ["A", "A", "B", "B", "B", "C", "A"]
    expected_add_d = ["A", "A", "D", "D", "B", "C", "A"]
    expected_rem_b = ["A", "A", "C", "C", "C", "C", "A"]

    assert res_init == expected_init, f"Case 1 ไม่ตรง: ได้ {res_init}"
    assert res_add_d == expected_add_d, f"Case 2 ไม่ตรง: ได้ {res_add_d}"
    assert res_rem_b == expected_rem_b, f"Case 3 ไม่ตรง: ได้ {res_rem_b}"

    # นับจำนวนคนย้าย
    moved_add_d = sum(1 for i in range(len(guest_positions)) if res_init[i] != res_add_d[i])
    moved_rem_b = sum(1 for i in range(len(guest_positions)) if res_init[i] != res_rem_b[i])

    print(f"\n✔ จำนวนแขกที่ต้องย้ายเมื่อเพิ่ม D : {moved_add_d} คน (คาดหวัง: 2 คน)")
    print(f"✔ จำนวนแขกที่ต้องย้ายเมื่อลบ B  : {moved_rem_b} คน (คาดหวัง: 3 คน)")
    assert moved_add_d == 2
    assert moved_rem_b == 3

    print("\n🎉 ผลการตรวจตรรกะข้อ 9.1: ผ่านถูกต้อง 100%")


if __name__ == "__main__":
    run_test_9_1()