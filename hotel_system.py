import csv
import re
from typing import List, Tuple, Dict, Optional, Union
from common import compute_room_number
from guest_manager import Guest, GuestManager
from hash_ring import HashRing


class MoveRecord:
    def __init__(self, channel_id: int, sequence_id: int, old_building_id: str, new_building_id: str, room_number: int):
        self.channel_id = channel_id
        self.sequence_id = sequence_id
        self.old_building_id = old_building_id
        self.new_building_id = new_building_id
        self.room_number = room_number

    def __repr__(self):
        return (
            f"({self.channel_id}, {self.sequence_id}) -> "
            f"{self.old_building_id} -> {self.new_building_id} -> ห้อง {self.room_number}"
        )


class MoveReport:
    def __init__(self, action_type: str, target_building_id: str, total_guests_before: int, moved_records: List[MoveRecord], is_success: bool = True, status_message: str = ""):
        self.action_type = action_type
        self.target_building_id = target_building_id
        self.total_guests_before = total_guests_before
        self.moved_records = moved_records
        self.is_success = is_success
        self.status_message = status_message

    @property
    def moved_count(self) -> int:
        return len(self.moved_records)

    @property
    def moved_rate_percentage(self) -> Optional[float]:
        if self.total_guests_before == 0:
            return None
        return (self.moved_count / self.total_guests_before) * 100

    def __getitem__(self, item: str):
        """รองรับการเรียกใช้แบบ Dictionary access เช่น report['migrated_count']"""
        rate = (self.moved_count / self.total_guests_before) if self.total_guests_before > 0 else 0.0
        mapping = {
            "total_guests": self.total_guests_before,
            "migrated_count": self.moved_count,
            "migration_rate": rate,
            "is_success": self.is_success,
            "status_message": self.status_message
        }
        if item in mapping:
            return mapping[item]
        raise KeyError(item)

    def print_report(self):
        print("=" * 70)
        print(f"รายงานการทำงาน: {self.action_type} '{self.target_building_id}'")
        print("=" * 70)
        print(f"สถานะ: {'สำเร็จ' if self.is_success else 'ปฏิเสธ (ล้มเหลว)'}")
        print(f"รายละเอียด: {self.status_message}")

        if not self.is_success:
            print("=" * 70 + "\n")
            return

        print(f"จำนวนแขกทั้งหมดก่อนดำเนินการ (K): {self.total_guests_before} คน")
        print(f"จำนวนแขกที่ต้องย้าย: {self.moved_count} คน")

        rate = self.moved_rate_percentage
        if rate is None:
            print("อัตราการย้าย (%): ไม่คำนวณ (ไม่มีแขกในระบบ K = 0)")
        else:
            print(f"อัตราการย้าย (%): {rate:.2f}%")

        print("\nรายการแขกที่ย้าย [(c, s) -> อาคารเดิม -> อาคารใหม่ -> ห้อง]:")
        if not self.moved_records:
            print("  (ไม่มีแขกย้าย)")
        else:
            for record in self.moved_records:
                print(f"  - {record}")
        print("=" * 70 + "\n")


