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
        # response = model.generate_content([
        #     "Describe the image with a noun phrase, between 70 and 180 characters."
        #     "Provide 35-50 related keywords, separated by commas.",
        #     image
        # ])

        # response = model.generate_content([
        #     "Give a description for this image, using noun phrase, description should be more than 80 characters"
        #     "Provide 35-50 related keywords, separated by commas.",
        #     image
        # ])

        # response = model.generate_content([
        #     "Describe the image, separated by comma, description should be more than 70 characters, but no more than 150 characters."
        #     "Provide 35-50 related keywords, separated by commas.",
        #     image
        # ])

        response = model.generate_content([
            "Describe the image, separated by comma, description should be more than 70 characters, but no more than 150 characters. Exclude trademarked word. "
            "Provide 35-50 related keywords, separated by commas. Exclude trademarked keywords. Prioritize essential or relevant keywords at the beginning.",
            image
        ])

        # response = model.generate_content([
        #     "Clearly describe the image using noun phrases, with a description exceeding 80 characters."
        #     "Provide 35-50 related keywords, separated by commas.",
        #     image
        # ])

        # response = model.generate_content([
        #     "Describe the image, using noun phrase, with a description exceeding 80 characters."
        #     "Provide 35-50 related keywords, separated by commas.",
        #     image
        # ])

        text_response = response.text.strip()

        print(text_response)

        # ใช้ regex แยก description และ keywords
        match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)

        if match:
            description = match.group(1).strip()
            keywords_part = match.group(2).strip()

            # ✅ ลบ "**Description:**" และ "**" ที่อาจติดมาใน description
            description = re.sub(r"^\*\*Description:\*\*\s*|\*\*", "", description).strip()

            # ✅ ถ้า description ไม่มี "." ให้เพิ่มเข้าไป
            if not description.endswith("."):
                description += "."

            if keywords_part:
                keywords_list = [
                    kw.strip().lstrip("*:").replace("**", "").replace("Keywords:", "").strip().lower()  
                    for kw in re.split(r",\s*|\n", keywords_part) if kw.strip()
                ]
                
                # ลบคีย์เวิร์ดที่มีมากกว่า 2 คำ
                keywords_list = [kw.lower() for kw in keywords_list if len(kw.split()) <= 2]

                # ลบจุด "." ท้ายคีย์เวิร์ดสุดท้ายถ้ามี
                if keywords_list and keywords_list[-1].endswith('.'):
                    keywords_list[-1] = keywords_list[-1][:-1]
            else:
                keywords_list = []
        else:
            description = text_response

            # ✅ ลบ "**Description:**" และ "**" ที่อาจติดมาใน description
            description = re.sub(r"^\*\*Description:\*\*\s*|\*\*", "", description).strip()

            # ✅ ถ้า description ไม่มี "." ให้เพิ่มเข้าไป
            if not description.endswith("."):
                description += "."

            keywords_list = list(set(description.lower().split()))[:40]

        # ✅ ลบ "**" ที่อาจติดมาใน title
        description = re.sub(r"^\*\*", "", description).strip()
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