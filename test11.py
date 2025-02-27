# List of common trademarked words to check for (this is a sample, more can be added)
trademarked_words = [
    "Lego", "Photoshop", "iPhone", "GoPro", "Velcro", "Jet Ski", "Bubble Wrap",
    "Band-Aid", "Frisbee", "Crock-Pot", "Post-it", "Sharpie", "Tupperware",
    "Xerox", "Google", "Segway", "Popsicle", "Ziploc", "Roomba", "Thermos",
    "Hoover", "Jacuzzi", "Kleenex", "Vaseline", "ChapStick", "Walkman", "Sony",
    "Nintendo", "PlayStation", "Xbox", "Tesla", "MacBook", "Windows", "Android",
    "Bluetooth", "Wi-Fi", "YouTube", "Netflix", "Disney", "Starbucks", "Coca-Cola",
    "Pepsi", "McDonald's", "Nike", "Adidas", "Gucci", "Louis Vuitton", "Apple",
    "Samsung", "Canon", "Nikon", "Instagram", "Facebook", "Twitter", "TikTok"
]

# Convert to lowercase for case-insensitive checking
trademarked_words_lower = [word.lower() for word in trademarked_words]

# Function to check for trademarked words in a text field
def check_trademarks(text):
    if pd.isna(text):
        return []
    words = text.lower().split()  # Split text into words
    found = [word for word in words if word in trademarked_words_lower]
    return found

# Check for trademarked words in Description and Keywords columns
violations = []

for index, row in df.iterrows():
    found_desc = check_trademarks(row["Description"])
    found_keywords = check_trademarks(row["Keywords"])
    
    if found_desc or found_keywords:
        violations.append({
            "Filename": row["Filename"],
            "Trademarked Words in Description": found_desc,
            "Trademarked Words in Keywords": found_keywords
        })

# Convert results into a DataFrame for better readability
violations_df = pd.DataFrame(violations)

# Display the results
import ace_tools as tools
tools.display_dataframe_to_user(name="Trademark Violations", dataframe=violations_df)
