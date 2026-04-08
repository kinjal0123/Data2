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

def scrape_boston(city_code="BOS"):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 25)

    neighborhoods = [
        "Allston Boston MA", "Back Bay Boston MA", "Bay Village Boston MA", "Beacon Hill Boston MA",
        "Brighton Boston MA", "Charlestown Boston MA", "Chinatown Boston MA", "Leather District Boston MA",
        "Dorchester Boston MA", "Downtown Boston MA", "East Boston MA", "Fenway Kenmore Boston MA"
    ]

    final_list = []
    used_names = set()

    for area in neighborhoods:
        query = f"Cafes Coffee Shops in {area}"
        print(f"\n Scanning: {area}")
        driver.get("https://www.google.com/maps/search/" + query.replace(" ", "+"))
        time.sleep(8)

        container = get_scroll_container(driver)
        if container is None:
            print(" Scroll container not found")
            continue

        seen_cards = set()
        neighborhood_count = 0

        while True:
            deep_scroll(driver, container, pause=2)
            cards = driver.find_elements(By.XPATH, '//div[contains(@class,"Nv2PK")]')
            new_cards = [c for c in cards if c not in seen_cards]
            if not new_cards:
                break
            seen_cards.update(new_cards)

            for card in new_cards:
                try:
                    name = card.get_attribute("aria-label")
                    if not name or name in used_names:
                        continue
                    used_names.add(name)

                    # Defaults
                    coords = ("N/A", "N/A")
                    address = area
                    images = []

                    # Coordinates from href
                    try:
                        a_tag = card.find_element(By.TAG_NAME, "a")
                        href = a_tag.get_attribute("href")
                        c = re.search(r'@([-?\d.]+),([-?\d.]+)', href)
                        if c:
                            coords = (c.group(1), c.group(2))
                    except: pass

                    # Address
                    try:
                        addr_el = card.find_element(By.CLASS_NAME, "W4Efsd")
                        address = addr_el.text.strip()
                    except: pass

                    # Click card to get panel info
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", card)
                    time.sleep(3)

                    # Coordinates from URL
                    try:
                        url = driver.current_url
                        c = re.search(r'@([-?\d.]+),([-?\d.]+)', url)
                        if c:
                            coords = (c.group(1), c.group(2))
                    except: pass

                    # Address 
                    try:
                        addr_el = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id="address"]'))
                        )
                        address = addr_el.text.strip()
                    except: pass

                    # ZIP
                    zip_match = re.search(r'\b\d{5}\b', address)
                    zip_code = zip_match.group(0) if zip_match else ""

                    # Images
                    try:
                        photo_elements = driver.find_elements(By.XPATH,
                            '//img[contains(@src,"https://lh3.googleusercontent.com")]')
                        for img_el in photo_elements[:10]:
                            src = img_el.get_attribute("src")
                            if src and src not in images:
                                images.append(src)
                    except: pass

                    final_list.append({
                        "Name": name,
                        "Shop Code": f"{city_code}-{100 + len(final_list) + 1}",
                        "Neighborhood": area.replace(" Boston MA", ""),
                        "Latitude": coords[0],
                        "Longitude": coords[1],
                        "Full Address": address,
                        "Zip Code": zip_code,
                        "City": "Boston",
                        "State": "MA",
                        "Images": images
                    })
                    neighborhood_count += 1
                    print(f"✔ {name} | Images: {len(images)} found")

                except:
                    continue

        print(f"Total cafés fetched in {area}: {neighborhood_count}")

    driver.quit()
    print(f"\n TOTAL unique cafés fetched across all neighborhoods: {len(final_list)}")
    return final_list

if __name__ == "__main__":
    data = scrape_boston("BOS")
    if data:
        df = pd.DataFrame(data)
        df.drop_duplicates(subset=["Name"], inplace=True)
        df.drop_duplicates(subset=["Latitude", "Longitude"], inplace=True)
        df.to_csv("Boston_Neighborhoods_Full_WithImages.csv", index=False)
        print(f"\n DONE! CSV saved with {len(df)} unique cafés")