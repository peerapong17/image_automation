import google.generativeai as genai
from PIL import Image
import os

# ตั้งค่า API key
genai.configure(api_key="AIzaSyAg_S0xTN67D_091F5VldfvqUFIQM3hZVM")  # เปลี่ยนเป็น API Key ของคุณ

# เลือกโมเดลที่ต้องการใช้
model = genai.GenerativeModel("gemini-1.5-pro")

# โฟลเดอร์ที่เก็บรูปภาพ
image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"  # เปลี่ยนเป็นที่อยู่ของโฟลเดอร์รูปภาพ

# ดึงรายชื่อไฟล์ทั้งหมดในโฟลเดอร์
image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# วนลูปประมวลผลทุกภาพ
for image_file in image_files:
    image_path = os.path.join(image_folder, image_file)
    
    try:
        image = Image.open(image_path)  # โหลดรูปภาพ

        # ส่งภาพไปยังโมเดล
        response = model.generate_content([
            "Give a description for this image, using noun phrase, the description more than 70 characters. "
            "Give me related keywords for this image, more than 35 keywords, separate by comma.",
            image
        ])

        print(f"Image: {image_file}")
        print(response.text)  # แสดงผลลัพธ์
        print(response.text["Keywords"])
        print("-" * 50)

    except Exception as e:
        print(f"Error processing {image_file}: {e}")
