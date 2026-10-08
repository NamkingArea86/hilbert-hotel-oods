import bisect
from typing import List, Set
from common import hash_to_64bit

class VirtualNode:
    def __init__(self, pos: int, node_id: str, j: int):
        self.pos = pos
        self.node_id = node_id
        self.j = j 

class HashRing:
    def __init__(self, V: int):
        if V < 1:
            raise ValueError("V must >= 1")
        self.V = V
        self.nodes: List[VirtualNode] = []
        self.buildings: Set[str] = set()

    @property
    def N(self):
        return len(self.buildings)

    def add_building(self, node_id: str):
        if not node_id or not isinstance(node_id, str):
            raise ValueError("Must not be empty.")
            
        if node_id in self.buildings:
            raise ValueError(f"have '{node_id}' in system")

        self.buildings.add(node_id)
        for j in range(self.V):
            key_str = f"node:{node_id}:{j}"
            pos = hash_to_64bit(key_str)
            vnode = VirtualNode(pos, node_id, j)
            bisect.insort(self.nodes, vnode, key=lambda v: (v.pos, v.node_id, v.j))

    def remove_building(self, node_id: str):
        if node_id not in self.buildings:
            raise ValueError(f"Not founded '{node_id}'.")
            
        if self.N == 1:
            raise ValueError("Can not remove last N.")

        self.buildings.remove(node_id)
        self.nodes = [v for v in self.nodes if v.node_id != node_id]

    def get_building_for_guest(self, c: int, s: int) -> str:
        if not self.nodes:
            raise ValueError("Not founded")

        guest_key = f"guest:{c}:{s}"
        guest_pos = hash_to_64bit(guest_key)

        idx = bisect.bisect_left(
            self.nodes, 
            (guest_pos, "", -1), 
            key=lambda v: (v.pos, v.node_id, v.j)
        )

        if idx == len(self.nodes):
            idx = 0

        return self.nodes[idx].node_id