import os
import json
import re
import pandas as pd
import csv
import google.generativeai as genai
from PIL import Image

# ตั้งค่า API Key สำหรับ Gemini
# genai.configure(api_key="AIzaSyCcUKq4ygHQwHi_h7CJBctK_VaJQWrdzCI")

# free api key
# genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")
genai.configure(api_key="AIzaSyAg_S0xTN67D_091F5VldfvqUFIQM3hZVM")

# ตั้งค่าโฟลเดอร์ที่มีรูปภาพ
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
output_csv_path = "output_metadata.csv"

# โหลดโมเดล Gemini
model = genai.GenerativeModel("gemini-1.5-pro")
# model = genai.GenerativeModel("gemini-2.0-flash-exp")

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
            "Describe the image, separated by comma, description should be more than 70 characters, but no more than 150 characters. Exclude trademarked words. "
            "Provide 35-50 related keywords, separated by commas. Exclude trademarked keywords. Prioritize essential or relevant keywords at the beginning.",
            image
        ])

        text_response = response.text.strip()
        print(text_response)

        # ใช้ regex แยก description และ keywords
        match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)

        if match:
            description = match.group(1).strip()
            keywords_part = match.group(2).strip()

            # ✅ ลบเครื่องหมายที่อาจติดมาใน description
            description = re.sub(r"^\*\*Description:\*\*\s*|\*\*", "", description).strip()

            # ✅ ถ้า description ไม่มีจุด ลงท้าย ให้เพิ่มเข้าไป
            description = re.sub(r"[.,]+$", ".", description)

            if keywords_part:
                keywords_list = [
                    kw.strip().lstrip("*:").replace("**", "").replace("Keywords:", "").strip().lower()  
                    for kw in re.split(r",\s*|\n", keywords_part) if kw.strip()
                ]
                
                # ✅ ลบคีย์เวิร์ดที่มีมากกว่า 2 คำ
                keywords_list = [kw for kw in keywords_list if len(kw.split()) <= 2]

                # ✅ จำกัดจำนวน Keywords ไม่เกิน 50 คำ
                keywords_list = keywords_list[:50]
            else:
                keywords_list = []
        else:
            description = text_response.strip()
            description = re.sub(r"^\*\*Description:\*\*\s*|\*\*", "", description).strip()
            description = re.sub(r"[.,]+$", ".", description)
            keywords_list = list(set(description.lower().split()))[:50]

        # ✅ สร้าง Title จาก Description
        title = description

        # ✅ เก็บผลลัพธ์
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
output_df = pd.DataFrame(results)

# บันทึก CSV
output_df.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_ALL)

print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")
