import os
import csv
import re
import pandas as pd
import emoji
from PIL import Image
import google.generativeai as genai

def main():
    # ตั้งค่า API Key สำหรับ Gemini
    genai.configure(api_key="AIzaSyCcUKq4ygHQwHi_h7CJBctK_VaJQWrdzCI")
    
    image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = (
        "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters. Avoid redundant phrases." 
        "Provide 35-50 related keywords, separated by commas. Prioritize essential or relevant keywords at the beginning. Avoid similar or redundant keyword."
    )   
    
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    for image_name in image_files:
        image_path = os.path.join(image_folder, image_name)
        image = Image.open(image_path)

        response = model.generate_content([prompt, image])

        print(response.usage_metadata)            
        # print(model.count_tokens(image))
        # print(model.count_tokens("https://drive.google.com/drive/u/0/my-drive"))

if __name__ == "__main__":
    main()