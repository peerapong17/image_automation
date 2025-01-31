import google.generativeai as genai
from PIL import Image

# ตั้งค่า API Key
genai.configure(api_key="AIzaSyAg_S0xTN67D_091F5VldfvqUFIQM3hZVM")

# โหลดโมเดล
model = genai.GenerativeModel("gemini-1.5-pro")

# โหลดภาพ
image = Image.open("image_2.jpg")

# สร้างข้อความจากภาพ
response = model.generate_content([
    "Give a description for this image, using noun phrase, the description more than 70 characters. "
    "Give me related keywords for this image, more than 35 keywords, separate by comma.",
    image
])

# แยกคำตอบออกเป็นส่วนๆ
text_response = response.text

# ค้นหาส่วนที่เป็น Keywords
if "Keywords:" in text_response:
    keywords_part = text_response.split("Keywords:")[1].strip()
    keywords_list = [kw.strip() for kw in keywords_part.split(",")]
    print(keywords_list)  # ได้เป็นลิสต์ของ Keywords
    print(text_response)
else:
    print("No keywords found.")
