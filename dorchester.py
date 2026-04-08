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

def deep_scroll(driver, container, pause=2.8):
    last_height = 0
    stable_count = 0
    print("⏳ Scanning results...")

    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
        time.sleep(pause)

        new_height = driver.execute_script("return arguments[0].scrollHeight", container)
        if new_height == last_height:
            stable_count += 1
            if stable_count >= 4:
                break
        else:
            stable_count = 0

        last_height = new_height

def scrape_dorchester_accurate():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    # 🔥 Dorchester search terms
    search_terms = [
        "Coffee shops in Dorchester Boston MA",
        "Cafes in Dorchester Boston MA",
        "Dorchester Boston coffee",
        "Dorchester MA cafes",
        "Coffee near Dorchester MA",
        "Best cafes in Dorchester MA"
    ]

    final_list = []
    seen_names = set()
    last_scraped_address = ""

    for query in search_terms:
        print(f"\n🚀 Searching: {query}")
        driver.get("https://www.google.com/maps/search/" + query.replace(" ", "+"))
        time.sleep(6)

        container = get_scroll_container(driver)
        if container is None:
            print("⚠ Could not detect scroll container. Skipping query.")
            continue

        deep_scroll(driver, container)

        cards = driver.find_elements(
            By.XPATH,
            '//a[contains(@href, "/maps/place/")]/ancestor::div[contains(@class,"Nv2PK")]'
        )

        for card in cards:
            try:
                link_element = card.find_element(By.XPATH, './/a[contains(@href, "/maps/place/")]')
                name = card.get_attribute("aria-label") or link_element.get_attribute("aria-label")

                if not name or name in seen_names:
                    continue

                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                time.sleep(1)
                link_element.click()

                # ✅ Address retry loop with longer wait
                full_address = "N/A"
                address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "Io6YTe")]'

                for _ in range(15):  # increased attempts
                    try:
                        temp_addr = driver.find_element(By.XPATH, address_xpath).text.strip()
                        if temp_addr and temp_addr != last_scraped_address:
                            full_address = temp_addr
                            last_scraped_address = full_address
                            break
                    except:
                        pass
                    time.sleep(0.7)

                if full_address == "N/A":
                    continue

                # Lat/Lon
                lat, lon = "N/A", "N/A"
                for _ in range(10):
                    current_url = driver.current_url
                    match = re.search(r'@([-?\d.]+),([-?\d.]+)', current_url)
                    if match:
                        lat = match.group(1)
                        lon = match.group(2)
                        break
                    time.sleep(0.5)

                # Zip code
                zip_match = re.search(r'\b\d{5}\b', full_address)
                zip_code = zip_match.group(0) if zip_match else "02125"  # Dorchester ZIP

                # Images
                images = []
                try:
                    photo_elements = driver.find_elements(
                        By.XPATH, '//img[contains(@src,"lh3.googleusercontent.com")]'
                    )
                    images = [img.get_attribute("src") for img in photo_elements[:5]]
                except:
                    pass

                final_list.append({
                    "Name": name,
                    "Shop Code": f"BOS-DOR-{100 + len(final_list) + 1}",
                    "Latitude": lat,
                    "Longitude": lon,
                    "Full Address": full_address,
                    "Zip Code": zip_code,
                    "City": "Boston",
                    "State": "MA",
                    "Images": " | ".join(images)
                })

                seen_names.add(name)
                print(f"✔ Saved: {name} | Addr: {full_address[:45]}...")

            except Exception as e:
                continue

    driver.quit()
    return final_list

if __name__ == "__main__":
    data = scrape_dorchester_accurate()

    if data:
        df = pd.DataFrame(data)
        file_name = "Dorchester_Cafes_Final_Fixed.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"\n✅ SUCCESS! {len(df)} entries saved in '{file_name}'")
    else:
        print("⚠ Data fetch nahi ho saka.")