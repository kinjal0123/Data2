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


def deep_scroll(driver, container, pause=3.0):
    last_height = 0
    stable_count = 0
    print("⏳ Hyde Park area scan ho raha hai (Deep Scan)...")

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


def scrape_hyde_park(max_entries=55):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    wait = WebDriverWait(driver, 25)

    search_terms = [
        "Coffee shops in Hyde Park Boston MA",
        "Cafes in Hyde Park Boston MA",
        "Bakery cafes Hyde Park Boston"
    ]

    final_list = []
    seen_names = set()
    last_scraped_address = ""

    for query in search_terms:
        print(f"\n🚀 Searching: {query}")
        driver.get("https://www.google.com/maps/search/" + query.replace(" ", "+"))
        time.sleep(8)

        container = get_scroll_container(driver)
        if container is None:
            continue

        deep_scroll(driver, container)

        cards = driver.find_elements(By.XPATH, '//div[contains(@class,"Nv2PK")]')

        for card in cards:

            if len(final_list) >= max_entries:
                print(f"⚡ Max {max_entries} Hyde Park entries collected.")
                break

            try:
                link_element = card.find_element(By.XPATH, './/a[contains(@href,"/maps/place/")]')

                name = card.get_attribute("aria-label") or link_element.get_attribute("aria-label")
                if not name or name in seen_names:
                    continue

                # Category validation
                try:
                    cat_elements = card.find_elements(By.CLASS_NAME, "W4Efsd")
                    category_text = ""

                    for el in cat_elements:
                        if el.text and not any(ch.isdigit() for ch in el.text):
                            category_text = el.text.lower()
                            break

                    is_cafe = any(w in category_text for w in ["cafe", "coffee", "espresso", "roastery"])
                    if not is_cafe:
                        if not any(w in name.lower() for w in ["cafe", "coffee"]):
                            continue
                except:
                    pass

                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                time.sleep(1)
                link_element.click()
                time.sleep(3)

                # Address with retry
                full_address = "N/A"
                address_xpath = '//button[@data-item-id="address"]//div[contains(@class,"Io6YTe")]'

                for _ in range(15):
                    try:
                        temp = driver.find_element(By.XPATH, address_xpath).text.strip()
                        if temp and temp != last_scraped_address:
                            full_address = temp
                            last_scraped_address = full_address
                            break
                    except:
                        pass
                    time.sleep(0.7)

                if full_address == "N/A":
                    continue

                # Lat/Lon from URL
                lat, lon = "N/A", "N/A"

                for _ in range(10):
                    url = driver.current_url
                    match = re.search(r'@([-?\d.]+),([-?\d.]+)', url)
                    if match:
                        lat, lon = match.group(1), match.group(2)
                        break
                    time.sleep(0.5)

                # Zip code
                zip_match = re.search(r'\b\d{5}\b', full_address)
                zip_code = zip_match.group(0) if zip_match else "02136"

                # Images
                images = []
                try:
                    photo_elements = driver.find_elements(
                        By.XPATH,
                        '//img[contains(@src,"lh3.googleusercontent.com")]'
                    )
                    images = [img.get_attribute("src") for img in photo_elements[:5]]
                except:
                    pass

                final_list.append({
                    "Name": name,
                    "Shop Code": f"BOS-HP-{100 + len(final_list) + 1}",
                    "Latitude": lat,
                    "Longitude": lon,
                    "Full Address": full_address,
                    "Zip Code": zip_code,
                    "Images": " | ".join(images)
                })

                seen_names.add(name)
                print(f"✔ Saved: {name}")

            except:
                continue

        if len(final_list) >= max_entries:
            break

    driver.quit()
    return final_list


if __name__ == "__main__":
    data = scrape_hyde_park()
    if data:
        df = pd.DataFrame(data)
        file_name = "Hyde_Park_Cafes_Final.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"\n✅ DONE! {len(df)} entries saved in '{file_name}'")
        print("Columns: Name, Shop Code, Latitude, Longitude, Full Address, Zip Code, Images")
    else:
        print("⚠ Data fetch nahi ho saka.")