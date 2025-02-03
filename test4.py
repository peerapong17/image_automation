import os
import json
import re
import google.generativeai as genai
from PIL import Image

# ตั้งค่า API Key
genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")

# ตั้งค่าโฟลเดอร์ที่มีรูปภาพ
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"  # เปลี่ยนเป็น path ของคุณ
output_file = "output_results.json"  # ไฟล์ที่ใช้บันทึกผลลัพธ์

# โหลดโมเดล
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
            "Give a description for this image, using noun phrase, the description more than 70 characters. "
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
            else:
                keywords_list = []
        else:
            # ถ้าไม่มี "Keywords:" ให้ใช้คำอธิบายสร้างคีย์เวิร์ดแทน
            description = text_response
            keywords_list = list(set(description.lower().split()))[:40]  # ดึงคีย์เวิร์ดจากคำอธิบาย

        # เก็บผลลัพธ์
        results.append({
            "image": image_name,
            "description": description,
            "keywords": keywords_list
        })

        print(f"✅ Processed: {image_name}")

    except Exception as e:
        print(f"❌ Error processing {image_name}: {e}")

# บันทึกผลลัพธ์เป็น JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Finished processing all images. Results saved to {output_file}")
