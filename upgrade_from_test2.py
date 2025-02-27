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
    text = re.sub(r'\s+\b\w+\b[.,]?$', '', text, flags=re.IGNORECASE).strip()
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

def process_gemini_response(text_response):
    """Process Gemini API response to separate description and keywords."""
    match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)
    if match:
        description = match.group(1).strip()
        description = clean_text(remove_uncertainty_words(description))
        
        keywords = match.group(2).strip()
        keywords_list = [
            remove_uncertainty_words(remove_emojis(kw.strip()))
            for kw in re.split(r",\s*", keywords)
            if kw.strip() and len(kw.split()) <= 2 and not kw.endswith('.')
        ][:50]
        
        return description, keywords_list
    return None, None  # Indicate failure

def main():
    genai.configure(api_key="YOUR_API_KEY")
    image_folder = "C:/Users/moopi/Downloads/Image Generator/image_test"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    results = []
    failed_images = []
    
    prompt = (
        "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters. "
        "Provide 35-50 related keywords, separated by commas. Prioritize relevant keywords at the beginning. Avoid trademark keyword. "
        "Avoiding any copyrighted terms except for animal names."
    )  
    
    for image_name in image_files:
        attempts = 0
        success = False
        
        while attempts < 3 and not success:
            try:
                image_path = os.path.join(image_folder, image_name)
                image = Image.open(image_path)
                response = model.generate_content([prompt, image])
                
                description, keywords_list = process_gemini_response(response.text.strip())
                if description and keywords_list:
                    results.append({
                        "Filename": image_name,
                        "Title": description,
                        "Description": description,
                        "Keywords": clean_keywords(", ".join(keywords_list)).lower(),
                        "Category": "",
                        "Release(s)": ""
                    })
                    print(f"✅ Processed: {image_name}")
                    success = True
                else:
                    print(f"🔁 Retrying {image_name} ({attempts + 1}/3)")
                    attempts += 1
            
            except Exception as e:
                print(f"❌ Error processing {image_name}: {e}")
                break  # Stop retrying if an error occurs
        
        if not success:
            failed_images.append(image_name)
    
    if failed_images:
        print("\n🚨 The following images could not be processed:")
        for img in failed_images:
            print(f"❌ {img}")
    else:
        print("\n✅ All images processed successfully.")
    
    df = pd.DataFrame(results)
    df.to_csv(output_csv_path, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
    print(f"\n✅ CSV saved as: {output_csv_path}")

if __name__ == "__main__":
    main()
