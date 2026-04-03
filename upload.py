import gspread
import pandas as pd
import os
import time
from google.oauth2.service_account import Credentials


scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
JSON_FILE = 'credentials.json' 

try:
    creds = Credentials.from_service_account_file(JSON_FILE, scopes=scope)
    client = gspread.authorize(creds)
    print("--- Authenticated Successfully ---")
except Exception as e:
    print(f"Error: JSON file not found or credentials are wrong. {e}")
    exit()

sheet_id = '1sMafGhN7jEd7hbKB6j8jtccpN6nmYrtnWDY6fb1Fb4o'
spreadsheet = client.open_by_key(sheet_id)

#    Target Tab: "Shop Import"
try:
    worksheet = spreadsheet.worksheet("Shop Import")
except gspread.exceptions.WorksheetNotFound:
    print("Error: not found 'shop import' tab.")
    exit()

# List of  8 CSV files
files_to_upload = [
    "Navrangpura_Full_Data.csv", "Prahladnagar_Full_Data.csv",
    "Ambawadi_Full_Data.csv", "Maninagar_Full_Data.csv",
    "Gurukul_Road_Full_Data.csv", "SG_Highway_Full_Data.csv",
    "Boston_Full_Data.csv", "vastral_Full_Area_Final.csv"
]

print("\nStarting Upload to 'shop import'...")

for file_name in files_to_upload:
    if os.path.exists(file_name):
        print(f"Processing: {file_name}...")
        try:
            # Read CSV and handle empty cells
            df = pd.read_csv(file_name)
            df = df.fillna("")
            
            # Convert to list of lists 
            data_rows = df.values.tolist()
            
            if data_rows:
                # 'append_rows' ensures data is added at the end (No overwrite)
                worksheet.append_rows(data_rows)
                print(f"-> Successfully added {len(data_rows)} rows.")
                time.sleep(2) # To avoid hitting Google API limits
            else:
                print(f"-> {file_name} is empty, skipping.")
        except Exception as e:
            print(f"-> Error reading {file_name}: {e}")
    else:
        print(f"-> Skip: {file_name} not found in current folder.")

print("\n All Done!")