import google.generativeai as genai
from PIL import Image

genai.configure(api_key="AIzaSyAg_S0xTN67D_091F5VldfvqUFIQM3hZVM")

model = genai.GenerativeModel("gemini-2.0-flash-exp")

# โหลดภาพ
image = Image.open("image_5.jpg")

response = model.generate_content([
    "Give a description for this image, using noun phrase, keep the description within 150 characters.",
    image
])

print(response.text)
