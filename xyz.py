import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_scroll_container(driver):
    candidates = [
        '//div[@role="feed"]',
        '//div[contains(@class,"m6QErb") and contains(@class,"PsxyXe")]',
        '//div[contains(@class,"m6QErb") and contains(@class,"WNBkOb")]'
    ]
    for c in candidates:
        try:
            return driver.find_element(By.XPATH, c)
        except:
            continue
    return None

def deep_scroll(driver, container, pause=2.5):
    last_height = 0
    stable_count = 0
    print("⏳ Scrolling to load all cafes...")
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
        time.sleep(pause)
        new_height = driver.execute_script("return arguments[0].scrollHeight", container)
        if new_height == last_height:
            stable_count += 1
            if stable_count >= 3:
                break
        else:
            stable_count = 0
        last_height = new_height

def scrape_single_area(target_area, city_code="BOS"):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)

    final_list = []
    used_names = set()

    query = f"Cafes Coffee Shops in {target_area}"
    print(f"\n📍 Scanning: {target_area}")
    driver.get("https://www.google.com/maps/search/" + query.replace(" ", "+"))
    time.sleep(8)

    container = get_scroll_container(driver)
    if container is None:
        print("❌ Scroll container not found.")
        driver.quit()
        return []

    # Loading all results first
    deep_scroll(driver, container, pause=2)
    
    cards = driver.find_elements(By.XPATH, '//div[contains(@class,"Nv2PK")]')
    print(f"🔎 Found {len(cards)} results. Starting detailed extraction...")

    for card in cards:
        try:
            name = card.get_attribute("aria-label")
            if not name or name in used_names:
                continue
            
            # Initial Data
            coords = ("N/A", "N/A")
            address = target_area
            images = []

            # Coordinates from link
            try:
                href = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                c = re.search(r'@([-?\d.]+),([-?\d.]+)', href)
                if c: coords = (c.group(1), c.group(2))
            except: pass

            # Click for details
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", card)
            time.sleep(3)

            # Panel Info
            try:
                addr_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id="address"]')))
                address = addr_el.text.strip()
            except: pass

            zip_match = re.search(r'\b\d{5}\b', address)
            zip_code = zip_match.group(0) if zip_match else ""

            # Images (Top 5)
            try:
                photo_elements = driver.find_elements(By.XPATH, '//img[contains(@src,"https://lh3.googleusercontent.com")]')
                images = [img.get_attribute("src") for img in photo_elements[:5]]
            except: pass

            # Append to list
            final_list.append({
                "Name": name,
                "Shop Code": f"{city_code}-{100 + len(final_list) + 1}",
                "Neighborhood": target_area,
                "Latitude": coords[0],
                "Longitude": coords[1],
                "Full Address": address,
                "Zip Code": zip_code,
                "City": "Boston",
                "State": "MA",
                "Images": ", ".join(images) # Images ko string mein convert kiya taaki CSV mein load ho sake
            })
            used_names.add(name)
            print(f"✔ Saved: {name}")

        except Exception as e:
            print(f"Skipping a card due to: {e}")
            continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    # --- CONFIG ---
    area = "Allston Boston MA" 
    code = "BOS-AL"
    
    scraped_data = scrape_single_area(area, code)
    
    if scraped_data:
        try:
            print(f"\n Total cafes collected: {len(scraped_data)}")
            df = pd.DataFrame(scraped_data)
            
            # Deduplication
            df.drop_duplicates(subset=["Name"], inplace=True)
            
            # File saving with encoding fix
            file_name = f"{area.replace(' ', '_')}_Data.csv"
            df.to_csv(file_name, index=False, encoding='utf-8-sig')
            
            print(f" SUCCESS! Data saved to: {file_name}")
        except Exception as e:
            print(f"❌ Error while saving CSV: {e}")
    else:
        print("⚠ No data was fetched.")