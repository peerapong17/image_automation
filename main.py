import os
import csv
import re
import pandas as pd
import emoji
from PIL import Image
import google.generativeai as genai

def clean_text(text):
    """Ensures text ends with exactly one period and removes trailing misplaced words."""
    text = text.strip()
    
    # ลบคำสุดท้ายที่ดูเหมือนห้อยท้ายผิดพลาด
    text = re.sub(r'\s+\b\w+\b[.,]?$', '', text, flags=re.IGNORECASE).strip()

    while text and text[-1] in '.,':
        text = text[:-1].strip()

    return text + "."  # คืนค่า description ที่ถูกล้างแล้ว

def clean_keywords(keywords):
    """Removes trailing period from the last keyword in the list."""
    keywords = keywords.strip()
    if keywords.endswith('.'):
        keywords = keywords[:-1].strip()
    return keywords

def remove_uncertainty_words(text):
    """Remove uncertainty words while preserving spaces."""
    uncertainty_words = [
        'maybe', 'perhaps', 'likely', 'potentially', 'probably', 
        'presumably', 'conceivably', 'perchance', 'feasibly', 
        'seemingly', 'ostensibly', 'supposedly', 'reportedly',
        'apparently', 'arguably', 'hypothetically', 'allegedly',
        'theoretically', 'speculatively', 'purportedly', 'possibly'
    ]
    
    for word in uncertainty_words:
        text = re.sub(r'\b' + word + r'\b', '', text, flags=re.IGNORECASE)

    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def remove_emojis(text):
    """Remove emojis from text."""
    return emoji.replace_emoji(text, replace='')

def process_gemini_response(text_response):
    """Process Gemini API response to separate description and keywords."""
    print("Original response:", text_response)

    # ตรวจจับข้อความผิดปกติจาก AI (กันกรณีที่ไม่ใช่ข้อมูลจริง)
    if text_response.lower().startswith("here's") or "description and keywords" in text_response.lower():
        print("⚠️ AI response is invalid. Skipping this image.")
        return None, None

    # กรณีที่มีโครงสร้าง "Description:" และ "Keywords:"
    match = re.search(r"(?:Description:)?\s*(.*?)\s*(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)
    if match:
        description = match.group(1).strip()
        description = clean_text(remove_uncertainty_words(description))  # ลบคำที่ห้อยท้าย
        
        keywords = match.group(2).strip()
        keywords_list = [
            remove_uncertainty_words(remove_emojis(kw.strip()))
            for kw in re.split(r",\s*", keywords)
            if kw.strip() and len(kw.split()) <= 2 and not kw.endswith('.')
        ][:50]

        return description, keywords_list
    
    # กรณีที่ไม่มี "Description:" และ "Keywords:"
    parts = text_response.strip().split(',')
    
    description_parts = []
    keyword_parts = []
    found_sentence = False

    for part in parts:
        part = part.strip()
        if not found_sentence:
            description_parts.append(part)
            if re.search(r'[.!?]', part) or len(part) > 50:  # ถ้าพบประโยคสมบูรณ์
                found_sentence = True
                continue
        else:
            if part:
                keyword_parts.append(part)

    description = ', '.join(description_parts)
    description = clean_text(remove_uncertainty_words(description))  # ลบคำที่ห้อยท้าย
    
    keywords_list = []
    for kw in keyword_parts:
        kw = re.sub(r'[.!?,]', '', kw).strip()
        kw = remove_uncertainty_words(remove_emojis(kw))
        if kw and len(kw.split()) <= 2:
            keywords_list.append(kw)
    
    keywords_list = list(dict.fromkeys(keywords_list))[:50]

    print("Processed description:", description)
    print("Processed keywords:", keywords_list)
    
    return description, keywords_list

def main():
    # ตั้งค่า API Key สำหรับ Gemini
    genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")
    
    image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    results = []
    
    prompt = (
        "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters. "
        "Provide 35-50 related keywords, separated by commas. Prioritize essential or relevant keywords at the beginning."
    )    

    for image_name in image_files:
        try:
            image_path = os.path.join(image_folder, image_name)
            image = Image.open(image_path)
            
            response = model.generate_content([prompt, image])
            print(response.usage_metadata)
            
            description, keywords_list = process_gemini_response(response.text.strip())

            # ถ้า response ผิดปกติ ให้ข้ามไฟล์นั้น
            if description is None or keywords_list is None:
                continue
            
            results.append({
                "Filename": image_name,
                "Title": description,
                "Description": description,
                "Keywords": clean_keywords(", ".join(keywords_list)).lower(),
                "Category": "",
                "Release(s)": ""
            })
            
            print(f"✅ Processed: {image_name}")
            
        except Exception as e:
            print(f"❌ Error processing {image_name}: {e}")
    
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write('Filename,Title,Description,Keywords,Category,Release(s)\n')
    
    df = pd.DataFrame(results)
    with open(output_csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
        for _, row in df.iterrows():
            writer.writerow(row)
            
    print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")

if __name__ == "__main__":
    main()
