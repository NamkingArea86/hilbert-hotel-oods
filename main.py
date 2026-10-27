import sys
from hotel_system import HotelSystem

def print_menu():
    print("\n" + "="*55)
    print("  🏨 ระบบโรงแรมอนันต์แบบกระจาย Distributed Hilbert Hotel")
    print("="*55)
    print("  1. เพิ่มแขกคนเดียว")
    print("  2. เพิ่มแขกเป็นกลุ่ม")
    print("  3. ลบแขก")
    print("  4. เพิ่มอาคาร")
    print("  5. ลบอาคาร")
    print("  6. ค้นหาข้อมูลแขก (สองทาง)")
    print("  7. แสดงรายการห้องที่มีผู้พัก")
    print("  8. แสดงสถิติความสมดุลของโหลด")
    print("  9. ส่งออกข้อมูลเป็น CSV (แขก / รายการย้ายล่าสุด)")
    print(" 10. รันชุดการทดลองและเปรียบเทียบประสิทธิภาพ")
    print("  0. ออกจากโปรแกรม")
    print("="*55)

def get_valid_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = input(prompt).strip()
            if val == "":
                print("❌ กรุณาป้อนค่า")
                continue
            num = int(val)
            if min_val is not None and num < min_val:
                print(f"❌ ค่าต้องไม่น้อยกว่า {min_val}")
                continue
            if max_val is not None and num > max_val:
                print(f"❌ ค่าต้องไม่มากกว่า {max_val}")
                continue
            return num
        except ValueError:
            print("❌ กรุณาป้อนจำนวนเต็มเท่านั้น")

