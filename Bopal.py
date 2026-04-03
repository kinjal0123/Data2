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
    wait = WebDriverWait(driver, 15)

    # Specific Landmarks of Bopal
    landmarks = [
        "South Bopal", 
        "TRP Mall", 
        "Bopal Cross Road", 
        "Iscon Ambli Road", 
        "Sardar Patel Ring Road Bopal"
    ]
    
    sub_queries = [f"Cafes in {landmark} {main_area_name}" for landmark in landmarks]
    
    final_list = []
    seen_names = set()

    for sub_query in sub_queries:
        print(f"\nScanning Area: {sub_query}...")
        driver.get(f"https://www.google.com/maps/search/{sub_query.replace(' ', '+')}")
        time.sleep(5)

        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
            for _ in range(5):
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2)
        except: pass

        cafe_elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        for cafe in cafe_elements:
            try:
                name = cafe.get_attribute("aria-label")
                if not name or name in seen_names: continue
                
                # Click and Wait for Panel Title
                driver.execute_script("arguments[0].click();", cafe)
                
                # waiting till the side panel title doesn't match to current cafe name
                try:
                    wait.until(lambda d: d.find_element(By.XPATH, '//h1[contains(@class, "DUwDvf")]').text.strip() == name)
                except:
                    time.sleep(2) 

                # Address Extraction with Retry
                try:
                    # Specific element for address to avoid old data
                    address_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id='address']")))
                    full_address = address_el.text.strip().replace("\n", ", ")
                except:
                    full_address = f"{main_area_name}, Ahmedabad"

                # URL/Coords Update Wait
                time.sleep(1.5)
                url = driver.current_url
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', url)
                
                pincode_match = re.search(r'\b\d{6}\b', full_address)
                pincode = pincode_match.group(0) if pincode_match else "380058"

                seen_names.add(name)
                final_list.append({
                    "Name": name,
                    "Shop Code": f"AMD-{area_code_prefix}-{100 + len(final_list) + 1}",
                    "Latitude": coords.group(1) if coords else "N/A",
                    "Longitude": coords.group(2) if coords else "N/A",
                    "Full Address": full_address,
                    "Pincode": pincode
                })
                print(f"Captured: {name} at {coords.group(1) if coords else 'N/A'}")
                
            except Exception as e:
                print(f"Skipping {name} due to error...")
                continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    target_area = "Bopal"
    short_code = "BPL" 
    
    data = scrape_area_data(target_area, short_code)
    
    if data:
        df = pd.DataFrame(data)
        # Final check for duplicates
        df.drop_duplicates(subset=['Name'], inplace=True)
        file_name = f"{target_area}_Cafe_Data_Fixed.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"\n SUCCESS! Total {len(df)} Unique Cafes saved in {file_name}. ")