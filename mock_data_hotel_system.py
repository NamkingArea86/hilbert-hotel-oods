import os
from hotel_system import HotelSystem


def run_mock_simulation():
    print("=" * 75)
    print("      เริ่มต้นการจำลองข้อมูลทดสอบระบบ (Mock Data Simulation)")
    print("=" * 75 + "\n")

    # --------------------------------------------------------------------------
    # 1. การตั้งค่าระบบเริ่มต้น (Initial System Setup)
    # --------------------------------------------------------------------------
    initial_buildings = ["Building_A", "Building_B", "Building_C", "Building_D"]
    virtual_nodes_per_building = 16

    print(f"[1] เริ่มต้นสร้าง HotelSystem ด้วย {len(initial_buildings)} อาคาร:")
    for b_id in initial_buildings:
        print(f"    - {b_id}")

    hotel_system = HotelSystem(
        initial_building_ids=initial_buildings,
        virtual_nodes_per_building=virtual_nodes_per_building,
    )
    print("    -> สร้างระบบเรียบร้อยแล้ว\n")

    # --------------------------------------------------------------------------
    # 2. จำลองการเพิ่มแขกเข้าสู่ระบบ (Mock Guest Data Generation)
    # --------------------------------------------------------------------------
    print("[2] จำลองการสร้างข้อมูลแขกเป็นกลุ่ม (Mock Guest Groups):")

    # กำหนดข้อมูลจำลอง 5 ช่องทาง (Channels)
    mock_guest_batches = [
        {"channel_id": 101, "start_seq": 1, "count": 25},
        {"channel_id": 102, "start_seq": 1, "count": 30},
        {"channel_id": 103, "start_seq": 1, "count": 15},
        {"channel_id": 104, "start_seq": 1, "count": 40},
        {"channel_id": 105, "start_seq": 1, "count": 20},
    ]

    for batch in mock_guest_batches:
        c_id = batch["channel_id"]
        s_start = batch["start_seq"]
        count = batch["count"]

        hotel_system.guest_manager.add_guest_group(
            c=c_id,
            s_start=s_start,
            count=count,
            get_node_func=lambda c, s: hotel_system.hash_ring.get_building_for_guest(
                c, s
            ),
        )
        print(
            f"    + เพิ่มแขก ช่องทาง {c_id}: ลำดับ {s_start} ถึง {s_start + count - 1} ({count} คน)"
        )

    total_guests_k = hotel_system.guest_manager.total_guests
    print(f"    -> สรุปจำนวนแขกในระบบทั้งหมดก่อนดำเนินการ (K): {total_guests_k} คน\n")

    # --------------------------------------------------------------------------
    # 3. ทดสอบการทำงานปกติ: เพิ่มอาคารใหม่ (Add Building Normal Case)
    # --------------------------------------------------------------------------
    print("[3] ทดสอบการเพิ่มอาคารใหม่ 'Building_E' (Normal Case):")
    add_report_e = hotel_system.add_building("Building_E")
    add_report_e.print_report()

    # --------------------------------------------------------------------------
    # 4. ทดสอบการทำงานปกติ: ลบอาคาร (Remove Building Normal Case)
    # --------------------------------------------------------------------------
    print("[4] ทดสอบการลบอาคาร 'Building_B' (Normal Case):")
    remove_report_b = hotel_system.remove_building("Building_B")
    remove_report_b.print_report()

    # --------------------------------------------------------------------------
    # 5. ทดสอบการจัดการกรณีขอบทั้งหมด (Edge Cases Testing)
    # --------------------------------------------------------------------------
    print("[5] ทดสอบการรับมือกรณีขอบ (Edge Cases Testing):")

    print("\n   5.1 เพิ่มอาคารที่มีอยู่แล้วในระบบ (Duplicate Building ID):")
    dup_add_report = hotel_system.add_building("Building_A")
    dup_add_report.print_report()

    print("   5.2 ลบอาคารที่ไม่มีอยู่จริงในระบบ (Non-existent Building ID):")
    missing_remove_report = hotel_system.remove_building("Building_Unknown_999")
    missing_remove_report.print_report()

    print("   5.3 ป้อนรหัสอาคารเป็นค่าว่างเปล่า (Empty / Whitespace String):")
    empty_building_report = hotel_system.add_building("   ")
    empty_building_report.print_report()

    print("   5.4 ทดสอบการเพิ่มกลุ่มแขกที่มีรหัสซ้ำบางรายการ (Batch Insert Collision):")
    try:
        # พยายามเพิ่มแขกช่องทาง 101 ลำดับที่ 20-29 ซึ่งบางส่วน (20-25) มีอยู่แล้ว
        hotel_system.guest_manager.add_guest_group(
            c=101,
            s_start=20,
            count=10,
            get_node_func=lambda c, s: hotel_system.hash_ring.get_building_for_guest(
                c, s
            ),
        )
    except ValueError as e:
        print(f"    [ผลการปฏิเสธ]: {e}\n")

    # --------------------------------------------------------------------------
    # 6. ส่งออกข้อมูลทั้งหมดเป็นไฟล์ CSV
    # --------------------------------------------------------------------------
    print("[6] ส่งออกข้อมูลจำลองไปยังไฟล์ CSV:")
    csv_guests_path = "mock_guests_output.csv"
    csv_moves_path = "mock_moves_output.csv"

    hotel_system.export_guests_to_csv(csv_guests_path)
    hotel_system.export_moves_to_csv(remove_report_b, csv_moves_path)

    print("\n" + "=" * 75)
    print("      การจำลองข้อมูลทดสอบเสร็จสมบูรณ์เรียบร้อยแล้ว!")
    print("=" * 75)


if __name__ == "__main__":
    run_mock_simulation()
