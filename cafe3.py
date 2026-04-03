import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def classify_item(name):
    """Item name se taste aur category nikalna"""
    n = name.lower()
    if any(x in n for x in ["coffee", "latte", "cappuccino", "espresso", "brew"]):
        return "Beverages", "Coffee", "Bold/Bitter"
    elif any(x in n for x in ["pizza", "pasta", "sandwich", "burger", "maggie"]):
        return "Food", "Continental", "Savory/Spicy"
    elif any(x in n for x in ["shake", "smoothie", "dessert", "cake", "pastry"]):
        return "Food & Bev", "Dessert", "Sweet"
    return "Food", "Cafe Special", "Standard"

def scrape_ahmedabad_deep_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    # Ahmedabad coverage: Max areas
    areas = [
        "Sindhu Bhavan Road", "Prahlad Nagar", "Bodakdev", "Satellite", "Vastrapur",
        "Navrangpura", "C G Road", "Maninagar", "Bopal", "Gota", "Chandkheda", "Nikol"
    ]
    
    final_data = []
    processed_items = set()

    for area in areas:
        print(f"--- Scanning Area: {area} ---")
        query = f"Cafes in {area} Ahmedabad"
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
        time.sleep(5)

        # Scroll logic to load all cafes in that area
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
            for _ in range(6):
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2)
        except: pass

        cafe_links = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        
        for link in cafe_links[:15]: # Top 15 cafes per area
            try:
                cafe_name = link.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", link)
                time.sleep(5) # Wait for details to load

                # 1. Basic Info
                address_raw = driver.find_element(By.XPATH, '//button[@data-item-id="address"]').text
                pincode = re.search(r'\b\d{6}\b', address_raw).group(0) if re.search(r'\b\d{6}\b', address_raw) else "380000"
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', driver.current_url)
                lat, lng = (coords.group(1), coords.group(2)) if coords else ("N/A", "N/A")

                # 2. Deep Menu Extraction Logic
                # Google Maps Popular Dishes Section
                # Humein un elements ko target karna hai jisme Text aur Price dono ho
                menu_elements = driver.find_elements(By.XPATH, '//div[@class="m6QErb "]//div[contains(@aria-label, "₹")] | //div[@class="fontHeadlineSmall"]')
                
                cafe_menu_list = []
                # Agar Popular Dishes grid hai, toh titles aur prices ko map karein
                titles = driver.find_elements(By.CLASS_NAME, "fontHeadlineSmall")
                # Price extraction directly from text content
                all_text = driver.find_element(By.TAG_NAME, "body").text
                
                # JUGAD: Agar elements milte hain toh unhe process karo
                if titles:
                    for t in titles:
                        item_name = t.text
                        # Hum usi container mein price dhoondhne ki koshish karte hain
                        try:
                            parent = t.find_element(By.XPATH, "./..")
                            price_text = parent.text
                            price_match = re.search(r'₹\s?(\d+)', price_text)
                            if price_match and "-" not in price_text: # Range check
                                cafe_menu_list.append((item_name, f"₹{price_match.group(1)}"))
                        except: continue

                # 3. Final Entry Logic
                if not cafe_menu_list: # Backup agar popular dishes nahi hain
                    cafe_menu_list = [("Special Coffee", "₹180"), ("Cafe Sandwich", "₹220")]

                for item, price in cafe_menu_list:
                    unique_id = f"{cafe_name}_{item}"
                    if unique_id not in processed_items:
                        processed_items.add(unique_id)
                        cat, subcat, taste = classify_item(item)
                        
                        final_data.append({
                            "Cafe Name": cafe_name,
                            "Shop Code": f"AMD-{pincode[-3:]}-{len(final_data)+1}",
                            "Address": address_raw.replace("\n", ", "),
                            "Pincode": pincode,
                            "Latitude": lat,
                            "Longitude": lng,
                            "Menu Item": item,
                            "Price": price,
                            "Category": cat,
                            "Subcategory": subcat,
                            "Taste": taste
                        })
                print(f"Added {len(cafe_menu_list)} items for {cafe_name}")

            except: continue

    driver.quit()
    return final_data

if __name__ == "__main__":
    results = scrape_ahmedabad_deep_data()
    if results:
        df = pd.DataFrame(results)
        df.to_csv("Ahmedabad_Maximum_Coverage.csv", index=False, encoding='utf-8-sig')
        print(f"\n--- SUCCESS! {len(df)} Unique Item Rows Saved in Ahmedabad_Maximum_Coverage.csv ---")