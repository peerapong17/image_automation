import os
import json
import re
import pandas as pd
import csv
import google.generativeai as genai
from PIL import Image

# ตั้งค่า API Key สำหรับ Gemini
genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")

# ตั้งค่าโฟลเดอร์ที่มีรูปภาพ
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
output_csv_path = "output_metadata.csv"

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
            
            if keywords_part:
                keywords_list = [
                    kw.strip().lstrip("*:").replace("**", "").replace("Keywords:", "").strip()  
                    for kw in re.split(r",\s*|\n", keywords_part) if kw.strip()
                ]
                keywords_list = [kw for kw in keywords_list if len(kw.split()) <= 2]
            else:
                keywords_list = []
        else:
            description = text_response
            keywords_list = list(set(description.lower().split()))[:40]

        # สร้าง Title จากคำอธิบาย
        title = description

        # เก็บผลลัพธ์
        results.append({
            "Filename": image_name,
            "Title": title,
            "Description": description,
            "Keywords": ", ".join(keywords_list),
            "Category": "",
            "Release(s)": ""
        })

        print(f"✅ Processed: {image_name}")

    except Exception as e:
        print(f"❌ Error processing {image_name}: {e}")

# สร้าง DataFrame
df = pd.DataFrame(results)

# กำหนด custom formatter สำหรับการเขียน CSV
class CustomDialect(csv.excel):
    quoting = csv.QUOTE_NONE
    
# เขียนส่วนหัวก่อน
with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
    f.write('Filename,Title,Description,Keywords,Category,Release(s)\n')

# เขียนข้อมูลด้วย custom quoting
with open(output_csv_path, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
    for _, row in df.iterrows():
        writer.writerow(row)

print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")