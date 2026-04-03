import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_vastral_complete_coverage():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    vastral_sub_areas = [
        "Cafes near Vastral Gam Metro Station",
        "Coffee shops near Nirant Cross Road Vastral",
        "Cafes near Madhav Farm Vastral",
        "Restaurants near Ratanpura Vastral",
        "Cafes near Shivalik Residency Vastral"
    ]
    
    final_list = []
    seen_names = set()

    for sub_query in vastral_sub_areas:
        print(f"Scanning Area: {sub_query}...")
        driver.get(f"https://www.google.com/maps/search/{sub_query.replace(' ', '+')}")
        time.sleep(4)

        
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
            for _ in range(5):
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(1.5)
        except: pass

        cafe_elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        for cafe in cafe_elements:
            try:
                name = cafe.get_attribute("aria-label")
                if not name or name in seen_names: continue
                
                # Click for Perfect Address
                driver.execute_script("arguments[0].click();", cafe)
                time.sleep(3) # Wait for panel

                # --- Deep Address Extraction ---
                try:
                   
                    full_address = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']").text.strip()
                except:
                    full_address = "Vastral, Ahmedabad"

                pincode_match = re.search(r'\b\d{6}\b', full_address)
                pincode = pincode_match.group(0) if pincode_match else "382418"

                url = driver.current_url
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', url)
                
                seen_names.add(name)
                final_list.append({
                    "Name": name,
                    "Shop Code": f"AMD-VSR-{100 + len(final_list) + 1}",
                    "Latitude": coords.group(1) if coords else "N/A",
                    "Longitude": coords.group(2) if coords else "N/A",
                    "Full Address": full_address.replace("\n", ", "),
                    "Pincode": pincode
                })
                print(f"Captured: {name}")
            except: continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    data = scrape_vastral_complete_coverage()
    if data:
        df = pd.DataFrame(data)
        df.to_csv("Vastral_Full_Area_Final.csv", index=False, encoding='utf-8-sig')
        print(f"\n--- DONE! Total {len(df)} Unique Cafes found in all of Vastral. ---")