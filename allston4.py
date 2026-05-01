import time
import requests
import re
import pytesseract
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIG ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Runs in the background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_logic(text):
    """Deep Regex to catch item and price patterns like 'Coffee $5.50' or 'Sandwich 12'"""
    # Pattern: Captures text followed by a currency symbol and digits
    pattern = r"([A-Za-z\s'&]{4,30})\s*[:\.\-]*\s*[\$\₹]?\s*(\d{1,3}(?:\.\d{2})?)"
    return re.findall(pattern, text)

def aggressive_scrape(base_url):
    driver = get_driver()
    target_urls = [urljoin(base_url, p) for p in ["/menu", "/menu/", "/all-day-menu"]]
    
    final_menu = {}

    for url in target_urls:
        print(f"\n Launching Browser for: {url}")
        try:
            driver.get(url)
            time.sleep(5) # Wait for JavaScript to load fully
            
            # Action 1: Full Page Text Extraction
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Strategy A: Text Parsing
            # Hum poore page ka text nikal kar regex chalayenge
            raw_text = driver.find_element(By.TAG_NAME, "body").text
            items = extract_logic(raw_text)
            
            for item, price in items:
                final_menu[item.strip()] = price

            # Strategy B: Image Scraping (If text is low)
            if len(final_menu) < 5:
                print(" Text not found, images being scan...")
                images = soup.find_all('img')
                for img in images[:10]: # Top 10 images
                    src = img.get('src') or img.get('data-src')
                    if src:
                        img_url = urljoin(url, src)
                        if ".jpg" in img_url or ".png" in img_url:
                            try:
                                res = requests.get(img_url, timeout=5)
                                pic = Image.open(BytesIO(res.content))
                                ocr_text = pytesseract.image_to_string(pic)
                                ocr_items = extract_logic(ocr_text)
                                for i, p in ocr_items:
                                    final_menu[i.strip()] = p
                            except:
                                continue

        except Exception as e:
            print(f"[!] Error on {url}: {e}")

    driver.quit()

    # Results Print
    if final_menu:
        print("\n" + "="*50)
        print(f"{'ITEM NAME':<35} | {'PRICE':<10}")
        print("="*50)
        for item, price in sorted(final_menu.items()):
            if len(item) > 3:
                print(f"{item[:35]:<35} | ${price}")
    else:
        print("\n Hard Luck! Website has blocked your url.")

if __name__ == "__main__":
    aggressive_scrape("https://tattebakery.com")