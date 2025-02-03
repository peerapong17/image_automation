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
genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")
# genai.configure(api_key="AIzaSyAg_S0xTN67D_091F5VldfvqUFIQM3hZVM")

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

def clean_description(text):
    """
    Cleans description/title text by ensuring it ends with exactly one period.
    Removes any trailing punctuation and adds a single period.
    
    Args:
        text (str): The input description or title text
        
    Returns:
        str: Cleaned text ending with exactly one period
    """
    # First remove any trailing whitespace
    text = text.strip()
    
    # Remove any trailing punctuation (periods or commas)
    while text and text[-1] in '.,':
        text = text[:-1].strip()
    
    # Add a single peri

# วนลูปประมวลผลทุกภาพ
for image_name in image_files:
    image_path = os.path.join(image_folder, image_name)
    
    try:
        # โหลดภาพ
        image = Image.open(image_path)

        # ขอข้อมูลจาก Gemini
        response = model.generate_content([
            "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters."
            "Provide 35-50 related keywords, separated by commas. Exclude trademarked keywords. Prioritize essential or relevant keywords at the beginning. Avoid similar or redundant keywords.",
            image
        ])

        # response = model.generate_content([
        #     "Describe the image concisely, using 70-120 characters. Avoid repetitive phrases and trademarked words."
        #     "Provide 35-50 related keywords, separated by commas. Exclude trademarked keywords. Prioritize essential or relevant keywords at the beginning. Avoid similar or redundant keywords.",
        #     image
        # ])

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
            # description = re.sub(r"[.,]+$", ".", description)
            # description = re.sub(r"[.,]*\Z", "", description.strip()) + "."
            cleaned_description = clean_description(description)

            # ✅ แปลงให้นอกจากตัวแรกของประโยคแล้ว นอกนั้นเป็นตัวพิมพ์เล็ก
            description = cleaned_description.capitalize()

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
