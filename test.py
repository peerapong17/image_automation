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
    
    # ลบคำที่ไม่สมเหตุสมผลที่อาจหลงเหลือท้าย description
    text = re.sub(r'\s+\b(?:dog|corgi|puppy|canine)\b[.,]?$', '', text, flags=re.IGNORECASE).strip()
    
    while text and text[-1] in '.,':
        text = text[:-1].strip()
    
    return text + "."

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

def extract_main_subject(description):
    """Extract the first mentioned noun (main subject) from the description."""
    words = description.split()
    first_noun = None

    for word in words:
        if word.lower() in ['dog', 'corgi', 'puppy', 'canine']:  # สามารถเพิ่มคำอื่น ๆ ได้
            first_noun = word.lower()
            break
    
    return first_noun

def process_gemini_response(text_response):
    """Process Gemini API response to separate description and keywords."""
    print("Original response:", text_response)
    
    match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)
    if match:
        description = match.group(1).strip()
        description = clean_text(remove_uncertainty_words(description))
        
        # ดึง main subject ออกจาก description ถ้ามี
        main_subject = extract_main_subject(description)
        if main_subject:
            description = re.sub(r'\b' + main_subject + r'\b', '', description, count=1, flags=re.IGNORECASE).strip()
        
        keywords = match.group(2).strip()
        keywords_list = [
            remove_uncertainty_words(remove_emojis(kw.strip()))
            for kw in re.split(r",\s*", keywords)
            if kw.strip() and len(kw.split()) <= 2 and not kw.endswith('.')
        ][:50]
        
        # นำ main_subject ไปเพิ่มเป็นคีย์เวิร์ดแรกถ้ามี
        if main_subject and main_subject not in keywords_list:
            keywords_list.insert(0, main_subject)
        
        return description, keywords_list
    
    # ถ้าไม่เจอรูปแบบ Keywords: ให้แยก description และ keywords ด้วย ,
    parts = text_response.strip().split(',')
    
    description_parts = []
    keyword_parts = []
    found_sentence = False
    
    for part in parts:
        part = part.strip()
        if not found_sentence:
            description_parts.append(part)
            if re.search(r'[.!?]', part):  # หาประโยคที่จบแล้ว
                found_sentence = True
                continue
        else:
            if part:
                keyword_parts.append(part)
    
    description = ', '.join(description_parts)  # ใช้จุลภาคคั่น
    description = clean_text(remove_uncertainty_words(description))
    
    # ดึง main subject และเอาออกจาก description
    main_subject = extract_main_subject(description)
    if main_subject:
        description = re.sub(r'\b' + main_subject + r'\b', '', description, count=1, flags=re.IGNORECASE).strip()
    
    keywords_list = []
    for kw in keyword_parts:
        kw = re.sub(r'[.!?,]', '', kw).strip()
        kw = remove_uncertainty_words(remove_emojis(kw))
        if kw and len(kw.split()) <= 2:
            keywords_list.append(kw)
    
    keywords_list = list(dict.fromkeys(keywords_list))[:50]

    # นำ main_subject ไปเพิ่มเป็นคีย์เวิร์ดแรกถ้ามี
    if main_subject and main_subject not in keywords_list:
        keywords_list.insert(0, main_subject)

    print("Processed description:", description)
    print("Processed keywords:", keywords_list)
    
    return description, keywords_list

def main():
    # ตั้งค่า API Key สำหรับ Gemini
    # ตั้งค่า API Key สำหรับ Gemini
    # genai.configure(api_key="AIzaSyCadLG25yqR3q1Vk-l4MWcMx5pVsQmWDPU")

    genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")
    
    image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    results = []
    
    prompt = (
        "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters." 
        "Provide 35-50 related keywords, separated by commas. Prioritize essential or relevant keywords at the beginning."
    )    

    for image_name in image_files:
        try:
            image_path = os.path.join(image_folder, image_name)
            image = Image.open(image_path)
            
            response = model.generate_content([prompt, image])
            print(response.usage_metadata)
            description, keywords_list = process_gemini_response(response.text.strip())
            
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
