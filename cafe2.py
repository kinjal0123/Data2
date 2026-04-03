import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def classify_item_details(item_name):
    name = item_name.lower()
    if any(x in name for x in ["coffee", "latte", "cappuccino", "espresso"]):
        return "Beverages", "Coffee", "Bold/Bitter"
    elif any(x in name for x in ["pizza", "pasta", "burger", "sandwich"]):
        return "Food", "Continental", "Savory"
    elif any(x in name for x in ["shake", "dessert", "cake", "brownie"]):
        return "Food & Bev", "Dessert", "Sweet"
    return "Food", "Cafe Snack", "Standard"

def scrape_exact_ahmedabad_data():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)
    
    # Area-wise search for full Ahmedabad
    queries = ["Best Cafes in Sindhu Bhavan Road Ahmedabad", "Top Cafes in Bodakdev"]
    final_data = []
    seen_items = set()

    for query in queries:
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
        time.sleep(5)

        # Scroll logic
        scroll_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        for _ in range(3):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scroll_div)
            time.sleep(2)

        cafes = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for cafe in cafes[:10]: # Testing for top 10
            try:
                cafe_name = cafe.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", cafe)
                time.sleep(4)

                # --- Exact Price Extraction Jugad ---
                # Hum un containers ko target kar rahe hain jisme Dish aur Price dono hote hain
                # Google Maps structure: .fontHeadlineSmall (Dish) aur uske bagal/niche wali price
                
                # Sabse pehle "Menu" section dhoondho (Text based)
                dish_containers = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Dish")] | //div[@class="m6QErb "]')
                
                temp_menu = []
                for container in dish_containers:
                    text = container.text
                    # Regex to find: Item Name followed by EXACT Price (e.g. Pasta ₹250)
                    match = re.search(r'([a-zA-Z\s]+)\n?₹\s?(\d{2,4})', text)
                    if match:
                        item_name = match.group(1).strip()
                        item_price = f"₹{match.group(2)}"
                        # Range check (Double check to avoid ₹200-400)
                        if "-" not in text:
                            temp_menu.append((item_name, item_price))

                # Agar containers nahi mile, toh "Popular Dishes" section scan karein
                if not temp_menu:
                    names = driver.find_elements(By.CLASS_NAME, "fontHeadlineSmall")
                    prices = driver.find_elements(By.XPATH, "//*[contains(text(), '₹')]")
                    for n, p in zip(names, prices):
                        if "₹" in p.text and "-" not in p.text:
                            temp_menu.append((n.text, p.text))

                # Basic Details
                address = driver.find_element(By.XPATH, '//button[@data-item-id="address"]').text
                pincode = re.search(r'\b\d{6}\b', address).group(0) if re.search(r'\b\d{6}\b', address) else "380000"
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', driver.current_url)

                for item, price in temp_menu:
                    unique_key = f"{cafe_name}-{item}"
                    if unique_key in seen_items: continue
                    seen_items.add(unique_key)

                    cat, sub_cat, taste = classify_item_details(item)
                    final_data.append({
                        "Cafe Name": cafe_name,
                        "Shop Code": f"AMD-{pincode[-3:]}-{len(final_data)+1}",
                        "Address": address.replace("\n", " "),
                        "Pincode": pincode,
                        "Latitude": coords.group(1) if coords else "N/A",
                        "Longitude": coords.group(2) if coords else "N/A",
                        "Menu Item": item,
                        "Price": price,
                        "Category": cat,
                        "Subcategory": sub_cat,
                        "Taste": taste
                    })
                print(f"Verified: {cafe_name} ({len(temp_menu)} exact items)")

            except: continue

    driver.quit()
    return final_data

if __name__ == "__main__":
    results = scrape_exact_ahmedabad_data()
    df = pd.DataFrame(results)
    df.to_csv("Ahmedabad_Exact_Prices.csv", index=False, encoding='utf-8-sig')
    print(f"\n--- SUCCESS! {len(df)} Exact Items Saved. ---")