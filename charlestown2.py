import pandas as pd
import time
import os
from playwright.sync_api import sync_playwright
import playwright_stealth

def scrape_cafe_menu(cafe_name, city, shop_code):
    menu_data = []
    
    with sync_playwright() as p:
        # Browser launch (headless=False taaki aap process dekh sakein)
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Bot detection bypass
        playwright_stealth.stealth_sync(page)

        try:
            # Yelp search query (Name + City for accuracy)
            search_url = f"https://www.yelp.com/search?find_desc={cafe_name.replace(' ', '+')}&find_loc={city.replace(' ', '+')}"
            print(f"Searching for: {cafe_name}")
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            # Pehle business result par click karein
            first_result = page.query_selector('a[href*="/biz/"]')
            if first_result:
                first_result.click()
                time.sleep(3)
                
                # "Full Menu" link dhundein
                full_menu_link = page.query_selector('a:has-text("Full Menu")')
                if full_menu_link:
                    full_menu_link.click()
                    time.sleep(3)

                # Extraction Logic (Categories, Items, Prices, Descriptions)
                sections = page.query_selector_all('.menu-section')
                
                for section in sections:
                    # Category nikaalein
                    cat_elem = section.query_selector('h2, h3')
                    category = cat_elem.inner_text().strip() if cat_elem else "General"
                    
                    # Items nikaalein
                    items = section.query_selector_all('.menu-item-details')
                    for item in items:
                        name_elem = item.query_selector('h4')
                        price_elem = item.query_selector('.menu-item-price-amount')
                        desc_elem = item.query_selector('.menu-item-description')
                        
                        name = name_elem.inner_text().strip() if name_elem else "Unknown"
                        description = desc_elem.inner_text().strip() if desc_elem else "No description available"
                        
                        # Price formatting with $
                        raw_price = price_elem.inner_text().strip() if price_elem else "0.00"
                        formatted_price = f"${raw_price.replace('$', '').strip()}"
                        
                        # Simple Taste Tags based on keywords in name/description
                        desc_lower = description.lower()
                        name_lower = name.lower()
                        if any(x in desc_lower or x in name_lower for x in ["chocolate", "sugar", "sweet", "caramel", "syrup"]):
                            taste = "Sweet, Rich"
                        elif any(x in desc_lower or x in name_lower for x in ["spicy", "chili", "pepper", "hot"]):
                            taste = "Spicy, Zesty"
                        elif any(x in desc_lower or x in name_lower for x in ["bitter", "espresso", "dark", "strong"]):
                            taste = "Bold, Strong"
                        else:
                            taste = "Balanced, Fresh"
                        
                        # Sirf wahi data jo aapne maanga hai
                        menu_data.append({
                            "Shop Code": shop_code,
                            "Cafe Name": cafe_name,
                            "Item Name": name,
                            "Taste Tags": taste,
                            "Category": category,
                            "Sub-Category": "Standard", # Default value
                            "Price": formatted_price,
                            "Description": description
                        })
            else:
                print(f"Business page not found for {cafe_name}")

        except Exception as e:
            print(f"Error scraping {cafe_name}: {e}")
        
        browser.close()
    return menu_data

# --- Execution ---
input_csv = 'Charlestown_Cafes_Final_Fixed.csv'
output_csv = 'Cafe_Menu_Details_Only.csv'

if os.path.exists(input_csv):
    df = pd.read_csv(input_csv)
    final_list = []

    # Testing ke liye pehle 5 cafes (head(5)), baad mein ise hata dena
    for index, row in df.head(5).iterrows():
        print(f"\n[{index+1}/{len(df)}] Scraping: {row['Name']}")
        
        # City column input CSV se liya ja raha hai sirf search accuracy ke liye
        scraped_items = scrape_cafe_menu(row['Name'], row['City'], row['Shop Code'])
        
        if scraped_items:
            final_list.extend(scraped_items)

    # Result save karein
    if final_list:
        output_df = pd.DataFrame(final_list)
        # Reordering columns as per your requirement
        output_df = output_df[["Shop Code", "Cafe Name", "Item Name", "Taste Tags", "Category", "Sub-Category", "Price", "Description"]]
        output_df.to_csv(output_csv, index=False)
        print(f"\nDONE! File saved as: {output_csv}")
    else:
        print("\nNo data collected.")
else:
    print(f"Error: {input_csv} not found.")