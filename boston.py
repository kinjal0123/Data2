import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_boston_cafes(main_area_name, area_code_prefix):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30) # USA networks  30s wait is enough

    # Boston Specific Neighborhoods
    landmarks = [
        "Back Bay Boston", 
        "North End Boston", 
        "Seaport District Boston", 
        "South End Boston", 
        "Beacon Hill Boston",
        "Cambridge near Harvard Square" # Boston meta-area ka part hai
    ]
    sub_queries = [f"Best Cafes in {landmark}" for landmark in landmarks]
    
    final_list = []
    seen_names = set()

    for sub_query in sub_queries:
        print(f"\n--- Searching Boston: {sub_query} ---")
        driver.get(f"https://www.google.com/maps/search/{sub_query.replace(' ', '+')}")
        time.sleep(8) # International page load buffer

        # --- STEP 1: DEEP SCROLLING ---
        print("Scrolling to load all Boston results... Please wait.")
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
            last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            while True:
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(4) # Boston maps results heavy hote hain
                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                if new_height == last_height:
                    time.sleep(3)
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                    if new_height == driver.execute_script("return arguments[0].scrollHeight", scrollable_div):
                        break
                last_height = new_height
        except: pass

        # --- STEP 2: PRECISE EXTRACTION ---
        cafe_elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"Found {len(cafe_elements)} potential Boston results.")

        for cafe in cafe_elements:
            try:
                name = cafe.get_attribute("aria-label")
                if not name or name in seen_names: continue
                
                # Scroll to element to ensure it is in view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cafe)
                time.sleep(1.5)
                driver.execute_script("arguments[0].click();", cafe)
                
                # --- FIX: Strict Sync for USA Data ---
                # Panel change hone ka intezar (Title match)
                try:
                    wait.until(lambda d: d.find_element(By.XPATH, '//h1[contains(@class, "DUwDvf")]').text.strip().lower() == name.lower())
                except:
                    time.sleep(5) # USA maps interface thoda slow sync hota hai

                # Address sync buffer
                time.sleep(3) 

                # Address Extraction (USA Format)
                try:
                    address_el = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']")
                    full_address = address_el.text.strip().replace("\n", ", ")
                except:
                    full_address = "Boston, MA"

                # Coords Extraction (4s wait for URL refresh)
                time.sleep(4) 
                url = driver.current_url
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', url)
                
                # Zip Code Extraction (USA Zip codes are 5 digits, e.g., 02116)
                zip_match = re.search(r'\b\d{5}\b', full_address)
                zip_code = zip_match.group(0) if zip_match else "02108" # Boston Common default Zip

                seen_names.add(name)
                final_list.append({
                    "Name": name,
                    "Shop Code": f"BOS-{area_code_prefix}-{100 + len(final_list) + 1}",
                    "Latitude": coords.group(1) if coords else "N/A",
                    "Longitude": coords.group(2) if coords else "N/A",
                    "Full Address": full_address,
                    "Zip Code": zip_code,
                    "City": "Boston",
                    "State": "MA"
                })
                print(f"Captured Unique: {name} ({zip_code})")
                
            except Exception:
                continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    # Settings for Boston
    target_city = "Boston"
    short_code = "USA" 
    
    data = scrape_boston_cafes(target_city, short_code)
    
    if data:
        df = pd.DataFrame(data)
        # Final cleanup for unique data
        df.drop_duplicates(subset=['Name'], inplace=True)
        df.drop_duplicates(subset=['Latitude', 'Longitude'], keep='first', inplace=True)
        
        file_name = f"{target_city}_Full_Data.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"\n--- SUCCESS! Total {len(df)} Unique Boston Cafes found. ---")