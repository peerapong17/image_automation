import os
import json
import re
import pandas as pd
import csv  # ✅ ต้องใช้เพื่อจัดการ " " ใน CSV
import google.generativeai as genai
from PIL import Image

# ตั้งค่า API Key สำหรับ Gemini
genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")  # แทนที่ด้วย API Key ของคุณ

# ตั้งค่าโฟลเดอร์ที่มีรูปภาพ
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"  # เปลี่ยนเป็น path ของคุณ
output_csv_path = "output_metadata.csv"  # ไฟล์ CSV ที่ใช้บันทึกผลลัพธ์

# โหลดโมเดล Gemini
model = genai.GenerativeModel("gemini-1.5-pro")

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
            "Give a detailed noun phrase description of this image, ensuring it is more than 70 characters.",
            "Generate at least 35 related keywords for this image. Each keyword must be a single word or a two-word phrase. Do not include phrases longer than two words. Separate keywords by commas.",
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
        results.append({
            "Filename": formatted_filename,
            "Title": description,
            "Description": description,
            "Keywords": ", ".join(keywords_list),
            "Category": "",  # เว้นว่างตามตัวอย่าง
            "Release(s)": ""  # เว้นว่างตามตัวอย่าง
        })

        print(f"✅ Processed: {image_name}")

    except Exception as e:
        print(f"❌ Error processing {image_name}: {e}")

# แปลงเป็น DataFrame
df_results = pd.DataFrame(results)

# บันทึกเป็นไฟล์ CSV พร้อม " " ครอบทุกช่อง
df_results.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_ALL, escapechar='\\')

print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")
