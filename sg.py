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

    # S.G. Highway Specific Landmarks
    landmarks = [
        "S.G. Highway Gota", 
        "Sola Bridge S.G. Highway", 
        "Thaltej Cross Road S.G. Highway", 
        "Sindhu Bhavan Road", # S.G. Highway se connected main hub
        "Iskcon Cross Road",
        "Prahladnagar AMT S.G. Highway"
    ]
    sub_queries = [f"Cafes in {landmark} Ahmedabad" for landmark in landmarks]
    
    final_list = []
    seen_names = set()

    for sub_query in sub_queries:
        print(f"\n--- Searching: {sub_query} ---")
        driver.get(f"https://www.google.com/maps/search/{sub_query.replace(' ', '+')}")
        time.sleep(7) 

        # --- STEP 1: SMART INFINITE SCROLL ---
        print("Scrolling to load all results... Please wait.")
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
            last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            while True:
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(3.5) 
                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                if new_height == last_height:
                    time.sleep(2)
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                    if new_height == driver.execute_script("return arguments[0].scrollHeight", scrollable_div):
                        break
                last_height = new_height
        except: pass

        # STEP 2: DATA COLLECTION
        cafe_elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"Found {len(cafe_elements)} potential results. Starting extraction...")

        for cafe in cafe_elements:
            try:
                name = cafe.get_attribute("aria-label")
                if not name or name in seen_names: continue
                
                # Element visibility ensuring scroll
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cafe)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", cafe)
                
                # Strict Sync Logic
                try:
                    # Wait for title to match
                    wait.until(lambda d: d.find_element(By.XPATH, '//h1[contains(@class, "DUwDvf")]').text.strip().lower() == name.lower())
                except:
                    time.sleep(4) 

                # Refresh buffer
                time.sleep(2.5) 

                # Address Extraction
                try:
                    address_el = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']")
                    full_address = address_el.text.strip().replace("\n", ", ")
                except:
                    full_address = f"{main_area_name}, Ahmedabad"

                # Coords Extraction (3.5s buffer)
                time.sleep(3.5) 
                url = driver.current_url
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', url)
                
                pincode_match = re.search(r'\b\d{6}\b', full_address)
                # S.G. Highway various pincodes (380054, 380059, 380015)
                pincode = pincode_match.group(0) if pincode_match else "380054"

                seen_names.add(name)
                final_list.append({
                    "Name": name,
                    "Shop Code": f"AMD-{area_code_prefix}-{100 + len(final_list) + 1}",
                    "Latitude": coords.group(1) if coords else "N/A",
                    "Longitude": coords.group(2) if coords else "N/A",
                    "Full Address": full_address,
                    "Pincode": pincode
                })
                print(f"Captured Unique: {name}")
                
            except Exception:
                continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    # Settings for S.G. Highway
    target_area = "SG_Highway"
    short_code = "SGH" 
    
    data = scrape_area_data(target_area, short_code)
    
    if data:
        df = pd.DataFrame(data)
        # Final cleanup for unique data
        df.drop_duplicates(subset=['Name'], inplace=True)
        df.drop_duplicates(subset=['Latitude', 'Longitude'], keep='first', inplace=True)
        
        file_name = f"{target_area}_Full_Data.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"\n SUCCESS! Total {len(df)} Unique Cafes found on S.G. Highway.")