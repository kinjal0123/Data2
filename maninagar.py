import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_area_data(main_area_name, area_code_prefix):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)

    # Maninagar broad areas
    landmarks = ["Maninagar", "Kankaria", "Jawahar Chowk"]
    sub_queries = [f"Cafes in {landmark} Ahmedabad" for landmark in landmarks]
    
    final_list = []
    seen_names = set()

    for sub_query in sub_queries:
        print(f"\n Searching: {sub_query} ")
        driver.get(f"https://www.google.com/maps/search/{sub_query.replace(' ', '+')}")
        time.sleep(6)

        #  STEP 1: SMART INFINITE SCROLL
        print("Scrolling to load all results... Please wait.")
        scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        while True:
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(3) # Slow scroll for data loading
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            if new_height == last_height:
                time.sleep(2)
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                if new_height == driver.execute_script("return arguments[0].scrollHeight", scrollable_div):
                    break
            last_height = new_height

        # --- STEP 2: DATA COLLECTION ---
        cafe_elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"Found {len(cafe_elements)} potential results. Starting extraction...")

        for cafe in cafe_elements:
            try:
                name = cafe.get_attribute("aria-label")
                if not name or name in seen_names: continue
                
                # Click and Wait for Panel to Sync
                driver.execute_script("arguments[0].click();", cafe)
                
                # Validation: Check if the side panel heading matches the name
                try:
                    wait.until(lambda d: d.find_element(By.XPATH, '//h1[contains(@class, "DUwDvf")]').text.strip().lower() == name.lower())
                except:
                    time.sleep(3) # Extra wait if title doesn't sync

                # Address Extraction
                try:
                    address_el = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']")
                    full_address = address_el.text.strip().replace("\n", ", ")
                except:
                    full_address = f"{main_area_name}, Ahmedabad"

                # Coords Extraction (Wait for URL refresh)
                time.sleep(2.5)
                url = driver.current_url
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', url)
                
                pincode_match = re.search(r'\b\d{6}\b', full_address)
                pincode = pincode_match.group(0) if pincode_match else "380008"

                seen_names.add(name)
                final_list.append({
                    "Name": name,
                    "Shop Code": f"AMD-{area_code_prefix}-{100 + len(final_list) + 1}",
                    "Latitude": coords.group(1) if coords else "N/A",
                    "Longitude": coords.group(2) if coords else "N/A",
                    "Full Address": full_address,
                    "Pincode": pincode
                })
                print(f"Captured: {name}")
                
            except Exception:
                continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    target_area = "Maninagar"
    short_code = "MNR" 
    
    data = scrape_area_data(target_area, short_code)
    
    if data:
        df = pd.DataFrame(data)
        # Final cleanup for exact duplicates
        df.drop_duplicates(subset=['Name'], inplace=True)
        df.to_csv(f"{target_area}_Full_Data.csv", index=False, encoding='utf-8-sig')
        print(f"\n--- DONE! Total {len(df)} Unique Cafes found. ---")