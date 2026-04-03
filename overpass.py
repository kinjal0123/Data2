import requests
import pandas as pd
import re

def fetch_pure_cafe_data():
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Bounding Box covering Ahmedabad + Gandhinagar
    bbox = "22.85,72.35,23.40,72.80"
    
    # Query: Sirf Cafe aur Coffee/Tea specific tags
    overpass_query = f"""
    [out:json][timeout:180];
    (
      // 1. All primary Cafes
      node["amenity"="cafe"]({bbox});
      way["amenity"="cafe"]({bbox});
      
      // 2. Specific Coffee Shops & Tea points
      node["cuisine"~"coffee_shop|tea|beverages"]({bbox});
      way["cuisine"~"coffee_shop|tea|beverages"]({bbox});
    );
    out center;
    """

    print("Fetching Pure Cafe & Coffee Shop data... (Target: 1000+ points)")
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=120)
        # Backup mirror agar main server busy ho
        if response.status_code != 200:
            response = requests.get("https://overpass.kumi.systems/api/interpreter", params={'data': overpass_query}, timeout=120)
        
        data = response.json()
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

    cafes_list = []
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        name = tags.get('name', "Unnamed Cafe")
        
        # Skip unnamed or non-relevant entries
        if name == "Unnamed Cafe" or "restaurant" in name.lower():
            continue

        lat = element.get('lat') or element.get('center', {}).get('lat')
        lon = element.get('lon') or element.get('center', {}).get('lon')
        
        # Address & Pincode
        street = tags.get('addr:street', '')
        suburb = tags.get('addr:suburb', '')
        city = tags.get('addr:city', 'Ahmedabad/GNR')
        pincode = tags.get('addr:postcode', 'N/A')
        
        full_address = f"{tags.get('addr:housename', '')} {tags.get('addr:housenumber', '')} {street} {suburb} {city}".strip()
        
        # City Tagging for Shop Code
        city_tag = "GNR" if lat > 23.16 else "AMD"

        cafes_list.append({
            "Name": name,
            "Shop Code": f"{city_tag}-CF-{1000 + len(cafes_list) + 1}",
            "Latitude": lat,
            "Longitude": lon,
            "Full Address": full_address if full_address else f"{suburb}, {city}",
            "Pincode": pincode,
            "Type": tags.get('amenity', 'Cafe'),
            "Cuisine": tags.get('cuisine', 'Coffee/Tea')
        })

    return cafes_list

if __name__ == "__main__":
    results = fetch_pure_cafe_data()
    if results:
        df = pd.DataFrame(results)
        # Final cleanup: Remove duplicates
        df = df.drop_duplicates(subset=['Latitude', 'Longitude'])
        
        file_name = "Amd_Gnr_Pure_Cafes.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        
        print(f"\n--- SUCCESS! ---")
        print(f"Total Pure Cafes Found: {len(df)}")
        print(f"Data saved in: {file_name}")
    else:
        print("Data fetch nahi ho paya. Ek baar phir se run karein.")