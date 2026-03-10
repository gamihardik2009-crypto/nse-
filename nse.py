import requests
import json
import time
from datetime import datetime

# User input
target_strike = input("Enter target NIFTY strike (e.g., 24100): ")
interval = float(input("Enter time interval in seconds (e.g., 2): "))

# Convert strike to Groww symbol
ce_symbol = f"NIFTY26310{target_strike}CE"
pe_symbol = f"NIFTY26310{target_strike}PE"

url = "https://groww.in/v1/api/stocks_fo_data/v1/tr_live_prices/exchange/NSE/segment/FNO/latest_prices_batch"
headers = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'origin': 'https://groww.in',
    'referer': 'https://groww.in/options/nifty',
    'user-agent': 'Mozilla/5.0',
    'x-app-id': 'growwWeb'
}

# Print table header
print(f"{'Time':<10} | {'CE_LTP':<7} {'CE_%':<7} | {'PE_LTP':<7} {'PE_%':<7}")
print("-"*50)

# Fetch loop
while True:
    payload = json.dumps([ce_symbol, pe_symbol])
    response = requests.post(url, headers=headers, data=payload)
    data = response.json()

    ce = data.get(ce_symbol, {})
    pe = data.get(pe_symbol, {})

    ce_ltp = ce.get("ltp", 0)
    pe_ltp = pe.get("ltp", 0)
    ce_open = ce.get("open", 1)  # avoid div by zero
    pe_open = pe.get("open", 1)

    # Calculate % difference from open
    ce_diff = round((ce_ltp - ce_open) / ce_open * 100, 2)
    pe_diff = round((pe_ltp - pe_open) / pe_open * 100, 2)

    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"{current_time:<10} | {ce_ltp:<7} {ce_diff:<7} | {pe_ltp:<7} {pe_diff:<7}")

    time.sleep(interval)
