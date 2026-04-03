import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_ahmedabad_full_city():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    ahmedabad_zones = [
        "Cafes in Sindhu Bhavan Road Ahmedabad",
        "Coffee shops in Prahlad Nagar Ahmedabad",
        "Cafes in Satellite Ahmedabad",
        "Cafes in Vastrapur Ahmedabad",
        "Coffee shops in Bodakdev Ahmedabad",
        "Cafes in Navrangpura Ahmedabad",
        "Cafes in C G Road Ahmedabad",
        "Coffee shops in Bopal Ahmedabad",
        "Cafes in Gota Ahmedabad",
        "Cafes in Chandkheda Ahmedabad",
        "Restaurants in Maninagar Ahmedabad",
        "Cafes in Nikol Ahmedabad",
        "Coffee shops in Sola Ahmedabad",
        "Cafes in Thaltej Ahmedabad"
    ]
    
    final_list = []
    seen_names = set()

    for zone_query in ahmedabad_zones:
        print(f"\n--- Scanning Zone: {zone_query} ---")
        driver.get(f"https://www.google.com/maps/search/{zone_query.replace(' ', '+')}")
        time.sleep(5)

        # Scrolling logic for each zone
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
            for _ in range(8): 
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2)
        except: pass

        cafe_elements = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        for cafe in cafe_elements:
            try:
                name = cafe.get_attribute("aria-label")
                if not name or name in seen_names: continue
                
                # Cafe Details Load
                driver.execute_script("arguments[0].click();", cafe)
                time.sleep(3.5) # extra wait for detailed address 

                #  Perfect Address Extraction
                try:
                    # Specific ID targeting for full address
                    full_address = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']").text.strip()
                except:
                    full_address = "Ahmedabad, Gujarat"

                # Pincode extraction logic
                pincode_match = re.search(r'\b\d{6}\b', full_address)
                pincode = pincode_match.group(0) if pincode_match else "380001"

                # Lat/Long extraction from URL
                url = driver.current_url
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', url)
                
                seen_names.add(name)
                final_list.append({
                    "Name": name,
                    "Shop Code": f"AMD-{pincode[-3:]}-{len(final_data)+1 if 'final_data' in locals() else len(final_list)+1}",
                    "Latitude": coords.group(1) if coords else "N/A",
                    "Longitude": coords.group(2) if coords else "N/A",
                    "Full Address": full_address.replace("\n", ", "),
                    "Pincode": pincode
                })
                print(f"Captured ({len(final_list)}): {name}")
            except: continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    all_data = scrape_ahmedabad_full_city()
    if all_data:
        df = pd.DataFrame(all_data)
        # Shop Code cleanup
        df['Shop Code'] = [f"AMD-{row['Pincode'][-3:]}-{i+1}" for i, row in df.iterrows()]
        
        df.to_csv("Ahmedabad_Full_City_Cafes.csv", index=False, encoding='utf-8-sig')
        print(f"\n SUCCESS! Total {len(df)} Unique Cafes captured across Ahmedabad.")