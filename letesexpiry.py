import requests
import json
import time
import re
from datetime import datetime

interval = float(input("Enter refresh time (seconds): "))

# -------- HEADERS --------
headers = {
    "accept": "application/json, text/plain, */*",
    "referer": "https://groww.in/indices/nifty",
    "user-agent": "Mozilla/5.0",
    "x-app-id": "growwWeb"
}

# -------- NIFTY API --------
nifty_url = "https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/NIFTY"

# -------- OPTION API --------
option_url = "https://groww.in/v1/api/stocks_fo_data/v1/tr_live_prices/exchange/NSE/segment/FNO/latest_prices_batch"

# -------- GET LATEST EXPIRY --------
expiry_page = "https://groww.in/options/nifty"

r = requests.get(expiry_page, headers=headers)
html = r.text

matches = re.findall(r'NIFTY(\d{5})\d{4,5}(CE|PE)', html)
latest_expiry = matches[0][0]

print("Latest Expiry Code:", latest_expiry)

# -------- Get NIFTY OPEN --------
r = requests.get(nifty_url, headers=headers)
data = r.json()

nifty_open = data["open"]
atm_strike = round(nifty_open / 50) * 50

ce_symbol = f"NIFTY{latest_expiry}{atm_strike}CE"
pe_symbol = f"NIFTY{latest_expiry}{atm_strike}PE"

# -------- Get CE/PE OPEN --------
payload = json.dumps([ce_symbol, pe_symbol])
r2 = requests.post(option_url, headers=headers, data=payload)
option_data = r2.json()

ce_open = option_data.get(ce_symbol, {}).get("open", 0)
pe_open = option_data.get(pe_symbol, {}).get("open", 0)

print("\nNIFTY OPEN:", nifty_open)
print("ATM Strike:", atm_strike)
print("Tracking:", ce_symbol, "/", pe_symbol)
print("CE Open:", ce_open)
print("PE Open:", pe_open, "\n")

print(f"{'Time':<10} {'NIFTY':<8} | {'CE_LTP':<7} {'CE_%':<7} | {'PE_LTP':<7} {'PE_%':<7}")
print("-"*65)

while True:

    r = requests.get(nifty_url, headers=headers)
    data = r.json()
    nifty_ltp = data["value"]

    payload = json.dumps([ce_symbol, pe_symbol])
    r2 = requests.post(option_url, headers=headers, data=payload)
    option_data = r2.json()

    ce = option_data.get(ce_symbol, {})
    pe = option_data.get(pe_symbol, {})

    ce_ltp = ce.get("ltp", 0)
    pe_ltp = pe.get("ltp", 0)

    ce_diff = round((ce_ltp - ce_open) / ce_open * 100, 2)
    pe_diff = round((pe_ltp - pe_open) / pe_open * 100, 2)

    now = datetime.now().strftime("%H:%M:%S")

    print(f"{now:<10} {nifty_ltp:<8} | {ce_ltp:<7} {ce_diff:<7} | {pe_ltp:<7} {pe_diff:<7}")

    time.sleep(interval)
