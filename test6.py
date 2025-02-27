import os
import csv
import re
import pandas as pd
import emoji
from PIL import Image
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

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
    """Process Gemini API response to separate description and keywords."""
    match = re.search(r"(.*?)(?:Keywords:|\n\n)(.*)", text_response, re.DOTALL)
    if match:
        description = clean_text(match.group(1).strip())
        description = remove_uncertainty_words(description)
        
        keywords = match.group(2).strip()
        keywords_list = [
            remove_uncertainty_words(remove_emojis(kw.strip()))
            for kw in re.split(r",\s*|\n", keywords) 
            if kw.strip() and len(kw.split()) <= 2
        ][:50]
        
        return description, keywords_list
    
    return None, None

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processor")
        self.root.geometry("800x600")
        
        # Variables
        self.folder_path = tk.StringVar()
        self.api_key = tk.StringVar()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # API Key
        ttk.Label(main_frame, text="Gemini API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.api_key, width=50).grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Folder selection
        ttk.Label(main_frame, text="Image Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.folder_path, width=50).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # Process button
        ttk.Button(main_frame, text="Process Images", command=self.process_images).grid(row=2, column=0, columnspan=3, pady=20)
        
        # Log area
        self.log_area = ScrolledText(main_frame, width=70, height=20)
        self.log_area.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=3, pady=10)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.root.update()

    def process_single_image(self, image_name, image_folder, model, prompt):
        try:
            image_path = os.path.join(image_folder, image_name)
            image = Image.open(image_path)
            
            response = model.generate_content([prompt, image])
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            
            description, keywords_list = process_gemini_response(response.text.strip())
            
            if not description or not keywords_list:
                raise ValueError("Invalid response format")
            
            return {
                "Filename": image_name,
                "Title": description,
                "Description": description,
                "Keywords": clean_keywords(", ".join(keywords_list)).lower(),
                "Category": "",
                "Release(s)": ""
            }
            
        except Exception as e:
            self.log(f"❌ Error processing {image_name}: {e}")
            return None

    def process_images(self):
        if not self.api_key.get().strip():
            messagebox.showerror("Error", "Please enter your Gemini API Key")
            return
            
        if not self.folder_path.get().strip():
            messagebox.showerror("Error", "Please select an image folder")
            return
        
        try:
            # Configure API
            genai.configure(api_key=self.api_key.get().strip())
            model = genai.GenerativeModel("gemini-1.5-pro")
            
            image_folder = self.folder_path.get()
            output_csv_path = os.path.join(image_folder, "output_metadata.csv")
            
            image_files = [f for f in os.listdir(image_folder) 
                          if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            
            if not image_files:
                messagebox.showwarning("Warning", "No image files found in the selected folder")
                return
            
            prompt = (
                "Describe the image, separated by comma, description should be more than 70 characters, but no more than 100 characters." 
                "Provide 35-50 related keywords, separated by commas. Prioritize relevant keywords at the beginning. Avoid trademark keyword."
                "Avoiding any copyrighted terms except for animal names."
            )
            
            all_results = []
            unprocessable_results = image_files[:]
            max_retries = 3
            
            self.progress['maximum'] = len(image_files) * max_retries
            self.progress['value'] = 0
            
            for attempt in range(max_retries):
                if not unprocessable_results:
                    break
                
                self.log(f"\n🔄 Attempt {attempt + 1} - Processing {len(unprocessable_results)} unprocessed images...")
                
                current_results = []
                still_unprocessable = []
                
                for image_name in unprocessable_results:
                    result = self.process_single_image(image_name, image_folder, model, prompt)
                    if result:
                        current_results.append(result)
                        self.log(f"✅ Processed: {image_name}")
                    else:
                        still_unprocessable.append(image_name)
                
                all_results.extend(current_results)
                unprocessable_results = still_unprocessable
                
                self.progress['value'] += len(current_results)
                
            # Save results to CSV
            df = pd.DataFrame(all_results)
            df.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
            
            self.log(f"\n✅ Finished processing all images. CSV saved as: {output_csv_path}")
            if unprocessable_results:
                self.log(f"❌ Remaining unprocessable images after {max_retries} attempts: {unprocessable_results}")
            else:
                self.log("✅ All images processed successfully!")
                
            messagebox.showinfo("Success", "Processing completed!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.log(f"❌ Error: {str(e)}")

def main():
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
