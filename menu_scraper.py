import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import json

ua = UserAgent()

def fetch_html(url):
    headers = {"User-Agent": ua.random}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        return None
    return None

# -------------------------------
# Yelp Scraper
# -------------------------------
def scrape_yelp_menu(cafe_name, zipcode):
    query = cafe_name.replace(" ", "+")
    search_url = f"https://www.yelp.com/search?find_desc={query}&find_loc={zipcode}"
    html = fetch_html(search_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one("a.css-1m051bw")
    if not link:
        return None

    business_url = "https://www.yelp.com" + link.get("href") + "?osq=menu"
    html = fetch_html(business_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.menu-item")
    if not items:
        return None

    results = []
    for item in items:
        title = item.select_one(".menu-item-details h4")
        price = item.select_one(".menu-item-price-amount")
        desc = item.select_one(".menu-item-details .menu-item-description")
        results.append({
            "item": title.text.strip() if title else None,
            "price": price.text.strip() if price else None,
            "description": desc.text.strip() if desc else None,
            "source": "Yelp"
        })
    return results if results else None

# -------------------------------
# UberEats Scraper
# -------------------------------
def scrape_ubereats(cafe_name, zipcode):
    query = cafe_name.replace(" ", "%20")
    url = f"https://www.ubereats.com/api/getFeed?search={query}%20{zipcode}"
    html = fetch_html(url)
    if not html:
        return None

    try:
        data = json.loads(html)
    except:
        return None

    merchants = data.get("data", {}).get("results", [])
    if not merchants:
        return None

    uuid = merchants[0].get("uuid")
    if not uuid:
        return None

    menu_url = f"https://www.ubereats.com/api/getMenu?uuid={uuid}"
    resp = fetch_html(menu_url)
    if not resp:
        return None

    data = json.loads(resp)
    items = []
    for section in data.get("sections", []):
        for item in section.get("items", []):
            items.append({
                "item": item.get("title"),
                "price": item.get("price"),
                "description": item.get("description"),
                "category": section.get("title"),
                "source": "UberEats"
            })
    return items if items else None

# -------------------------------
# DoorDash Scraper
# -------------------------------
def scrape_doordash(cafe_name, zipcode):
    query = cafe_name.replace(" ", "%20")
    url = f"https://www.doordash.com/api/search/store/?q={query}&zip={zipcode}"
    html = fetch_html(url)
    if not html:
        return None

    try:
        data = json.loads(html)
    except:
        return None

    if not data.get("stores"):
        return None

    store = data["stores"][0]
    merchant_id = store.get("store_id")
    if not merchant_id:
        return None

    menu_url = f"https://www.doordash.com/api/merchant/{merchant_id}/menu/"
    resp = fetch_html(menu_url)
    if not resp:
        return None

    data = json.loads(resp)
    items = []
    for section in data.get("menu_categories", []):
        cat_name = section.get("name")
        for item in section.get("items", []):
            items.append({
                "item": item.get("name"),
                "price": item.get("price"),
                "description": item.get("description"),
                "category": cat_name,
                "source": "DoorDash"
            })
    return items if items else None

# -------------------------------
# Universal wrapper
# -------------------------------
def get_menu(cafe_name, zipcode):
    print(f"\nSearching menu for: {cafe_name} ({zipcode})")

    # Priority 1: UberEats
    data = scrape_ubereats(cafe_name, zipcode)
    if data:
        print("→ Found via UberEats")
        return data

    # Priority 2: DoorDash
    data = scrape_doordash(cafe_name, zipcode)
    if data:
        print("→ Found via DoorDash")
        return data

    # Priority 3: Yelp
    data = scrape_yelp_menu(cafe_name, zipcode)
    if data:
        print("→ Found via Yelp")
        return data

    print("→ Menu not found on any source")
    return None