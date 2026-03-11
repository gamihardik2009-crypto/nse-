import requests
import json
import time
import re
from datetime import datetime

# -------- USER INPUT --------
interval = float(input("Refresh time (seconds): "))
mode = input("Mode (buyer/seller): ").lower()
threshold = float(input("Threshold % (example 50): "))
oi_mode = int(input("OI Mode (1 = Total OI , 2 = OI Change): "))

# -------- HEADERS --------
headers = {
    "accept": "application/json, text/plain, */*",
    "referer": "https://groww.in/indices/nifty",
    "user-agent": "Mozilla/5.0",
    "x-app-id": "growwWeb"
}

# -------- URLS --------
nifty_url = "https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/NIFTY"
option_url = "https://groww.in/v1/api/stocks_fo_data/v1/tr_live_prices/exchange/NSE/segment/FNO/latest_prices_batch"

# -------- GET EXPIRY --------
expiry_page = "https://groww.in/options/nifty"

r = requests.get(expiry_page, headers=headers)
html = r.text
matches = re.findall(r'NIFTY(\d{5})\d{4,5}(CE|PE)', html)

latest_expiry = matches[0][0]
print("Latest Expiry:", latest_expiry)

# -------- GET NIFTY OPEN --------
r = requests.get(nifty_url, headers=headers)
data = r.json()

nifty_open = data["open"]
atm_strike = round(nifty_open / 50) * 50

ce_symbol = f"NIFTY{latest_expiry}{atm_strike}CE"
pe_symbol = f"NIFTY{latest_expiry}{atm_strike}PE"

# -------- GET CE/PE OPEN --------
payload = json.dumps([ce_symbol, pe_symbol])
r2 = requests.post(option_url, headers=headers, data=payload)
option_data = r2.json()

ce_open = option_data.get(ce_symbol, {}).get("open", 0)
pe_open = option_data.get(pe_symbol, {}).get("open", 0)

print("NIFTY OPEN:", nifty_open)
print("ATM STRIKE:", atm_strike)
print("Tracking:", ce_symbol, "/", pe_symbol)
print("CE OPEN:", ce_open)
print("PE OPEN:", pe_open)

print()

# -------- TABLE HEADER --------
print(f"{'Time':<9} {'NIFTY':<9} | {'CE':<7} {'CE%':<7} | {'PE':<7} {'PE%':<7} | {'R1':<6} {'R2':<6} {'R3':<6} | {'S1':<6} {'S2':<6} {'S3':<6} | RESULT")
print("-"*120)

# -------- FAKE OI STRUCTURE PLACEHOLDER --------
# (replace later with real OI API if needed)

R1 = atm_strike + 50
R2 = atm_strike + 100
R3 = atm_strike + 150

S1 = atm_strike - 50
S2 = atm_strike - 100
S3 = atm_strike - 150

# -------- LIVE LOOP --------
while True:

    # NIFTY PRICE
    r = requests.get(nifty_url, headers=headers)
    data = r.json()
    nifty_ltp = data["value"]

    # OPTION DATA
    payload = json.dumps([ce_symbol, pe_symbol])
    r2 = requests.post(option_url, headers=headers, data=payload)
    option_data = r2.json()

    ce = option_data.get(ce_symbol, {})
    pe = option_data.get(pe_symbol, {})

    ce_ltp = ce.get("ltp", 0)
    pe_ltp = pe.get("ltp", 0)

    # % CHANGE
    ce_diff = round((ce_ltp - ce_open) / ce_open * 100, 2)
    pe_diff = round((pe_ltp - pe_open) / pe_open * 100, 2)

    # RESULT LOGIC
    result = "NEUTRAL"

    if mode == "buyer":

        if pe_diff > threshold and ce_diff < -threshold:
            result = "SUPER BEARISH"

        elif ce_diff > threshold and pe_diff < -threshold:
            result = "SUPER BULLISH"

        elif pe_diff > threshold:
            result = "BEARISH"

        elif ce_diff > threshold:
            result = "BULLISH"

    elif mode == "seller":

        if ce_diff < -threshold and pe_diff > threshold:
            result = "SUPER BEARISH"

        elif pe_diff < -threshold and ce_diff > threshold:
            result = "SUPER BULLISH"

    now = datetime.now().strftime("%H:%M:%S")

    # PRINT ROW
    print(f"{now:<9} {nifty_ltp:<9} | "
          f"{ce_ltp:<7} {ce_diff:<7} | "
          f"{pe_ltp:<7} {pe_diff:<7} | "
          f"{R1:<6} {R2:<6} {R3:<6} | "
          f"{S1:<6} {S2:<6} {S3:<6} | "
          f"{result}")

    time.sleep(interval)
