import os
import csv
import re
import pandas as pd
from PIL import Image
import google.generativeai as genai

def clean_text(text):
    """
    Ensures text ends with exactly one period.
    """
    text = text.strip()
    # Remove trailing punctuation
    while text and text[-1] in '.,':
        text = text[:-1].strip()
    return text + "."

def clean_keywords_string(keywords_string):
    if keywords_string.endswith('.'):
        return keywords_string[:-1]
    return keywords_string

def process_gemini_response(text_response):
    """
    Process Gemini API response to separate description and keywords.
    If the response doesn't contain explicit 'Keywords:' separator,
    it will try to separate based on sentence structure.
    """
    print("Original response:", text_response)
    
    # First try to find explicit Keywords section
    match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)
    if match:
        description = clean_text(match.group(1).strip())
        description = description.capitalize()
        
        keywords = match.group(2).strip()
        keywords_list = [
            kw.strip().lower() 
            for kw in re.split(r",\s*|\n", keywords) 
            if kw.strip() and len(kw.split()) <= 2
        ][:50]
        
        return description, keywords_list
    
    # If no explicit Keywords section, try to separate based on sentence structure
    text = text_response.strip()
    parts = text.split(',')
    
    # Find the end of the first complete sentence
    description_parts = []
    keyword_parts = []
    found_sentence = False
    
    for part in parts:
        part = part.strip()
        if not found_sentence:
            description_parts.append(part)
            # Check if this part contains end of sentence
            if re.search(r'[.!?]', part):
                found_sentence = True
                continue
        else:
            if part:  # Only add non-empty parts as keywords
                keyword_parts.append(part)
    
    # Clean up description
    description = ' '.join(description_parts)
    description = clean_text(description)
    description = description.capitalize()
    
    # Clean up keywords
    keywords_list = []
    for kw in keyword_parts:
        # Remove any punctuation and extra whitespace
        kw = re.sub(r'[.!?,]', '', kw).strip().lower()
        # Only keep keywords with 1-2 words
        if kw and len(kw.split()) <= 2:
            keywords_list.append(kw)
    
    # Remove duplicates while preserving order
    keywords_list = list(dict.fromkeys(keywords_list))[:50]
    
    print("Processed description:", description)
    print("Processed keywords:", keywords_list)
    
    return description, keywords_list

def main():
    # ตั้งค่า API Key สำหรับ Gemini
    # genai.configure(api_key="AIzaSyCcUKq4ygHQwHi_h7CJBctK_VaJQWrdzCI")
    
    # free api key options
    # genai.configure(api_key="AIzaSyDbMaW0pEx2Cr9HswWv984rp-C_SDXA-Ic")
    # genai.configure(api_key="AIzaSyAg_S0xTN67D_091F5VldfvqUFIQM3hZVM")
    
    # Configuration
    image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    # Find image files
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    results = []
    
    prompt = (
        "Describe the image, separated by comma, description should be more than 70 "
        "characters, but no more than 100 characters. Provide 35-50 related keywords, "
        "separated by commas. Exclude trademarked keywords. Prioritize essential or "
        "relevant keywords at the beginning. Avoid similar or redundant keywords."
    )
    
    # Process each image
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

    for result in results:
        result['Keywords'] = clean_keywords_string(result['Keywords'])
    
    # Write CSV header
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write('Filename,Title,Description,Keywords,Category,Release(s)\n')
        
    
    # Write data with proper quoting
    df = pd.DataFrame(results)
    with open(output_csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
        for _, row in df.iterrows():
            writer.writerow(row)
            
    print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")

if __name__ == "__main__":
    main()