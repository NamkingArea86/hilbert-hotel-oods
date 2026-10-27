import bisect
from typing import List, Set, Optional, Callable, Tuple
from common import hash_to_64bit

class VirtualNode:
    def __init__(self, pos: int, node_id: str, j: int):
        self.pos = pos
        self.node_id = node_id
        self.j = j

    def __repr__(self):
        return f"VirtualNode(pos={self.pos}, node_id='{self.node_id}', j={self.j})"


class HashRing:
    def __init__(self, V: int = 32):
        if V < 1:
            raise ValueError("จำนวน virtual node (V) ต้อง >= 1")
        self.V = V
        self.nodes: List[VirtualNode] = []
        self.buildings: Set[str] = set()

    @property
    def N(self) -> int:
        return len(self.buildings)

    def add_building(self, node_id: str, salt: str = ""):
        """
        เพิ่มอาคารและแทรก virtual nodes V ตัวลงในวงแหวน
        ใช้ bisect.insort พร้อมคีย์ (pos, node_id, j) ตามกติกาข้อ 4.3 (4)
        """
        if not node_id or not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("ปฏิเสธ: รหัสอาคารต้องเป็นข้อความที่ไม่ว่างเปล่า")
        
        node_id = node_id.strip()
        if node_id in self.buildings:
            raise ValueError(f"ปฏิเสธ: มีอาคาร '{node_id}' ในระบบแล้ว")

        self.buildings.add(node_id)
        for j in range(self.V):
            key_str = f"node:{node_id}:{j}"
            pos = hash_to_64bit(key_str, salt=salt)
            vnode = VirtualNode(pos, node_id, j)
            bisect.insort(self.nodes, vnode, key=lambda v: (v.pos, v.node_id, v.j))

    def remove_building(self, node_id: str):
        """
        ลบอาคารและลบ virtual nodes ทั้งหมดของอาคารนั้น
        ปฏิเสธหากลบอาคารสุดท้าย (N=1) หรืออาคารไม่มีอยู่ ตามกติกาข้อ 4.5
        """
        if not node_id or not isinstance(node_id, str):
            raise ValueError("ปฏิเสธ: รหัสอาคารไม่ถูกต้อง")

        node_id = node_id.strip()
        if node_id not in self.buildings:
            raise ValueError(f"ปฏิเสธ: ไม่พบอาคาร '{node_id}' ในระบบ")

        if self.N == 1:
            raise ValueError("ปฏิเสธ: ไม่สามารถลบอาคารสุดท้ายได้ (ระบบต้องมีอย่างน้อย N >= 1 อาคาร)")

        self.buildings.remove(node_id)
        self.nodes = [v for v in self.nodes if v.node_id != node_id]

    def get_building_for_guest(self, c: int, s: int, salt: str = "", custom_pos_fn: Optional[Callable[[int, int], int]] = None) -> str:
        """
        คำนวณตำแหน่งแขกบนวงแหวน ค้นหา virtual node แรกที่มีตำแหน่ง >= แขก (เดินตามเข็มนาฬิกา)
        หากเกินจุดสุดท้าย ให้วนกลับไปจุดแรก (ข้อ 4.3 ข้อ 3)
        ใช้วิธี bisect.bisect_left เป็น Binary Search O(log M)
        """
        if not self.nodes:
            raise ValueError("ไม่มีโหนดอยู่ในวงแหวน")

        if custom_pos_fn:
            guest_pos = custom_pos_fn(c, s)
        else:
            guest_key = f"guest:{c}:{s}"
            guest_pos = hash_to_64bit(guest_key, salt=salt)

        idx = bisect.bisect_left(
            self.nodes, 
            (guest_pos, "", -1), 
            key=lambda v: (v.pos, v.node_id, v.j)
        )

        if idx == len(self.nodes):
            idx = 0

        return self.nodes[idx].node_id

    def set_manual_nodes_for_testing(self, manual_vnodes: List[Tuple[int, str, int]]):
        """
        ฟังก์ชันฉีดตำแหน่งจุดทดสอบ (สำหรับทดสอบวงแหวนจำลองตามหัวข้อ 9.1)
        """
        self.nodes = []
        self.buildings = set()
        for pos, node_id, j in manual_vnodes:
            self.buildings.add(node_id)
            vnode = VirtualNode(pos, node_id, j)
            self.nodes.append(vnode)
        self.nodes.sort(key=lambda v: (v.pos, v.node_id, v.j))