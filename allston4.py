import pandas as pd
import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- Configuration ---
INPUT_FILE = 'Allston_Cafes_Final_Updated.csv'
OUTPUT_FILE = 'cafe_menus_cleaned.csv'

chrome_options = Options()
# chrome_options.add_argument("--headless") 
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Banned words jo menu ka part nahi hote
BANNED_WORDS = {
    'sign in', 'order now', 'login', 'cart', 'checkout', 'my account', 'locations', 
    'privacy policy', 'terms of service', 'follow us', 'facebook', 'instagram', 
    'twitter', 'copyright', 'all rights reserved', 'contact us', 'view nutrition', 
    'find a store', 'gift cards', 'careers', 'newsletter', 'search', 'click here'
}

def get_pure_menu(url):
    try:
        driver.get(url)
        time.sleep(7) 

        # Step 1: Specific Menu Page dhundna (taki home page ka kachra na aaye)
        try:
            menu_element = driver.find_element(By.PARTIAL_LINK_TEXT, 'Menu')
            menu_element.click()
            time.sleep(5)
        except:
            pass # Agar click nahi hua toh current page hi scan karenge

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Faltu tags uda do
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'button']):
            tag.decompose()

        # Step 2: Sirf un areas ko target karo jahan menu hone ke chances hain
        # Common menu tags: h3, h4, span (price ke sath), li
        potential_items = soup.find_all(['h3', 'h4', 'h5', 'p', 'span', 'li'])
        
        extracted_menu = []
        for item in potential_items:
            text = item.get_text().strip()
            
            # Filtering logic:
            # 1. Text bahut chota ya bahut bada na ho (item names are usually 3-50 chars)
            # 2. Text banned words list mein na ho
            # 3. Text mein koi number/price ho ya wo kisi heading ka part ho
            if 3 < len(text) < 60:
                low_text = text.lower()
                
                # Check if it contains banned phrases
                if any(word in low_text for word in BANNED_WORDS):
                    continue
                
                # Pattern check: Agar "Sign in" ya "Harvard Square" jaisa generic info hai toh skip
                if re.search(r'(\d+\.\d{2})|(\$)', text) or len(text.split()) < 6:
                    # Duplicate check
                    if text not in extracted_menu:
                        extracted_menu.append(text)
        
        return extracted_menu

    except Exception as e:
        print(f"Error: {e}")
        return []

# --- Main Run ---
df = pd.read_csv(INPUT_FILE)

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Cafe Name', 'Menu Item'])

    for index, row in df.iterrows():
        name = row['Name']
        url = row['Website']
        
        if pd.isna(url) or not str(url).startswith('http'):
            continue

        print(f"Fetching Menu for: {name}")
        menu_list = get_pure_menu(url)

        if menu_list:
            for item in menu_list:
                writer.writerow([name, item])
        else:
            writer.writerow([name, "Manual Check Required"])
        
        print(f"Waiting...")
        time.sleep(5)

driver.quit()
print("Cleaned data saved!")