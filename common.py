import hashlib

HASH_MAX = 2 ** 64  # ค่าสูงสุดของตำแหน่งบนแหวน 64-bit (0 ถึง 2^64 - 1)

def hash_to_64bit(text: str, salt: str = "") -> int:
    """
    แปลงข้อความ (และ salt) เป็นตำแหน่ง 64 บิตบนแหวน (0 ถึง 2^64 - 1)
    ใช้ SHA-256 ตัด 16 หลักแรกในรูป Hex (64 บิต) แล้วแปลงเป็น int
    ค่าคงที่เสมอข้ามการเปิด-ปิดโปรแกรม
    """
    combined = f"{salt}:{text}" if salt else text
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)

def compute_room_number(c: int, s: int) -> int:
    """
    คำนวณหมายเลขห้องด้วย Cantor Pairing Function
    แปลง c, s (จำนวนเต็มบวก >= 1) เป็น a = c - 1, b = s - 1
    คืนค่าหมายเลขห้องที่ไม่ซ้ำสำหรับแต่ละคู่ (c, s)
    """
    if c < 1 or s < 1:
        raise ValueError("Channel ID (c) และ Sequence ID (s) ต้องเป็นจำนวนเต็มบวก (>= 1)")
    a = c - 1
    b = s - 1
    return (a + b) * (a + b + 1) // 2 + b + 1