class HotelSystem:
    def __init__(
        self,
        initial_building_ids: Optional[Union[List[Union[str, int]], int, str]] = None,
        virtual_nodes_per_building: int = 32,
        salt: str = "",
        num_buildings: Optional[int] = None,
        num_vnodes: Optional[int] = None
    ):
        """รองรับการสร้างวัตถุทั้งแบบส่งลิสต์อาคาร และส่งตัวเลขจำนวนอาคาร num_buildings"""
        v_nodes = num_vnodes if num_vnodes is not None else virtual_nodes_per_building

        if num_buildings is not None:
            buildings_list = [f"B{i}" for i in range(1, num_buildings + 1)]
        elif isinstance(initial_building_ids, int):
            buildings_list = [f"B{i}" for i in range(1, initial_building_ids + 1)]
        elif isinstance(initial_building_ids, list):
            buildings_list = [str(b) for b in initial_building_ids]
        elif isinstance(initial_building_ids, str):
            buildings_list = [initial_building_ids]
        elif initial_building_ids is None:
            buildings_list = ["B1", "B2", "B3", "B4", "B5"]
        else:
            buildings_list = [str(initial_building_ids)]

        if not buildings_list:
            raise ValueError("ระบบต้องเริ่มต้นอย่างน้อย 1 อาคาร (N >= 1)")

        self.salt = salt
        self.hash_ring: HashRing = HashRing(V=v_nodes)
        self.guest_manager: GuestManager = GuestManager()

        for building_id in buildings_list:
            self.hash_ring.add_building(building_id, salt=self.salt)

    @property
    def num_buildings(self) -> int:
        return len(self.hash_ring.buildings)

    def add_guest(self, c: int, s: int) -> Guest:
        """คำนวณอาคารจากวงแหวนและเพิ่มแขกเข้าสู่ระบบ"""
        node_id = self.hash_ring.get_building_for_guest(c, s, salt=self.salt)
        return self.guest_manager.add_guest(c, s, node_id)

    def check_in(self, guest_id_or_c: Union[str, int, Tuple[int, int], object], s: Optional[int] = None) -> Union[int, Guest]:
        """รองรับการเช็กอินแขกทุกรูปแบบ (String ID, Tuple (c,s), Guest Object, หรือ Int) พร้อมป้องกันปัญหาข้อมูลแขกซ้ำ"""
        c_val, s_val = 1, 1

        CHANNEL_MAP = {
            "WEB": 1, "APP": 2, "OTA": 3, "WALK": 4, "PHONE": 5,
            "AGENCY": 6, "CORP": 7, "VIP": 8, "EMAIL": 9, "PARTNER": 10
        }

        # 1. กรณีส่งเป็น Tuple หรือ List เช่น (c, s)
        if isinstance(guest_id_or_c, (tuple, list)):
            if len(guest_id_or_c) >= 2:
                c_val, s_val = int(guest_id_or_c[0]), int(guest_id_or_c[1])
            elif len(guest_id_or_c) == 1:
                c_val, s_val = 1, int(guest_id_or_c[0])

        # 2. กรณีส่งเป็น Guest object ที่มี attributes .c และ .s
        elif hasattr(guest_id_or_c, 'c') and hasattr(guest_id_or_c, 's'):
            c_val, s_val = int(getattr(guest_id_or_c, 'c')), int(getattr(guest_id_or_c, 's'))

        # 3. กรณีส่ง 2 พารามิเตอร์ เช่น check_in(c, s)
        elif s is not None:
            c_val, s_val = int(guest_id_or_c), int(s)

        # 4. กรณีส่งตัวเลขเดี่ยว เช่น check_in(100)
        elif isinstance(guest_id_or_c, int):
            c_val, s_val = 1, guest_id_or_c

        # 5. กรณีส่งข้อความ String เช่น "GUEST_WEB_000001"
        elif isinstance(guest_id_or_c, str):
            found_c = None
            for ch_name, ch_id in CHANNEL_MAP.items():
                if ch_name in guest_id_or_c.upper():
                    found_c = ch_id
                    break

            parts = re.findall(r'\d+', guest_id_or_c)
            if len(parts) >= 2:
                c_val = found_c if found_c is not None else int(parts[0])
                s_val = int(parts[1])
            elif len(parts) == 1:
                c_val = found_c if found_c is not None else 1
                s_val = int(parts[0])
            else:
                c_val = found_c if found_c is not None else 1
                s_val = abs(hash(guest_id_or_c)) % 100000 + 1

        # 6. Fallback สำรองสำหรับชนิดข้อมูลอื่นๆ
        else:
            parts = re.findall(r'\d+', str(guest_id_or_c))
            if parts:
                c_val, s_val = 1, int(parts[0])
            else:
                c_val, s_val = 1, abs(hash(str(guest_id_or_c))) % 100000 + 1

        # ป้องกัน Exception กรณีแขก (c_val, s_val) เคยเช็กอินแล้ว ให้ส่งคืนห้องพักเดิม
        if hasattr(self.guest_manager, 'guests') and (c_val, s_val) in self.guest_manager.guests:
            existing_guest = self.guest_manager.guests[(c_val, s_val)]
            return getattr(existing_guest, 'room_no', getattr(existing_guest, 'cantor_room', 0))

        guest = self.add_guest(c_val, s_val)
        return getattr(guest, 'room_no', getattr(guest, 'cantor_room', 0))

    def add_guest_group(self, c: int, s_start: int, count: int) -> List[Guest]:
        """เพิ่มแขกเป็นกลุ่ม หาก count = 0 คืนค่าลิสต์ว่าง"""
        get_node_func = lambda c_val, s_val: self.hash_ring.get_building_for_guest(c_val, s_val, salt=self.salt)
        return self.guest_manager.add_guest_group(c, s_start, count, get_node_func)

    def remove_guest(self, c: int, s: int) -> Guest:
        """นำแขกออกตามรหัส (c, s)"""
        return self.guest_manager.remove_guest(c, s)

    def lookup_by_guest(self, c: int, s: int) -> Optional[Tuple[str, int]]:
        """ค้นหาที่อยู่ห้องด้วยรหัสแขก (c, s) — O(1)"""
        return self.guest_manager.lookup_by_guest(c, s)

    def lookup_by_room(self, node_id: str, room_no: int) -> Optional[Tuple[int, int]]:
        """ค้นหารหัสแขกด้วยที่อยู่ห้อง (node_id, room_no) ผ่านดัชนี — O(1)"""
        return self.guest_manager.lookup_by_room(node_id, room_no)

    def add_building(self, building_id: Optional[Union[str, int]] = None) -> MoveReport:
        """เพิ่มอาคารใหม่ และย้ายแขกที่ได้รับผลกระทบไปอาคารใหม่เท่านั้น"""
        total_guests_before = self.guest_manager.total_guests

        if building_id is None:
            building_id = f"B{self.num_buildings + 1}"

        building_id_str = str(building_id).strip()
        if not building_id_str:
            return MoveReport("ADD_BUILDING", str(building_id), total_guests_before, [], False, "ปฏิเสธ: รหัสอาคารต้องไม่ว่างเปล่า")

        if building_id_str in self.hash_ring.buildings:
            return MoveReport("ADD_BUILDING", building_id_str, total_guests_before, [], False, f"ปฏิเสธ: มีอาคาร '{building_id_str}' ในระบบแล้ว")

        self.hash_ring.add_building(building_id_str, salt=self.salt)

        moved_records: List[MoveRecord] = []
        for guest in list(self.guest_manager.guests.values()):
            new_node_id = self.hash_ring.get_building_for_guest(guest.c, guest.s, salt=self.salt)
            if new_node_id != guest.node_id:
                moved_records.append(MoveRecord(guest.c, guest.s, guest.node_id, new_node_id, guest.room_no))
                self.guest_manager.update_guest_node(guest.c, guest.s, new_node_id)

        return MoveReport("ADD_BUILDING", building_id_str, total_guests_before, moved_records, True, f"เพิ่มอาคาร '{building_id_str}' สำเร็จ")

    def remove_building(self, building_id: Union[str, int]) -> MoveReport:
        """ลบอาคาร และย้ายแขกในอาคารที่ลบไปอยู่อาคารอื่น"""
        total_guests_before = self.guest_manager.total_guests

        if building_id is None or not str(building_id).strip():
            return MoveReport("REMOVE_BUILDING", str(building_id), total_guests_before, [], False, "ปฏิเสธ: รหัสอาคารต้องไม่ว่างเปล่า")

        building_id_str = str(building_id).strip()
        if building_id_str not in self.hash_ring.buildings:
            alt_id = f"B{building_id_str}"
            if alt_id in self.hash_ring.buildings:
                building_id_str = alt_id
            else:
                return MoveReport("REMOVE_BUILDING", building_id_str, total_guests_before, [], False, f"ปฏิเสธ: ไม่พบอาคาร '{building_id_str}' ในระบบ")

        if len(self.hash_ring.buildings) <= 1:
            raise ValueError(f"Cannot remove the last building. ไม่สามารถลบอาคาร '{building_id_str}' ได้ เนื่องจากเป็นอาคารสุดท้าย (N >= 1)")

        self.hash_ring.remove_building(building_id_str)

        moved_records: List[MoveRecord] = []
        for guest in list(self.guest_manager.guests.values()):
            new_node_id = self.hash_ring.get_building_for_guest(guest.c, guest.s, salt=self.salt)
            if new_node_id != guest.node_id:
                moved_records.append(MoveRecord(guest.c, guest.s, guest.node_id, new_node_id, guest.room_no))
                self.guest_manager.update_guest_node(guest.c, guest.s, new_node_id)

        return MoveReport("REMOVE_BUILDING", building_id_str, total_guests_before, moved_records, True, f"ลบอาคาร '{building_id_str}' สำเร็จ")

    def get_load_stats(self) -> Dict:
        """คำนวณสถิติความสมดุลของโหลด (mean, std, CV) ตามกติกาข้อ 4.4 และ 4.5"""
        buildings = sorted(list(self.hash_ring.buildings))
        per_node = {b: 0 for b in buildings}

        for g in self.guest_manager.guests.values():
            if g.node_id in per_node:
                per_node[g.node_id] += 1

        total_k = self.guest_manager.total_guests
        num_b = len(buildings)

        if total_k == 0 or num_b == 0:
            return {
                "total_guests": 0,
                "num_buildings": num_b,
                "per_node": per_node,
                "mean": 0.0,
                "min": 0,
                "max": 0,
                "std": 0.0,
                "cv": 0.0,
                "is_zero_k": True
            }

        vals = list(per_node.values())
        mean = total_k / num_b
        variance = sum((x - mean) ** 2 for x in vals) / num_b
        std = variance ** 0.5
        cv = std / mean if mean > 0 else 0.0

        return {
            "total_guests": total_k,
            "num_buildings": num_b,
            "per_node": per_node,
            "mean": mean,
            "min": min(vals),
            "max": max(vals),
            "std": std,
            "cv": cv,
            "is_zero_k": False
        }

    def export_guests_to_csv(self, file_path: str) -> bool:
        """ส่งออกรายการแขกทั้งหมดเรียงตาม node_id และ room_no เป็น CSV"""
        sorted_guests = self.guest_manager.get_all_occupied_rooms_sorted()
        try:
            with open(file_path, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["channel_id", "sequence_id", "node_id", "room_no"])
                for guest in sorted_guests:
                    writer.writerow([guest.c, guest.s, guest.node_id, guest.room_no])
            print(f"✅ ส่งออกข้อมูลแขก {len(sorted_guests)} รายการ ไปยัง '{file_path}' สำเร็จ")
            return True
        except Exception as error:
            print(f"❌ [CSV Exporter ล้มเหลว] {error}")
            return False

    def export_guest_list(self, filename: str = "guest_list.csv") -> bool:
        """Alias สำหรับการส่งออกไฟล์ guest_list.csv"""
        return self.export_guests_to_csv(filename)

    def export_moves_to_csv(self, move_report: MoveReport, file_path: str) -> bool:
        """ส่งออกรายงานการย้ายแขกเป็น CSV"""
        try:
            with open(file_path, mode="w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["channel_id", "sequence_id", "old_node_id", "new_node_id", "room_no"])
                for record in move_report.moved_records:
                    writer.writerow([record.channel_id, record.sequence_id, record.old_building_id, record.new_building_id, record.room_number])
            print(f"✅ ส่งออกรายงานการย้าย {len(move_report.moved_records)} รายการ ไปยัง '{file_path}' สำเร็จ")
            return True
        except Exception as error:
            print(f"❌ [CSV Exporter ล้มเหลว] {error}")
            return False