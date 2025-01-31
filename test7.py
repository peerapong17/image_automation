import os
import json
import re
import pandas as pd
import csv
import google.generativeai as genai
from PIL import Image

# ตั้งค่า API Key สำหรับ Gemini
genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")  # แทนที่ด้วย API Key ของคุณ

# ตั้งค่าโฟลเดอร์ที่มีรูปภาพ
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"  # เปลี่ยนเป็น path ของคุณ
output_csv_path = "output_metadata.csv"  # ไฟล์ CSV ที่ใช้บันทึกผลลัพธ์

# โหลดโมเดล Gemini
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# ค้นหาไฟล์รูปภาพทั้งหมด
image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

# สร้างลิสต์เก็บผลลัพธ์
results = []

# วนลูปประมวลผลทุกภาพ
for image_name in image_files:
    image_path = os.path.join(image_folder, image_name)
    
    try:
        # โหลดภาพ
        image = Image.open(image_path)

        # ขอข้อมูลจาก Gemini
        response = model.generate_content([
            "Give a description for this image, using noun phrase, the description more than 70 characters, but no more than 200 characters."
            "Give me related keywords for this image, more than 35 keywords, separate by comma.",
            image
        ])

        text_response = response.text.strip()

        # ใช้ regex แยก description และ keywords
        match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)

        if match:
            description = match.group(1).strip()
            keywords_part = match.group(2).strip()
            
            # แยก keywords และทำความสะอาดข้อมูล
            if keywords_part:
                keywords_list = [
                    kw.strip().lstrip("*:").replace("**", "").replace("Keywords:", "").strip()  
                    for kw in re.split(r",\s*|\n", keywords_part) if kw.strip()
                ]
                
                # ลบคีย์เวิร์ดที่มีมากกว่า 2 คำ
                keywords_list = [kw for kw in keywords_list if len(kw.split()) <= 2]
            else:
                keywords_list = []
        else:
            # ถ้าไม่มี "Keywords:" ให้ใช้คำอธิบายสร้างคีย์เวิร์ดแทน
            description = text_response
            keywords_list = list(set(description.lower().split()))[:40]  # ดึงคีย์เวิร์ดจากคำอธิบาย

        # สร้าง Title จากคำอธิบายโดยเอาประโยคแรกสุด
        title = description.split(",")[0].strip()

        # แปลงชื่อไฟล์เป็น "_upscaled.jpeg" ตามฟอร์แมตที่ต้องการ
        formatted_filename = image_name.replace(".jpg", "_upscaled.jpeg").replace(".png", "_upscaled.jpeg").replace(".jpeg", "_upscaled.jpeg")

        # เก็บผลลัพธ์
        results.append([
            formatted_filename,  # ✅ Filename ครอบด้วย ""
            title,  # ✅ Title ไม่มี ""
            description,  # ✅ Description ครอบด้วย ""
            ", ".join(keywords_list),  # ✅ Keywords ครอบด้วย ""
            "",  # ✅ Category ครอบด้วย ""
            ""   # ✅ Release(s) ครอบด้วย ""
        ])

        print(f"✅ Processed: {image_name}")

    except Exception as e:
        print(f"❌ Error processing {image_name}: {e}")

# ✅ เขียนไฟล์ CSV เอง เพื่อควบคุมการครอบ " "
with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)  # ใช้ QUOTE_ALL เพื่อให้ทุกช่องมี "" ยกเว้น Title
    writer.writerow(["Filename", "Title", "Description", "Keywords", "Category", "Release(s)"])  # Header
    writer.writerows(results)

print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")
