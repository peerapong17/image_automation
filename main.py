import os
import csv
import re
import pandas as pd
import emoji
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

def clean_text(text):
    """Ensures text ends with exactly one period."""
    text = text.strip()
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
        text = text.replace(word, '')

    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
    

def remove_emojis(text):
    """Remove emojis from text."""
    return emoji.replace_emoji(text, replace='')

def process_gemini_response(text_response):
    """Process Gemini API response to separate description, keywords, and category."""
    # First try with explicit labels
    match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*?)(?:Category:|\n\n)(.*)", text_response, re.DOTALL)
    
    if not match:
        # If no explicit labels found, try splitting by double newlines
        parts = text_response.strip().split('\n\n')
        if len(parts) >= 3:
            description = parts[0].strip()
            keywords = parts[1].strip()
            category = parts[2].strip()
            
            description = clean_text(description)
            description = remove_uncertainty_words(description)
            
            keywords_list = [
                remove_uncertainty_words(remove_emojis(kw.strip()))
                for kw in re.split(r",\s*|\n", keywords) 
                if kw.strip() and len(kw.split()) <= 2
            ][:50]
            
            category = remove_uncertainty_words(remove_emojis(category))
            category = re.sub(r'^category:\s*', '', category, flags=re.IGNORECASE)
            
            return description, keywords_list, category
        return None, None, None
    
    # Process response with explicit labels
    description = clean_text(match.group(1).strip())
    description = remove_uncertainty_words(description)
    
    keywords = match.group(2).strip()
    keywords_list = [
        remove_uncertainty_words(remove_emojis(kw.strip()))
        for kw in re.split(r",\s*|\n", keywords) 
        if kw.strip() and len(kw.split()) <= 2
    ][:50]
    
    category = match.group(3).strip()
    category = remove_uncertainty_words(remove_emojis(category))
    category = re.sub(r'^category:\s*', '', category, flags=re.IGNORECASE)
    
    return description, keywords_list, category

def process_images(image_files, image_folder, model, prompt):
    results = []
    unprocessable_results = []
    
    for image_name in image_files:
        try:
            image_path = os.path.join(image_folder, image_name)
            image = Image.open(image_path)
            
            response = model.generate_content([prompt, image])

            print(response.text)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            
            description, keywords_list, category = process_gemini_response(response.text.strip())
            
            if not description or not keywords_list or not category:
                raise ValueError("Invalid response format")
            
            results.append({
                "Filename": image_name,
                "Title": description,
                "Description": description,
                "Keywords": clean_keywords(", ".join(keywords_list)).lower(),
                "Category": category.lower(),
                "Release(s)": ""
            })
            
            print(f"✅ Processed: {image_name}")
            
        except Exception as e:
            unprocessable_results.append(image_name)
            print(f"❌ Error processing {image_name}: {e}")
    
    return results, unprocessable_results

def main():
    # โหลด environment variables
    load_dotenv()
    
    # ใช้ API key จาก environment variable
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    
    image_folder = "C:/Users/Moopingz/Downloads/Image Generator/unprocessed_images"
    output_csv_path = "output_metadata.csv"
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    prompt = (
        "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters." 
        "Provide 35-50 related keywords, separated by commas. Prioritize relevant keywords at the beginning. Avoid trademark keyword."
        "Avoiding any copyrighted terms except for animal names."
        "Also provide a single category that best describes the main theme or subject of the image."
    )
    
    all_results = []
    unprocessable_results = image_files[:]
    max_retries = 3
    
    for attempt in range(max_retries):
        if not unprocessable_results:
            break  # If no more images need reprocessing, exit loop
        
        print(f"\n🔄 Attempt {attempt + 1} - Processing {len(unprocessable_results)} unprocessed images...")
        results, unprocessable_results = process_images(unprocessable_results, image_folder, model, prompt)
        all_results.extend(results)
    
    # Save results to CSV
    df = pd.DataFrame(all_results)
    df.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
    
    print(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")
    if unprocessable_results:
        print(f"❌ Remaining unprocessable images after {max_retries} attempts: {unprocessable_results}")
    else:
        print("✅ All images processed successfully!")

if __name__ == "__main__":
    main()
