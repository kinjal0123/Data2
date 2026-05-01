import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://en.wikipedia.org/wiki/List_of_cities_and_towns_in_the_San_Francisco_Bay_Area"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Wikipedia par cities wali table dhundna
table = soup.find('table', {'class': 'wikitable'})

cities = []
for row in table.find_all('tr')[1:]: # Pehli row header hoti hai
    columns = row.find_all(['td', 'th'])
    if columns:
        city_name = columns[0].text.strip()
        cities.append(city_name)

# Data ko display karna
print(cities)

# Agar aapko ise CSV mein save karna hai
# df = pd.DataFrame(cities, columns=['City'])
# df.to_csv('bay_area_cities.csv', index=False)