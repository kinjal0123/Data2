import time
import pandas as pd
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image
from io import BytesIO
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR_CONFIG = r"--psm 6 --oem 3"


# TEXT PREPROCESSING (Important)
def preprocess_image(img_bytes):
    img = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # enhance clarity
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    gray = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 31, 2
    )

    return gray


# Rule-based category classifier

def categorize_item(item):
    item_l = item.lower()

    if any(k in item_l for k in ["latte", "espresso", "mocha", "americano", "cold brew"]):
        return "Coffee", "Beverage"

    if any(k in item_l for k in ["tea", "chai", "matcha"]):
        return "Tea", "Beverage"

    if any(k in item_l for k in ["sandwich", "panini", "wrap"]):
        return "Sandwich", "Food"

    if any(k in item_l for k in ["cookie", "cake", "pastry", "croissant"]):
        return "Bakery", "Dessert"

    if any(k in item_l for k in ["smoothie", "juice"]):
        return "Juice", "Beverage"

    return "Other", "Other"

# Rule-based taste classifier

def detect_taste(item):
    item_l = item.lower()

    if any(k in item_l for k in ["chocolate", "mocha"]):
        return "Sweet"
    if any(k in item_l for k in ["spicy", "hot"]):
        return "Spicy"
    if any(k in item_l for k in ["vanilla", "caramel"]):
        return "Mild Sweet"
    if any(k in item_l for k in ["black coffee", "americano"]):
        return "Bitter"
    return ""


# Parse text for items + price + description

def parse_menu_text(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    menu = []
    
    for i, line in enumerate(lines):
        price_match = re.search(r"(\$?\d+(\.\d{1,2})?)", line)

        if price_match:
            price = price_match.group(1).replace("$", "")
            item_name = line.replace(price_match.group(1), "").strip()

            # Description = next line if looks like sentence
            description = ""
            if i + 1 < len(lines) and len(lines[i+1].split()) > 3:
                description = lines[i+1].strip()

            # Category rules
            category, subcat = categorize_item(item_name)
            taste = detect_taste(item_name)

            menu.append({
                "item_name": item_name,
                "price": price,
                "description": description,
                "category": category,
                "subcategory": subcat,
                "taste": taste
            })

    return menu

# OCR from a single image

def extract_text(img_bytes):
    pre = preprocess_image(img_bytes)
    text = pytesseract.image_to_string(pre, config=OCR_CONFIG)
    return text

# Scrape menu from Google Maps

def scrape_menu(cafe_name, address):
    query = f"{cafe_name} {address} menu"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(4)

    try:
        photos = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Photos')]"))
        )
        photos.click()
        time.sleep(3)
    except:
        print(" Photos tab not found")
        driver.quit()
        return []

    img_elements = driver.find_elements(By.XPATH, "//img[contains(@src,'=s')]")
    print(f"Found {len(img_elements)} images")

    results = []

    for img in img_elements[:12]:  
        try:
            img_url = img.get_attribute("src")

            # download image
            resp = requests.get(img_url)
            img_bytes = resp.content

            # OCR
            text = extract_text(img_bytes)
            parsed = parse_menu_text(text)

            results.extend(parsed)
        except:
            continue

    driver.quit()
    return results


# MAIN
df = pd.read_csv("Allston_Cafes_Accurate.csv")

final_rows = []

for _, row in df.iterrows():
    cafe = row["Name"]
    addr = row["Full Address"]
    code = row["Shop Code"]

    print(f"\n➡ Extracting menu for: {cafe}")

    items = scrape_menu(cafe, addr)

    for item in items:
        item["cafe_name"] = cafe
        item["shop_code"] = code
        final_rows.append(item)

pd.DataFrame(final_rows).to_csv("Allston_Cafes_Menu_Final.csv", index=False)

print("\n Extraction completed!")