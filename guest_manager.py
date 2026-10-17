from typing import Dict, Tuple, Optional, List, Callable
from common import compute_room_number

class Guest:
    def __init__(self, c: int, s: int, node_id: str):
        if c < 1 or s < 1:
            raise ValueError("Channel ID (c) and Sequence ID (s) must be positive integers (>= 1)")
        
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

    def __repr__(self):
        return f"Guest(c={self.c}, s={self.s}, node_id='{self.node_id}', room_no={self.room_no})"


class GuestManager:
    def __init__(self):
        self.guests: Dict[Tuple[int, int], Guest] = {}
        self.room_to_guest: Dict[Tuple[str, int], Tuple[int, int]] = {}

    @property
    def total_guests(self) -> int:
        return len(self.guests)

    def add_guest(self, c: int, s: int, node_id: str) -> Guest:
        if (c, s) in self.guests:
            raise ValueError(f"Rejected: Guest ID ({c}, {s}) already exists in the system")

        guest = Guest(c, s, node_id)
        room_key = guest.room_key

        if room_key in self.room_to_guest:
            raise ValueError(f"Error: Room {room_key} is already occupied")

        self.guests[(c, s)] = guest
        self.room_to_guest[room_key] = (c, s)
        return guest

    def add_guest_group(self, c: int, s_start: int, count: int, get_node_func: Callable[[int, int], str]) -> List[Guest]:
        if count < 0:
            raise ValueError("Guest count must not be negative")
        if count == 0:
            return []
        if s_start < 1:
            raise ValueError("s_start must be >= 1")

        target_keys = [(c, s) for s in range(s_start, s_start + count)]
        for key in target_keys:
            if key in self.guests:
                raise ValueError(
                    f"Batch insert rejected: Guest ID {key} already exists in the system (entire batch aborted)"
                )

        added_guests = []
        for c_val, s_val in target_keys:
            node_id = get_node_func(c_val, s_val)
            guest = self.add_guest(c_val, s_val, node_id)
            added_guests.append(guest)

        return added_guests

    def remove_guest(self, c: int, s: int) -> Guest:
        if (c, s) not in self.guests:
            raise ValueError(f"Guest ID ({c}, {s}) not found in the system")

        guest = self.guests.pop((c, s))
        room_key = guest.room_key
        
        if room_key in self.room_to_guest:
            del self.room_to_guest[room_key]

        return guest

    def update_guest_node(self, c: int, s: int, new_node_id: str):
        if (c, s) not in self.guests:
            raise ValueError(f"Guest ID ({c}, {s}) not found in the system")

        guest = self.guests[(c, s)]
        old_room_key = (guest.node_id, guest.room_no)

        if old_room_key in self.room_to_guest:
            del self.room_to_guest[old_room_key]

        guest.node_id = new_node_id

        new_room_key = (guest.node_id, guest.room_no)
        self.room_to_guest[new_room_key] = (c, s)

        def lookup_by_guest(self, c: int, s: int) -> Optional[Tuple[str, int]]:
            guest = self.guests.get((c, s))
            if guest:
                return (guest.node_id, guest.room_no)
            return None

        def lookup_by_room(self, node_id: str, room_no: int) -> Optional[Tuple[int, int]]:
            return self.room_to_guest.get((node_id, room_no))

    def get_all_occupied_rooms_sorted(self) -> List[Guest]:
        return sorted(self.guests.values(), key=lambda g: (g.node_id, g.room_no))
