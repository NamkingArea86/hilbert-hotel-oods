import csv
from typing import List, Tuple, Dict, Optional
from common import compute_room_number
from guest_manager import Guest, GuestManager
from hash_ring import HashRing


class MoveRecord:
  def __init__(self,channel_id: int,sequence_id: int,old_building_id: str,new_building_id: str,room_number: int,):
    self.channel_id= channel_id
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
  def __init__(
    self,action_type: str,target_building_id: str,total_guests_before: int,moved_records: List[MoveRecord],is_success: bool = True,status_message: str = "",):
    self.action_type = action_type  
    self.target_building_id = target_building_id
    self.total_guests_before = total_guests_before
    self.moved_records = moved_records
    self.is_success = is_success
    self.status_message = status_message

  @property
  def moved_count(self):
    return len(self.moved_records)

  @property
  def moved_rate_percentage(self):
    if self.total_guests_before == 0:
      return None
    return (self.moved_count / self.total_guests_before) * 100

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
  def __init__(self,initial_building_ids: List[str],virtual_nodes_per_building: int = 32,):    
    if not initial_building_ids:
      raise ValueError("ระบบต้องเริ่มต้นอย่างน้อย 1 อาคาร")

    self.hash_ring: HashRing = HashRing(V=virtual_nodes_per_building)
    self.guest_manager: GuestManager = GuestManager()

    for building_id in initial_building_ids:
      self.hash_ring.add_building(building_id)

  def add_building(self, building_id: str):
    total_guests_before = self.guest_manager.total_guests

    if not building_id or not isinstance(building_id, str) or not building_id.strip():
      return MoveReport(action_type="ADD_BUILDING",target_building_id=str(building_id),total_guests_before=total_guests_before,moved_records=[],is_success=False,status_message="ปฏิเสธ: รหัสอาคารต้องเป็นข้อความที่ไม่ว่างเปล่า",)

    building_id = building_id.strip()
    if building_id in self.hash_ring.buildings:
      return MoveReport(action_type="ADD_BUILDING",target_building_id=building_id,total_guests_before=total_guests_before,moved_records=[],is_success=False,status_message=f"ปฏิเสธ: มีอาคาร '{building_id}' อยู่ในระบบแล้ว",)

    self.hash_ring.add_building(building_id)

    moved_records: List[MoveRecord] = []
    for guest in list(self.guest_manager.guests.values()):
      channel_id = guest.c
      sequence_id = guest.s

      new_building_id = self.hash_ring.get_building_for_guest(channel_id, sequence_id)

      if new_building_id != guest.node_id:
        assert new_building_id == building_id, ("ข้อผิดพลาดตรรกะ: แขกต้องย้ายเข้าอาคารใหม่เท่านั้น")

        moved_records.append(
            MoveRecord(channel_id=channel_id,sequence_id=sequence_id,old_building_id=guest.node_id,new_building_id=new_building_id,room_number=guest.room_no,)
        )

        self.guest_manager.update_guest_node(
            channel_id, sequence_id, new_building_id
        )

    return MoveReport(action_type="ADD_BUILDING",target_building_id=building_id,total_guests_before=total_guests_before,moved_records=moved_records,is_success=True,status_message=f"เพิ่มอาคาร '{building_id}' สำเร็จ",)

  def remove_building(self, building_id: str):
    total_guests_before = self.guest_manager.total_guests

    if not building_id or not isinstance(building_id, str) or not building_id.strip():
      return MoveReport(action_type="REMOVE_BUILDING",target_building_id=str(building_id),total_guests_before=total_guests_before,moved_records=[],is_success=False,status_message="ปฏิเสธ: รหัสอาคารต้องเป็นข้อความที่ไม่ว่างเปล่า",
      )

    building_id = building_id.strip()
    if building_id not in self.hash_ring.buildings:
      return MoveReport(action_type="REMOVE_BUILDING",target_building_id=building_id,total_guests_before=total_guests_before,moved_records=[],is_success=False,status_message=f"ปฏิเสธ: ไม่พบอาคาร '{building_id}' ในระบบ",
      )

    if self.hash_ring.N == 1:
      return MoveReport(action_type="REMOVE_BUILDING",target_building_id=building_id,total_guests_before=total_guests_before,moved_records=[],is_success=False,status_message=f"ปฏิเสธ: ไม่สามารถลบอาคาร '{building_id}' ได้ เนื่องจากเป็นอาคารสุดท้าย (N >= 1)",
      )

    self.hash_ring.remove_building(building_id)

    moved_records: List[MoveRecord] = []
    for guest in list(self.guest_manager.guests.values()):
      channel_id = guest.c
      sequence_id = guest.s

      new_building_id = self.hash_ring.get_building_for_guest(channel_id, sequence_id)

      if new_building_id != guest.node_id:
        assert guest.node_id == building_id, ("ข้อผิดพลาดตรรกะ: แขกในอาคารอื่นที่ไม่ใช่อาคารที่ลบต้องไม่ย้าย")

        moved_records.append(MoveRecord(channel_id=channel_id,sequence_id=sequence_id,old_building_id=guest.node_id,new_building_id=new_building_id,room_number=guest.room_no,))

        self.guest_manager.update_guest_node(channel_id, sequence_id, new_building_id)

    return MoveReport(action_type="REMOVE_BUILDING",target_building_id=building_id,total_guests_before=total_guests_before,moved_records=moved_records,is_success=True,status_message=f"ลบอาคาร '{building_id}' สำเร็จ",)

  def export_guests_to_csv(self, file_path: str):
    sorted_guests = self.guest_manager.get_all_occupied_rooms_sorted()

    try:
        with open(file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["channel_id", "sequence_id", "node_id", "room_no"])
            for guest in sorted_guests:
              writer.writerow(
                [guest.c, guest.s, guest.node_id, guest.room_no]
                )
        print(
            f"[CSV Exporter] ส่งออกข้อมูลแขก {len(sorted_guests)} รายการ ไปยัง '{file_path}' สำเร็จ"
        )
        return True
    except Exception as error:
        print(f"[CSV Exporter ล้มเหลว] {error}")
        return False

  def export_moves_to_csv(
    self, move_report: MoveReport, file_path: str):

    try:
        with open(file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["channel_id","sequence_id","old_node_id","new_node_id","room_no",]
            )
            for record in move_report.moved_records:
                writer.writerow(
                    [record.channel_id,record.sequence_id,record.old_building_id,record.new_building_id,record.room_number,]
                )
        print(f"[CSV Exporter] ส่งออกรายงานการย้าย {len(move_report.moved_records)} รายการ ไปยัง '{file_path}' สำเร็จ")
        return True
    except Exception as error:
        print(f"[CSV Exporter ล้มเหลว] {error}")
        return False
