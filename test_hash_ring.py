import unittest
import os
import csv
from common import compute_room_number, hash_to_64bit
from hash_ring import HashRing, VirtualNode
from guest_manager import GuestManager
from hotel_system import HotelSystem

class TestDistributedHilbertHotel(unittest.TestCase):

    def test_cantor_room_number_formula(self):
        """1. ตรวจสอบเลขห้องตามตัวอย่างสูตรในโจทย์ ข้อ 4.2"""
        self.assertEqual(compute_room_number(1, 1), 1)
        self.assertEqual(compute_room_number(2, 1), 2)
        self.assertEqual(compute_room_number(1, 2), 3)
        self.assertEqual(compute_room_number(3, 1), 4)
        self.assertEqual(compute_room_number(2, 2), 5)

    def test_section_9_1_mini_ring_logic(self):
        """2. ตรวจสอบวงแหวนเล็กสำหรับตรวจตรรกะตามข้อ 9.1"""
        ring = HashRing(V=1)
        # กำหนดตำแหน่งจำลอง: A=20, B=50, C=80 บนวงแหวนขนาด 100
        ring.set_manual_nodes_for_testing([(20, "A", 0), (50, "B", 0), (80, "C", 0)])

        # ฟังก์ชันแปลงตำแหน่งแขก
        guest_positions = { (1,1):10, (1,2):20, (1,3):25, (1,4):35, (1,5):50, (1,6):70, (1,7):90 }
        pos_fn = lambda c, s: guest_positions[(c, s)]

        # ตรวจสอบสถานะเริ่มต้น
        self.assertEqual(ring.get_building_for_guest(1,1, custom_pos_fn=pos_fn), "A")
        self.assertEqual(ring.get_building_for_guest(1,2, custom_pos_fn=pos_fn), "A")
        self.assertEqual(ring.get_building_for_guest(1,3, custom_pos_fn=pos_fn), "B")
        self.assertEqual(ring.get_building_for_guest(1,4, custom_pos_fn=pos_fn), "B")
        self.assertEqual(ring.get_building_for_guest(1,5, custom_pos_fn=pos_fn), "B")
        self.assertEqual(ring.get_building_for_guest(1,6, custom_pos_fn=pos_fn), "C")
        self.assertEqual(ring.get_building_for_guest(1,7, custom_pos_fn=pos_fn), "A")  # วนกลับ

        # กรณีเพิ่ม D ที่ตำแหน่ง 35
        ring_add_d = HashRing(V=1)
        ring_add_d.set_manual_nodes_for_testing([(20, "A", 0), (35, "D", 0), (50, "B", 0), (80, "C", 0)])
        # คนที่ย้ายคือตำแหน่ง 25 (B->D) และ 35 (B->D) รวม 2 คน
        self.assertEqual(ring_add_d.get_building_for_guest(1,3, custom_pos_fn=pos_fn), "D")
        self.assertEqual(ring_add_d.get_building_for_guest(1,4, custom_pos_fn=pos_fn), "D")

        # กรณีลบ B จากสถานะเริ่มต้น
        ring_rem_b = HashRing(V=1)
        ring_rem_b.set_manual_nodes_for_testing([(20, "A", 0), (80, "C", 0)])
        # คนที่ย้ายคือตำแหน่ง 25, 35, 50 (B->C) รวม 3 คน
        self.assertEqual(ring_rem_b.get_building_for_guest(1,3, custom_pos_fn=pos_fn), "C")
        self.assertEqual(ring_rem_b.get_building_for_guest(1,4, custom_pos_fn=pos_fn), "C")
        self.assertEqual(ring_rem_b.get_building_for_guest(1,5, custom_pos_fn=pos_fn), "C")

    def test_edge_cases_section_4_5(self):
        """3. ตรวจสอบกรณีขอบทั้งหมดตามข้อ 4.5"""
        system = HotelSystem(["Building_1", "Building_2"], virtual_nodes_per_building=4)

        # 3.1 เพิ่มอาคารซ้ำ
        rep = system.add_building("Building_1")
        self.assertFalse(rep.is_success)

        # 3.2 ลบอาคารไม่มีอยู่
        rep = system.remove_building("Building_X")
        self.assertFalse(rep.is_success)

        # 3.3 ลบอาคารสุดท้าย (N=1)
        sys_single = HotelSystem(["OnlyOne"], virtual_nodes_per_building=4)
        rep = sys_single.remove_building("OnlyOne")
        self.assertFalse(rep.is_success)

        # 3.4 เพิ่มแขกรหัสซ้ำ
        system.add_guest(1, 1)
        with self.assertRaises(ValueError):
            system.add_guest(1, 1)

        # 3.5 ปฏิเสธกลุ่มที่มีรหัสซ้ำบางคน (Atomic Abort)
        with self.assertRaises(ValueError):
            system.add_guest_group(1, 1, 3) # (1,1) ซ้ำ

        # 3.6 นำแขกที่ไม่มีอยู่ออก
        with self.assertRaises(ValueError):
            system.remove_guest(999, 999)

        # 3.7 ค้นหาแล้วไม่พบ
        self.assertIsNone(system.lookup_by_guest(999, 999))
        self.assertIsNone(system.lookup_by_room("Building_1", 99999))

        # 3.8 สถิติเมื่อ K = 0
        sys_zero = HotelSystem(["B1", "B2"], virtual_nodes_per_building=4)
        stats = sys_zero.get_load_stats()
        self.assertTrue(stats["is_zero_k"])
        self.assertEqual(stats["total_guests"], 0)

    def test_guest_count_invariance_and_csv_export(self):
        """4. ตรวจสอบจำนวนแขกไม่หายไม่เพิ่ม และส่งออก CSV"""
        system = HotelSystem(["B1", "B2"], virtual_nodes_per_building=8)
        system.add_guest_group(1, 1, 50)
        self.assertEqual(system.guest_manager.total_guests, 50)

        # เพิ่มอาคาร
        system.add_building("B3")
        self.assertEqual(system.guest_manager.total_guests, 50)

        # ลบอาคาร
        system.remove_building("B1")
        self.assertEqual(system.guest_manager.total_guests, 50)

        # ส่งออก CSV และตรวจจำนวนแถว
        test_csv = "test_export.csv"
        system.export_guests_to_csv(test_csv)
        self.assertTrue(os.path.exists(test_csv))
        
        with open(test_csv, mode="r", encoding="utf-8") as f:
            lines = [line for line in f.readlines() if line.strip()]
        self.assertEqual(len(lines) - 1, 50) # หัก Header 1 แถว

        if os.path.exists(test_csv):
            os.remove(test_csv)

if __name__ == "__main__":
    unittest.main()