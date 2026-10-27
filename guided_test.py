import sys
from hotel_system import HotelSystem
from data_generator import generate_guests
from comparison import run_all_experiments

def run_guided_tests():
    print("="*60)
    print(" 🧪 GUIDED TEST SUITE (ชุดการทดสอบระบบ 1 ถึง 8)")
    print("="*60)

    # Test 1: Cantor Pairing & Basic Check-in
    print("\n[Test 1] 📥 ทดสอบ Cantor Pairing และการเช็กอินแขกเดี่ยว")
    hotel = HotelSystem(num_buildings=3, num_vnodes=50)
    c1 = hotel.check_in("GUEST_WEB_000001")
    c2 = hotel.check_in("GUEST_APP_000002")
    print(f"  ✅ GUEST_WEB_000001 ได้ Cantor Room: {c1}")
    print(f"  ✅ GUEST_APP_000002 ได้ Cantor Room: {c2}")

    # Test 2: Bulk Check-in
    print("\n[Test 2] 📦 ทดสอบเช็กอินกลุ่มแขกสุ่ม 1,000 คน")
    guests = generate_guests(1000)
    for g in guests:
        hotel.check_in(g)
    print(f"  ✅ เช็กอินสำเร็จ! จำนวนแขกในระบบปัจจุบัน: {len(hotel.guest_manager.guest_to_room)} คน")

    # Test 3: Add Building & Rebalance
    print("\n[Test 3] 🏢 ทดสอบการเพิ่มอาคารโรงแรม (Building 4)")
    report_add = hotel.add_building()
    print(f"  ✅ จำนวนย้ายห้อง: {report_add['migrated_count']} คน ({report_add['migration_rate']*100:.2f}%)")

    # Test 4: Remove Building & Rebalance
    print("\n[Test 4] 🗑️  ทดสอบการลบอาคารโรงแรม (Building 1)")
    report_del = hotel.remove_building(1)
    print(f"  ✅ จำนวนย้ายห้อง: {report_del['migrated_count']} คน ({report_del['migration_rate']*100:.2f}%)")

    # Test 5: Edge Cases
    print("\n[Test 5] ⚠️  ทดสอบกรณีขอบ (Edge Case: ห้ามลบอาคารสุดท้าย)")
    try:
        temp_hotel = HotelSystem(num_buildings=1)
        temp_hotel.remove_building(1)
    except ValueError as e:
        print(f"  ✅ ระบบป้องกันถูกต้อง: {e}")

    # Test 6: Load Balance Stats
    print("\n[Test 6] 📊 ทดสอบคำนวณสถิติโหลดและค่า CV")
    stats = hotel.get_load_stats()
    print(f"  ✅ Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}, CV: {stats['cv']:.4f}")

    # Test 7: Export Guest List CSV
    print("\n[Test 7] 📄 ทดสอบส่งออกไฟล์ guest_list.csv")
    hotel.export_guest_list("guest_list.csv")
    print("  ✅ บันทึกไฟล์ guest_list.csv สำเร็จแล้ว")

    # Test 8: Run Benchmarks and Update experiment_results.csv
    print("\n[Test 8] 🚀 รันทดลองวัดประสิทธิภาพเพื่ออัปเดต experiment_results.csv")
    run_all_experiments()

    print("\n" + "="*60)
    print(" 🎉 รันชุดการทดสอบครบทั้ง 8 ข้อเรียบร้อยแล้ว! ไฟล์ CSV ทั้งหมดถูกอัปเดตแล้ว")
    print("="*60)

if __name__ == "__main__":
    run_guided_tests()