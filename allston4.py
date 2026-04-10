import pandas as pd
import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def highlight_and_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    driver.execute_script("arguments[0].setAttribute('style', 'border: 5px solid red; background: yellow;');", element)
    time.sleep(2) 
    driver.execute_script("arguments[0].click();", element)

# 1. Configuration
INPUT_CSV = 'Allston_Cafes_Accurate.csv'
OUTPUT_CSV = 'Cafes_Menu_Final_Data.csv'

options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
options.add_argument("--lang=en")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 25)

try:
    df = pd.read_csv(INPUT_CSV)
except:
    print(f"Error: {INPUT_CSV} nahi mila!")
    exit()

with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Shop Name', 'Menu Item', 'Price'])

    for index, row in df.iterrows():
        cafe_name = row['Name']
        cafe_address = row['Full Address']
        
        search_query = f"{cafe_name} {cafe_address}"
        print(f"\n--- Processing: {cafe_name} ---")

        try:
            driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}")
            time.sleep(8)

            # STEP 1: Click Menu Tab
            try:
                menu_tab_xpath = "//div[@role='tablist']//button[contains(@aria-label, 'Menu')] | //div[@role='tablist']//div[text()='Menu']"
                menu_tab = wait.until(EC.element_to_be_clickable((By.XPATH, menu_tab_xpath)))
                highlight_and_click(driver, menu_tab)
                time.sleep(5)
            except:
                print("Skipping: Menu Tab not found.")
                continue

            # STEP 2: Click External Link
            try:
                link_xpath = "//a[contains(@data-item-id, 'menu')] | //a[.//div[contains(text(), 'Menu')]]"
                external_link = wait.until(EC.presence_of_element_located((By.XPATH, link_xpath)))
                
                main_window = driver.current_window_handle
                highlight_and_click(driver, external_link)
                time.sleep(10)

                # STEP 3: Switch & Extract Menu
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(7) 

                    # Patterns for extraction
                    price_pattern = r"\$\d+(?:\.\d{2})?"
                    
                
                    elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'item')] | //li | //tr | //div[@role='listitem']")
                    
                    if not elements: # Fallback agar specific containers na milein
                        elements = driver.find_elements(By.XPATH, "//div | //h3 | //h4 | //span")

                    found_items = set()
                    for el in elements:
                        try:
                            raw_text = el.text.strip()
                            if raw_text and '$' in raw_text and len(raw_text) < 150:
                                if raw_text not in found_items:
                                    match = re.search(price_pattern, raw_text)
                                    if match:
                                        price = match.group()
                                        # Cleaning: if multiple lines are there mostly first line will be name
                                        lines = raw_text.split('\n')
                                        item_name = lines[0] if lines[0] != price else "Item"
                                        
                                        # If still having problem we can see by removing price
                                        if item_name == "Item" or len(item_name) < 2:
                                            item_name = raw_text.replace(price, '').strip()

                                        writer.writerow([cafe_name, item_name, price])
                                        found_items.add(raw_text)
                        except: continue

                    driver.close()
                    driver.switch_to.window(main_window)
            except: print("Link Not Found.")
        except Exception as e:
            print(f"Error skipping {cafe_name}")

driver.quit()
print("Process Complete!")