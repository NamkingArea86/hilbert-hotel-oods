from typing import Dict, Tuple, Optional, List, Callable
from common import compute_room_number

class Guest:
    def __init__(self, c: int, s: int, node_id: str):
        if c < 1 or s < 1:
            raise ValueError("Channel ID (c) และ Sequence ID (s) ต้องเป็นจำนวนเต็มบวก (>= 1)")
        
        self.c: int = c
        self.s: int = s
        self.node_id: str = node_id
        self.room_no: int = compute_room_number(c, s)

    @property
    def guest_id(self) -> Tuple[int, int]:
        return (self.c, self.s)

    @property
    def room_key(self) -> Tuple[str, int]:
        return (self.node_id, self.room_no)

    @property
    def cantor_room(self) -> int:
        """Alias สำหรับการเข้าถึงหมายเลขห้อง Cantor"""
        return self.room_no

    @property
    def building_id(self) -> str:
        """Alias สำหรับการเข้าถึงรหัสอาคาร"""
        return self.node_id

    def __repr__(self):
        return f"Guest(c={self.c}, s={self.s}, node_id='{self.node_id}', room_no={self.room_no})"


class GuestManager:
    def __init__(self):
        self.guests: Dict[Tuple[int, int], Guest] = {}
        self.room_to_guest: Dict[Tuple[str, int], Tuple[int, int]] = {}

    @property
    def total_guests(self) -> int:
        return len(self.guests)

    @property
    def guest_to_room(self) -> Dict[Tuple[int, int], Tuple[str, int, int]]:
        """ส่งคืน Dictionary สำหรับการอ่านที่อยู่ห้องเพื่อรองรับ guided_test.py"""
        return {
            (g.c, g.s): (g.node_id, g.room_no, g.room_no)
            for g in self.guests.values()
        }

    @property
    def building_rooms(self) -> Dict[str, Dict[Tuple[int, int], Guest]]:
        """จัดกลุ่มแขกตามอาคารเพื่อรองรับการคำนวณสถิติโหลด"""
        b_map = {}
        for g in self.guests.values():
            if g.node_id not in b_map:
                b_map[g.node_id] = {}
            b_map[g.node_id][(g.c, g.s)] = g
        return b_map

    def clear(self):
        """ล้างข้อมูลแขกทั้งหมดในระบบ"""
        self.guests.clear()
        self.room_to_guest.clear()

    def add_guest(self, c: int, s: int, node_id: str) -> Guest:
        """เพิ่มแขกรายบุคคล ตรวจสอบการซ้ำของรหัสแขกและที่อยู่ห้อง"""
        if (c, s) in self.guests:
            raise ValueError(f"ปฏิเสธ: มีแขกรหัส (c={c}, s={s}) อยู่ในระบบแล้ว")

        guest = Guest(c, s, node_id)
        room_key = guest.room_key

        if room_key in self.room_to_guest:
            raise ValueError(f"ปฏิเสธ: ห้องพัก {room_key} มีผู้เข้าพักอยู่แล้ว")

        self.guests[(c, s)] = guest
        self.room_to_guest[room_key] = (c, s)
        return guest

    def add_guest_group(self, c: int, s_start: int, count: int, get_node_func: Callable[[int, int], str]) -> List[Guest]:
        """
        เพิ่มแขกเป็นกลุ่ม (count >= 0)
        หาก count = 0 จะคืนค่าลิสต์ว่างโดยไม่เปลี่ยนแปลงข้อมูล
        หากมีรหัสแขกทับซ้อนแม้รายการเดียว จะปฏิเสธทั้งกลุ่มตามกติกาข้อ 4.1 (3) และ 4.5
        """
        if count < 0:
            raise ValueError("จำนวนแขกต้องไม่เป็นจำนวนติดลบ")
        if count == 0:
            return []
        if s_start < 1:
            raise ValueError("ลำดับเริ่มต้น s_start ต้อง >= 1")

        target_keys = [(c, s) for s in range(s_start, s_start + count)]
        for key in target_keys:
            if key in self.guests:
                raise ValueError(
                    f"ปฏิเสธการเพิ่มเป็นกลุ่ม: พบรหัสแขก (c={key[0]}, s={key[1]}) ซ้ำในระบบ (ยกเลิกทั้งกลุ่ม)"
                )

        added_guests = []
        for c_val, s_val in target_keys:
            node_id = get_node_func(c_val, s_val)
            guest = self.add_guest(c_val, s_val, node_id)
            added_guests.append(guest)

        return added_guests

    def remove_guest(self, c: int, s: int) -> Guest:
        """นำแขกออกตามรหัส (c, s) และอัปเดตดัชนีห้องพัก"""
        if (c, s) not in self.guests:
            raise ValueError(f"ปฏิเสธ: ไม่พบแขกรหัส (c={c}, s={s}) ในระบบ")

        guest = self.guests.pop((c, s))
        room_key = guest.room_key
        
        if room_key in self.room_to_guest:
            del self.room_to_guest[room_key]

        return guest

    def update_guest_node(self, c: int, s: int, new_node_id: str):
        """
        ย้ายอาคารของแขก และอัปเดตดัชนีห้องพัก room_to_guest
        มีการตรวจเช็กก่อนว่าห้องพักปลายทางว่างหรือไม่เพื่อป้องกันการเขียนทับ
        """
        if (c, s) not in self.guests:
            raise ValueError(f"ไม่พบแขกรหัส (c={c}, s={s}) ในระบบ")

        guest = self.guests[(c, s)]
        old_room_key = (guest.node_id, guest.room_no)
        new_room_key = (new_node_id, guest.room_no)

        if new_room_key in self.room_to_guest and self.room_to_guest[new_room_key] != (c, s):
            raise ValueError(f"ไม่สามารถย้ายได้: ห้อง {new_room_key} มีแขกท่านอื่นพักอยู่")

        if old_room_key in self.room_to_guest:
            del self.room_to_guest[old_room_key]

        guest.node_id = new_node_id
        self.room_to_guest[new_room_key] = (c, s)

    def lookup_by_guest(self, c: int, s: int) -> Optional[Tuple[str, int]]:
        """ค้นหาที่อยู่ห้อง (node_id, room_no) ด้วยรหัสแขก (c, s) — O(1)"""
        guest = self.guests.get((c, s))
        if guest:
            return (guest.node_id, guest.room_no)
        return None

    def lookup_by_room(self, node_id: str, room_no: int) -> Optional[Tuple[int, int]]:
        """ค้นหารหัสแขก (c, s) ด้วยที่อยู่ห้อง (node_id, room_no) ผ่านดัชนี — O(1)"""
        return self.room_to_guest.get((node_id, room_no))

    def get_all_occupied_rooms_sorted(self) -> List[Guest]:
        """คืนค่ารายการแขกเรียงตาม node_id จากน้อยไปมาก และ room_no จากน้อยไปมาก"""
        return sorted(self.guests.values(), key=lambda g: (str(g.node_id), g.room_no))