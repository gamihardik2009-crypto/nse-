import requests
import json
import time
import re
from datetime import datetime

# -------- USER INPUT --------

target_strike = input("Enter target NIFTY strike (e.g., 24100): ")
interval = float(input("Enter time interval in seconds (e.g., 2): "))


headers = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'origin': 'https://groww.in',
    'referer': 'https://groww.in/options/nifty',
    'user-agent': 'Mozilla/5.0',
    'x-app-id': 'growwWeb'
}


# -------- DETECT LATEST EXPIRY --------

expiry_page = "https://groww.in/options/nifty"

r = requests.get(expiry_page, headers=headers)

matches = re.findall(r'NIFTY(\d{5})\d{4,5}(CE|PE)', r.text)

latest_expiry = matches[0][0]


# -------- FORMAT EXPIRY DATE --------

year = "20" + latest_expiry[0:2]
month = latest_expiry[2]
day = latest_expiry[3:5]

month_map = {
    "1":"Jan","2":"Feb","3":"Mar","4":"Apr","5":"May","6":"Jun",
    "7":"Jul","8":"Aug","9":"Sep","O":"Oct","N":"Nov","D":"Dec"
}

month_name = month_map.get(month, month)

expiry_date = f"{day} {month_name} {year}"


print("\nLatest Expiry Code:", latest_expiry)
print("Expiry Date:", expiry_date)


# -------- SYMBOLS --------

ce_symbol = f"NIFTY{latest_expiry}{target_strike}CE"
pe_symbol = f"NIFTY{latest_expiry}{target_strike}PE"


url = "https://groww.in/v1/api/stocks_fo_data/v1/tr_live_prices/exchange/NSE/segment/FNO/latest_prices_batch"


print()
print("Tracking:", ce_symbol, "/", pe_symbol)
print()


# -------- TABLE HEADER --------

print(f"{'Time':<10} | {'CE_LTP':<7} {'CE_%':<7} | {'PE_LTP':<7} {'PE_%':<7}")
print("-"*50)


# -------- LOOP --------

try:

    while True:

        payload = json.dumps([ce_symbol, pe_symbol])

        response = requests.post(url, headers=headers, data=payload)

        data = response.json()


        ce = data.get(ce_symbol, {})
        pe = data.get(pe_symbol, {})


        ce_ltp = ce.get("ltp", 0)
        pe_ltp = pe.get("ltp", 0)

        ce_open = ce.get("open", 1)
        pe_open = pe.get("open", 1)


        ce_diff = round((ce_ltp - ce_open) / ce_open * 100, 2)
        pe_diff = round((pe_ltp - pe_open) / pe_open * 100, 2)


        current_time = datetime.now().strftime("%H:%M:%S")


        print(f"{current_time:<10} | {ce_ltp:<7} {ce_diff:<7} | {pe_ltp:<7} {pe_diff:<7}")


        time.sleep(interval)


except KeyboardInterrupt:

    print("\nScript stopped by user.")
