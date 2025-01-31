import os
import google.generativeai as genai
from PIL import Image
import csv

# ตั้งค่า Google Gemini API
genai.configure(api_key="YOUR_API_KEY")  # เปลี่ยนเป็น API Key ของคุณ

# ใช้โมเดล Gemini (แนะนำใช้ gemini-1.5-pro หรือ gemini-1.5-flash)
model = genai.GenerativeModel("gemini-1.5-flash")

# กำหนดโฟลเดอร์ที่มีภาพทั้งหมด
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"  # เปลี่ยนเป็นพาธของคุณ
output_csv = "image_descriptions.csv"  # ไฟล์ CSV ที่จะบันทึกผลลัพธ์

# ค้นหาไฟล์รูปภาพในโฟลเดอร์
image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

print(image_files)
# ตรวจสอบว่ามีภาพหรือไม่
if not image_files:
    print("ไม่พบไฟล์รูปภาพในโฟลเดอร์")
    exit()

# เปิดไฟล์ CSV เพื่อบันทึกข้อมูล
with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Image", "Description", "Keywords"])  # หัวข้อของตาราง

    # วนลูปผ่านไฟล์รูปภาพทั้งหมด
    for image_name in image_files:
        image_path = os.path.join(image_folder, image_name)

        try:
            # โหลดภาพ
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()

            # ส่งภาพไปยัง Google Gemini API
            response = model.generate_content([
                "Give a description for this image, using noun phrase, the description more than 50 characters."
                "Give me related keywords for this image, more than 35 keywords, separate by comma.",
                image_bytes
            ])

            # แยกคำตอบจาก Gemini
            output_text = response.text.strip()  # ตัดช่องว่างหน้า-หลัง
            parts = output_text.split("\n")

            description = parts[0] if len(parts) > 0 else "No description"
            keywords = parts[1] if len(parts) > 1 else "No keywords"

            # พิมพ์ผลลัพธ์ออกมาก่อน
            print(f"\n📷 **Image:** {image_name}")
            print(f"📝 **Description:** {description}")
            print(f"🔑 **Keywords:** {keywords}\n")

            # บันทึกข้อมูลลง CSV
            writer.writerow([image_name, description, keywords])

            print(f"✔ ประมวลผล: {image_name}")  # แสดงความคืบหน้า

        except Exception as e:
            print(f"❌ ไม่สามารถประมวลผล {image_name}: {e}")

print(f"\n✅ เสร็จสิ้น! คำอธิบายและคีย์เวิร์ดถูกบันทึกที่ {output_csv}")
