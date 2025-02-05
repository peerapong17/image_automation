import os
import csv
import re
import pandas as pd
import emoji
from PIL import Image
import google.generativeai as genai

def clean_text(text):
    """Ensures text ends with exactly one period."""
    text = text.strip()
    while text and text[-1] in '.,':
        text = text[:-1].strip()
    return text + "."

def remove_uncertainty_words(text, capitalize_all=False):
    """Remove uncertainty words while preserving spaces."""
    uncertainty_words = [
        'maybe', 'perhaps', 'likely', 'potentially', 'probably', 
        'presumably', 'conceivably', 'perchance', 'feasibly', 
        'seemingly', 'ostensibly', 'supposedly', 'reportedly',
        'apparently', 'arguably', 'hypothetically', 'allegedly',
        'theoretically', 'speculatively', 'purportedly', 'possibly'
    ]
    
    text_lower = text.lower()
    for word in uncertainty_words:
        text_lower = text_lower.replace(word, '')

    text = re.sub(r'\s+', ' ', text_lower).strip()
    
    return text.capitalize() if capitalize_all else text.lower()

def remove_emojis(text):
    """Remove emojis from text."""
    return emoji.replace_emoji(text, replace='')

def process_gemini_response(text_response):
    """Process Gemini API response to separate description and keywords."""
    print("Original response:", text_response)
    
    match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)
    if match:
        description = clean_text(match.group(1).strip())
        description = remove_uncertainty_words(description, capitalize_all=True)
        
        keywords = match.group(2).strip()
        keywords_list = [
            remove_uncertainty_words(remove_emojis(kw.strip()))
            for kw in re.split(r",\s*|\n", keywords) 
            if kw.strip() and len(kw.split()) <= 2
        ][:50]
        
        return description, keywords_list
    
    text = text_response.strip()
    parts = text.split(',')
    
    description_parts = []
    keyword_parts = []
    found_sentence = False
    
    for part in parts:
        part = part.strip()
        if not found_sentence:
            description_parts.append(part)
            if re.search(r'[.!?]', part):
                found_sentence = True
                continue
        else:
            if part:
                keyword_parts.append(part)
    
    description = ' '.join(description_parts)
    description = clean_text(description)
    description = remove_uncertainty_words(description, capitalize_all=True)
    
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
    genai.configure(api_key="YOUR_API_KEY_HERE")
    
    image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    results = []
    
    prompt = (
        "Describe the image, separated by comma, description should be more than 70 "
        "characters, but no more than 100 characters. Provide 35-50 related keywords, "
        "separated by commas. Exclude trademarked keywords. Prioritize essential or "
        "relevant keywords at the beginning. Avoid similar or redundant keywords."
    )
    
    for image_name in image_files:
        try:
            image_path = os.path.join(image_folder, image_name)
            image = Image.open(image_path)
            
            response = model.generate_content([prompt, image])
            description, keywords_list = process_gemini_response(response.text.strip())
            
            results.append({
                "Filename": image_name,
                "Title": description,
                "Description": description,
                "Keywords": ", ".join(keywords_list),
                "Category": "",
                "Release(s)": ""
            })
            
            print(f"✅ Processed: {image_name}")
            
        except Exception as e:
            print(f"❌ Error processing {image_name}: {e}")
    
    df = pd.DataFrame(results)
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    
    print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")

if __name__ == "__main__":
    main()
