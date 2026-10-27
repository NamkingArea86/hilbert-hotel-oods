# 🏨 Distributed Hilbert Hotel — ระบบจัดการโรงแรมอนันต์แบบกระจาย

โปรแกรมจัดการแขกเข้าพักในเครือโรงแรมหลายอาคารด้วยเทคนิค **Consistent Hashing** บนวงแหวนขนาด 64 บิต เปรียบเทียบประสิทธิภาพกับวิธี **Hash Mod N** พร้อมการวิเคราะห์ Big-O และสถิติโหลด

## 📋 สมาชิกในกลุ่มและหน้าที่รับผิดชอบ
| ลำดับ | ชื่อ - นามสกุล | รหัสนักศึกษา | หน้าที่รับผิดชอบ |
|---|---|---|---|
| 1 | นายเศรษฐพงศ์ ขอดี | 68011111 | `common.py` — ฟังก์ชันแฮช SHA-256 64-bit และสูตร Cantor Pairing |
| 2 | นางสาวณัฐกฤตา ลิ้มธีระวัฒน์ | 68010324 | `hash_ring.py`, `hotel_system.py` — วงแหวนแฮช, การย้ายแขก และรายงาน |
| 3 | นายณัฐวัฒน์ อุปันโน | 68011690 | `guest_manager.py` — จัดการข้อมูลแขกและดัชนีห้องพัก |
| 4 | นางสาวลักษยา ยันต์สำโรง | 68010960 | `comparison.py`, `plot_results.py`, `main.py` — การทดลอง กราฟ และ UI |

## 📁 โครงสร้างไฟล์ในโปรเจกต์
```text
hilbert-hotel-oods/
├── common.py              # SHA-256 (64 บิต) และ Cantor Pairing Function
├── hash_ring.py           # Consistent Hashing + Virtual Nodes + bisect
├── guest_manager.py       # จัดการแขก + room_to_guest index
├── hotel_system.py        # HotelSystem + MoveReport + export_csv
├── data_generator.py      # สร้างชุดข้อมูลแขก 10 ช่องทาง
├── comparison.py          # เปรียบเทียบ CH vs Hash Mod N
├── plot_results.py        # สร้างรูปกราฟ 3 ภาพ (chart_a, chart_b, chart_c)
├── test_hash_ring.py      # สคริปต์ Unit Test อัตโนมัติ
├── main.py                # เมนูการใช้งานระบบ (CLI Menu)
├── requirements.txt       # ไบรารีภายนอกที่ต้องใช้ (numpy, matplotlib)
├── guest_list.csv         # ไฟล์ส่งออกรายการแขกปัจจุบัน
├── move_report.csv        # ไฟล์ส่งออกรายการย้ายแขก
└── experiment_results.csv # ผลการทดลองวัดประสิทธิภาพ

วิธีการติดตั้งและใช้งาน
1. ติดตั้ง Dependencies
เปิด Terminal ในโฟลเดอร์โปรเจกต์ แล้วติดตั้งไลบรารีภายนอกที่ต้องใช้งาน:
pip install -r requirements.txt

2. การรันระบบหลัก (Interactive CLI)
สำหรับใช้งานระบบโรงแรมแบบเมนูตอบโต้ (เช็กอินแขก, เพิ่ม/ลบอาคาร, ดูสถิติโหลด, ส่งออก CSV):
python main.py

3. การรันชุดทดสอบระบบ (Guided Test Suite 1–8)
สำหรับทดสอบความถูกต้องของระบบตามโจทย์ทั้ง 8 ข้อ พร้อมอัปเดตไฟล์ CSV:
python guided_test.py

4. การรันทดลองและวาดกราฟวัดประสิทธิภาพ
สำหรับทดสอบ Benchmark สวีปค่าตัวแปร K, N, V และสร้างภาพกราฟสรุปผล:
1. รันทดลองเพื่อเก็บข้อมูลลงไฟล์ experiment_results.csv
python comparison.py

2. สร้างไฟล์รูปภาพกราฟทั้ง 3 ภาพ (chart_a, chart_b, chart_c)
python plot_results.py

5. การรัน Unit Test อัตโนมัติสำหรับทดสอบความถูกต้องของโครงสร้าง Hash Ring:Bashpython test_hash_ring.py