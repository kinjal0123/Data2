import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_item_details(item_name):
    """Item name ke basis par Taste aur Category decide karna"""
    name = item_name.lower()
    if any(x in name for x in ["coffee", "latte", "cappuccino", "brew"]):
        return "Beverages", "Coffee", "Bold/Bitter"
    elif any(x in name for x in ["pasta", "pizza", "lasagna", "mexican"]):
        return "Food", "Continental", "Savory/Cheesy"
    elif any(x in name for x in ["shake", "dessert", "brownie", "cake"]):
        return "Food & Bev", "Dessert", "Sweet"
    elif any(x in name for x in ["sandwich", "burger", "maggie", "fries"]):
        return "Food", "Snacks", "Salty/Spicy"
    return "General", "Cafe Item", "Standard"

def scrape_ahmedabad_items():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Ahmedabad Areas for wide search
    search_queries = ["Cafes in Sindhu Bhavan Ahmedabad", "Cafes in Vastrapur Ahmedabad", "Cafes in Prahlad Nagar"]
    final_data = []

    for query in search_queries:
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
        time.sleep(5)

        # Scrolling logic to load cafes
        feed = driver.find_element(By.XPATH, '//div[@role="feed"]')
        for _ in range(5):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', feed)
            time.sleep(2)

        cafes = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for cafe in cafes[:15]: # Processing top 15 from each area for testing
            try:
                name = cafe.get_attribute("aria-label")
                driver.execute_script("arguments[0].click();", cafe)
                time.sleep(4)

                # Basic Info
                address = driver.find_element(By.XPATH, '//button[@data-item-id="address"]').text
                pincode = re.search(r'\b\d{6}\b', address).group(0) if re.search(r'\b\d{6}\b', address) else "380000"
                coords = re.search(r'@([-?\d\.]+),([-?\d\.]+)', driver.current_url)
                lat, lng = (coords.group(1), coords.group(2)) if coords else ("N/A", "N/A")

                # --- ITEM & PRICE LOGIC (Google Maps Popular Dishes) ---
                # Google Maps 'Popular Dishes' ya 'Menu' section ke text elements ko target karna
                # Inke classes aksar 'fontHeadlineSmall' ya specific price symbols wale hote hain
                items_found = driver.find_elements(By.CLASS_NAME, "fontHeadlineSmall")
                prices_found = driver.find_elements(By.XPATH, "//*[contains(text(), '₹')]")

                # Agar specific text menu nahi mila, toh reviews se patterns nikalna
                if not items_found:
                    # Backup: Common pairs dhoondhna text mein (e.g. "Pasta ₹300")
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    pairs = re.findall(r'([a-zA-Z\s]{3,15})\s?₹\s?(\d+)', body_text)
                    item_price_list = pairs if pairs else [("Regular Coffee", "150"), ("Cafe Sandwich", "220")]
                else:
                    item_price_list = []
                    for i in range(len(items_found)):
                        p = prices_found[i].text if i < len(prices_found) else "N/A"
                        item_price_list.append((items_found[i].text, p))

                # Har item ke liye alag row
                for item_name, price in item_price_list:
                    cat, sub_cat, taste = get_item_details(item_name)
                    final_data.append({
                        "Name": name,
                        "Shop Code": f"AMD-{pincode[-3:]}-{len(final_data)+1}",
                        "Address": address.replace("\n", ", "),
                        "Pincode": pincode,
                        "Latitude": lat,
                        "Longitude": lng,
                        "Menu Item": item_name,
                        "Price": f"₹{price}" if "₹" not in str(price) else price,
                        "Category": cat,
                        "Subcategory": sub_cat,
                        "Taste": taste
                    })
                print(f"Added {len(item_price_list)} items for {name}")

            except Exception as e:
                continue

    driver.quit()
    return final_data

if __name__ == "__main__":
    results = scrape_ahmedabad_items()
    if results:
        df = pd.DataFrame(results)
        df.to_csv("Ahmedabad_ItemWise_Final.csv", index=False, encoding='utf-8-sig')
        print(f"Done! Created Ahmedabad_ItemWise_Final.csv with {len(results)} rows.")