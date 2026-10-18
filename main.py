# ==================================================
# main.py — ส่วนติดต่อผู้ใช้ / เมนูหลัก
# ==================================================
import sys
from hotel_system import HotelSystem

def print_menu():
    print("\n" + "="*50)
    print("  🏨 ระบบโรงแรมกระจาย Distributed Hilbert Hotel")
    print("="*50)
    print("  1. เพิ่มแขกคนเดียว")
    print("  2. เพิ่มแขกเป็นกลุ่ม")
    print("  3. ลบแขก")
    print("  4. เพิ่มอาคาร")
    print("  5. ลบอาคาร")
    print("  6. ค้นหาข้อมูลแขก")
    print("  7. แสดงรายการห้องที่มีผู้พัก")
    print("  8. แสดงสถิติความสมดุลของโหลด")
    print("  9. ส่งออกข้อมูลเป็น CSV")
    print(" 10. เปรียบเทียบ Consistent Hashing vs Hash Mod N")
    print("  0. ออกจากโปรแกรม")
    print("="*50)

def get_valid_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = input(prompt).strip()
            if val == "":
                print("❌ กรุณาใส่ค่า")
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
            print("❌ ต้องป้อนจำนวนเต็มเท่านั้น")

def main():
    print("กำลังเริ่มระบบ...")
    
    N = get_valid_int("จำนวนอาคารเริ่มต้น: ", min_val=1)
    V = get_valid_int("จำนวนโหนดเสมือนต่ออาคาร (V): ", min_val=1)
    
    building_names = [f"Building_{i+1}" for i in range(N)]
    system = HotelSystem(building_names, V)
    print(f"✅ ระบบพร้อมใช้งาน — มี {N} อาคาร, V = {V}")

    while True:
        print_menu()
        choice = get_valid_int("เลือกทำงาน: ", min_val=0, max_val=10)

        if choice == 0:
            print("👋 ออกจากโปรแกรม...")
            break

        elif choice == 1:
            # เพิ่มแขกคนเดียว
            print("\n--- เพิ่มแขกคนเดียว ---")
            c = get_valid_int("รหัสช่องทาง (c): ", min_val=1)
            s = get_valid_int("ลำดับภายในช่องทาง (s): ", min_val=1)
            
            if (c, s) in system.guest_manager.guests:
                print(f"❌ มีแขก (c={c}, s={s}) ในระบบแล้ว")
                continue
            
            building_id = system.hash_ring.get_building_for_guest(c, s)
            try:
                guest = system.guest_manager.add_guest(c, s, building_id)
                print(f"✅ เพิ่มสำเร็จ → อาคาร: {guest.node_id}, ห้อง: {guest.room_no}")
            except ValueError as e:
                print(f"❌ {e}")

        elif choice == 2:
            # เพิ่มแขกเป็นกลุ่ม — ใช้เมธอด add_guest_group ที่มีอยู่
            print("\n--- เพิ่มแขกเป็นกลุ่ม ---")
            c = get_valid_int("รหัสช่องทาง (c): ", min_val=1)
            s_start = get_valid_int("ลำดับเริ่มต้น (s): ", min_val=1)
            count = get_valid_int("จำนวน: ", min_val=1)
            
            get_node_func = lambda c_val, s_val: system.hash_ring.get_building_for_guest(c_val, s_val)
            try:
                added = system.guest_manager.add_guest_group(c, s_start, count, get_node_func)
                print(f"✅ เพิ่มสำเร็จ {len(added)} คน")
            except ValueError as e:
                print(f"❌ {e}")

        elif choice == 3:
            # ลบแขก
            print("\n--- ลบแขก ---")
            c = get_valid_int("รหัสช่องทาง (c): ", min_val=1)
            s = get_valid_int("ลำดับภายในช่องทาง (s): ", min_val=1)
            
            try:
                system.guest_manager.remove_guest(c, s)
                print(f"✅ ลบ (c={c}, s={s}) สำเร็จ")
            except ValueError as e:
                print(f"❌ {e}")

        elif choice == 4:
            # เพิ่มอาคาร
            print("\n--- เพิ่มอาคาร ---")
            name = input("ชื่อ/รหัสอาคารใหม่: ").strip()
            report = system.add_building(name)
            report.print_report()

        elif choice == 5:
            # ลบอาคาร
            print("\n--- ลบอาคาร ---")
            name = input("ชื่อ/รหัสอาคารที่จะลบ: ").strip()
            report = system.remove_building(name)
            report.print_report()

        elif choice == 6:
            # ค้นหา
            print("\n--- ค้นหาข้อมูล ---")
            print("  1. ค้นด้วยรหัสแขก (c, s)")
            print("  2. ค้นด้วยที่อยู่ห้อง (อาคาร, ห้อง)")
            sub_choice = get_valid_int("เลือก: ", min_val=1, max_val=2)
            
            if sub_choice == 1:
                c = get_valid_int("รหัสช่องทาง (c): ", min_val=1)
                s = get_valid_int("ลำดับ (s): ", min_val=1)
                guest = system.guest_manager.guests.get((c, s))
                if guest:
                    print(f"✅ พบ → อาคาร: {guest.node_id}, ห้อง: {guest.room_no}")
                else:
                    print("❌ ไม่พบข้อมูล")
            else:
                node_id = input("รหัสอาคาร: ").strip()
                room_no = get_valid_int("หมายเลขห้อง: ", min_val=1)
                found = None
                for guest in system.guest_manager.guests.values():
                    if guest.node_id == node_id and guest.room_no == room_no:
                        found = guest
                        break
                if found:
                    print(f"✅ พบ → แขก (c={found.c}, s={found.s})")
                else:
                    print("❌ ไม่พบข้อมูล")

        elif choice == 7:
            # แสดงรายการห้อง
            print("\n--- รายการห้องที่มีผู้พัก ---")
            listing = system.guest_manager.get_all_occupied_rooms_sorted()
            if not listing:
                print("ยังไม่มีแขกในระบบ")
                continue
            current_building = None
            for guest in listing:
                if guest.node_id != current_building:
                    current_building = guest.node_id
                    print(f"\n  {current_building}:")
                print(f"    ห้อง {guest.room_no:>6} → แขก (c={guest.c}, s={guest.s})")

        elif choice == 8:
            # สถิติ
            print("\n--- สถิติความสมดุลของโหลด ---")
            total_guests = system.guest_manager.total_guests
            buildings = system.hash_ring.buildings
            per_node = {}
            for b in buildings:
                cnt = sum(1 for g in system.guest_manager.guests.values() if g.node_id == b)
                per_node[b] = cnt
            
            if total_guests == 0:
                print(f"  จำนวนอาคารทั้งหมด: {len(buildings)}")
                print("  ยังไม่มีแขกในระบบ")
                continue
            
            vals = list(per_node.values())
            mean = total_guests / len(buildings)
            variance = sum((x - mean) ** 2 for x in vals) / len(vals)
            std = variance ** 0.5
            cv = std / mean if mean > 0 else 0
            
            print(f"  จำนวนอาคารทั้งหมด: {len(buildings)}")
            print(f"  จำนวนแขกทั้งหมด: {total_guests}")
            print(f"  แขกต่ออาคาร: เฉลี่ย {mean:.2f} | สูงสุด {max(vals)} | ต่ำสุด {min(vals)}")
            print(f"  ส่วนเบี่ยงเบนมาตรฐาน: {std:.4f}")
            print(f"  ค่าสัมประสิทธิ์การแปรผัน (CV): {cv:.4f}")
            print("  รายอาคาร:")
            for b in sorted(per_node.keys()):
                print(f"    {b}: {per_node[b]} คน")

        elif choice == 9:
            # ส่งออก CSV
            filename = input("ชื่อไฟล์ (กด Enter ใช้ชื่อเริ่มต้น): ").strip()
            if not filename:
                filename = "guest_list.csv"
            ok = system.export_guests_to_csv(filename)
            if ok:
                print(f"✅ ส่งออกสำเร็จ → {filename}")
            else:
                print(f"❌ ส่งออกไม่สำเร็จ")

        elif choice == 10:
            # เปรียบเทียบ
            print("\n--- เปรียบเทียบประสิทธิภาพ ---")
            print("กำลังรันทดลอง... อาจใช้เวลาสักครู่")
            from comparison import run_all_experiments
            run_all_experiments()
            print("✅ เสร็จสิ้น! ดูผลที่ experiment_results.csv")

        input("\nกด Enter เพื่อดำเนินต่อไป...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ออกจากโปรแกรม")
        sys.exit(0)