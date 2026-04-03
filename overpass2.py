import requests
import csv
import json

def fetch_overpass_data():
    url = "https://overpass-api.de/api/interpreter"

    query = """
    [out:json][timeout:90];
    area["name"="Ahmedabad"]->.searchArea;

    (
      node["amenity"="cafe"](area.searchArea);
      way["amenity"="cafe"](area.searchArea);
      relation["amenity"="cafe"](area.searchArea);
    );

    out center;
    """

    response = requests.post(url, data={'data': query})
    response.raise_for_status()
    return response.json()


def parse_to_csv(osm_json, output_file="cafes.csv"):
    shops = osm_json.get("elements", [])

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "lat", "lon", "addr", "phone", "website"])

        for s in shops:
            tags = s.get("tags", {})

            # coordinates
            lat = s.get("lat") or s.get("center", {}).get("lat")
            lon = s.get("lon") or s.get("center", {}).get("lon")

            writer.writerow([
                tags.get("name", ""),
                lat,
                lon,
                tags.get("addr:full", tags.get("addr:housenumber", "")),
                tags.get("phone", ""),
                tags.get("website", "")
            ])

    print(f"File created: {output_file} | Total: {len(shops)}")


if __name__ == "__main__":
    data = fetch_overpass_data()
    parse_to_csv(data)