def main():
    print("กำลังเริ่มต้นระบบ...")
    N = get_valid_int("จำนวนอาคารเริ่มต้น (N >= 1): ", min_val=1)
    V = get_valid_int("จำนวนโหนดเสมือนต่ออาคาร (V >= 1): ", min_val=1)
    
    building_names = [f"Building_{i+1}" for i in range(N)]
    system = HotelSystem(building_names, V)
    last_move_report = None

    # ถามการสร้างแขกเริ่มต้นหลายช่องทาง
    setup_guests = input("ต้องการสร้างแขกเริ่มต้นทันทีหรือไม่? (y/n): ").strip().lower()
    if setup_guests == 'y':
        channels = get_valid_int("จำนวนช่องทาง (C >= 1): ", min_val=1)
        per_channel = get_valid_int("จำนวนแขกต่อช่องทาง: ", min_val=1)
        for c in range(1, channels + 1):
            system.add_guest_group(c, 1, per_channel)
        print(f"✅ เพิ่มแขกเริ่มต้นสำเร็จ รวม {system.guest_manager.total_guests} คน")

    while True:
        print_menu()
        choice = get_valid_int("เลือกเมนู (0-10): ", min_val=0, max_val=10)

        if choice == 0:
            print("👋 ออกจากโปรแกรม...")
            break

        elif choice == 1:
            print("\n--- เพิ่มแขกคนเดียว ---")
            c = get_valid_int("รหัสช่องทาง (c >= 1): ", min_val=1)
            s = get_valid_int("ลำดับภายในช่องทาง (s >= 1): ", min_val=1)
            try:
                guest = system.add_guest(c, s)
                print(f"✅ เพิ่มสำเร็จ → อาคาร: {guest.node_id}, ห้อง: {guest.room_no}")
            except ValueError as e:
                print(f"❌ {e}")

        elif choice == 2:
            print("\n--- เพิ่มแขกเป็นกลุ่ม ---")
            c = get_valid_int("รหัสช่องทาง (c >= 1): ", min_val=1)
            s_start = get_valid_int("ลำดับเริ่มต้น (s_start >= 1): ", min_val=1)
            count = get_valid_int("จำนวนแขก (>= 0): ", min_val=0) # count=0 ได้
            try:
                added = system.add_guest_group(c, s_start, count)
                print(f"✅ เพิ่มสำเร็จ {len(added)} คน")
            except ValueError as e:
                print(f"❌ {e}")

        elif choice == 3:
            print("\n--- ลบแขก ---")
            c = get_valid_int("รหัสช่องทาง (c >= 1): ", min_val=1)
            s = get_valid_int("ลำดับภายในช่องทาง (s >= 1): ", min_val=1)
            try:
                guest = system.remove_guest(c, s)
                print(f"✅ ลบแขก (c={c}, s={s}) จากห้อง {guest.node_id}-{guest.room_no} สำเร็จ")
            except ValueError as e:
                print(f"❌ {e}")

        elif choice == 4:
            print("\n--- เพิ่มอาคาร ---")
            name = input("ชื่อ/รหัสอาคารใหม่: ").strip()
            last_move_report = system.add_building(name)
            last_move_report.print_report()

        elif choice == 5:
            print("\n--- ลบอาคาร ---")
            name = input("ชื่อ/รหัสอาคารที่จะลบ: ").strip()
            last_move_report = system.remove_building(name)
            last_move_report.print_report()

        elif choice == 6:
            print("\n--- ค้นหาข้อมูล ---")
            print("  1. ค้นด้วยรหัสแขก (c, s)")
            print("  2. ค้นด้วยที่อยู่ห้อง (อาคาร, ห้อง)")
            sub_choice = get_valid_int("เลือก: ", min_val=1, max_val=2)
            
            if sub_choice == 1:
                c = get_valid_int("รหัสช่องทาง (c): ", min_val=1)
                s = get_valid_int("ลำดับ (s): ", min_val=1)
                res = system.lookup_by_guest(c, s)
                if res:
                    print(f"✅ พบ → อาคาร: {res[0]}, ห้อง: {res[1]}")
                else:
                    print("❌ ไม่พบข้อมูลแขก")
            else:
                node_id = input("รหัสอาคาร: ").strip()
                room_no = get_valid_int("หมายเลขห้อง: ", min_val=1)
                res = system.lookup_by_room(node_id, room_no) # O(1)ผ่านดัชนี
                if res:
                    print(f"✅ พบ → แขกรหัส (c={res[0]}, s={res[1]})")
                else:
                    print("❌ ไม่พบข้อมูลผู้เข้าพักในห้องนี้")

        elif choice == 7:
            print("\n--- รายการห้องที่มีผู้พัก ---")
            listing = system.guest_manager.get_all_occupied_rooms_sorted()
            total = len(listing)
            if total == 0:
                print("ยังไม่มีแขกในระบบ")
                continue

            max_show = 50
            current_building = None
            for idx, guest in enumerate(listing[:max_show]):
                if guest.node_id != current_building:
                    current_building = guest.node_id
                    print(f"\n  🏢 อาคาร {current_building}:")
                print(f"    ห้อง {guest.room_no:>6} → แขก (c={guest.c}, s={guest.s})")

            if total > max_show:
                print(f"\n... แสดงเพียง {max_show} รายการแรก จากทั้งหมด {total} รายการ (ส่งออก CSV เพื่อดูทั้งหมด)")

        elif choice == 8:
            print("\n--- สถิติความสมดุลของโหลด ---")
            stats = system.get_load_stats()
            print(f"  จำนวนอาคารทั้งหมด (N): {stats['num_buildings']}")
            print(f"  จำนวนแขกทั้งหมด (K): {stats['total_guests']}")
            print("  รายอาคาร:")
            for b, count in stats['per_node'].items():
                print(f"    - {b}: {count} คน")

            if stats["is_zero_k"]:
                print("  สถิติ: เฉลี่ย 0 | สูงสุด 0 | ต่ำสุด 0 | ส่วนเบี่ยงเบนมาตรฐาน 0.0000")
                print("  ค่าสัมประสิทธิ์การแปรผัน (CV): N/A (ไม่มีแขกในระบบ K = 0)")
            else:
                print(f"  แขกต่ออาคาร: เฉลี่ย {stats['mean']:.2f} | สูงสุด {stats['max']} | ต่ำสุด {stats['min']}")
                print(f"  ส่วนเบี่ยงเบนมาตรฐาน (Std): {stats['std']:.4f}")
                print(f"  ค่าสัมประสิทธิ์การแปรผัน (CV): {stats['cv']:.4f}")

        elif choice == 9:
            print("\n--- ส่งออก CSV ---")
            print("  1. ส่งออกรายการแขกปัจจุบัน")
            print("  2. ส่งออกรายการย้ายแขกจากคำสั่งล่าสุด")
            sub_c = get_valid_int("เลือก: ", min_val=1, max_val=2)
            
            if sub_c == 1:
                filename = input("ชื่อไฟล์ [guest_list.csv]: ").strip() or "guest_list.csv"
                system.export_guests_to_csv(filename)
            else:
                if not last_move_report or not last_move_report.moved_records:
                    print("⚠️ ไม่มีรายงานการย้ายล่าสุดที่มีแขกย้าย")
                else:
                    filename = input("ชื่อไฟล์ [move_report.csv]: ").strip() or "move_report.csv"
                    system.export_moves_to_csv(last_move_report, filename)

        elif choice == 10:
            print("\n--- เปรียบเทียบประสิทธิภาพ ---")
            print("กำลังรันทดลองการเปรียบเทียบและพล็อตกราฟ... อาจใช้เวลาสักครู่")
            from comparison import run_all_experiments
            from plot_results import generate_all_plots
            run_all_experiments()
            generate_all_plots()
            print("✅ ดำเนินการทดลองและสร้างรูปภาพกราฟทั้ง 3 ภาพ เรียบร้อยแล้ว!")

        input("\nกด Enter เพื่อดำเนินการต่อ...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ออกจากโปรแกรม")
        sys.exit(0)