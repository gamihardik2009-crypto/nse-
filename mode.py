import requests
import json
import time
import re
from datetime import datetime
from colorama import Fore, Style, init

init()

# -------- USER INPUT --------
interval = float(input("Refresh time (seconds): "))
mode = input("Mode (buyer/seller): ").lower()
threshold = float(input("Threshold % (example 50): "))

oi_mode = input("OI Mode (1 = Total OI , 2 = OI Change): ")

# -------- HEADERS --------
headers = {
    "accept": "application/json, text/plain, */*",
    "referer": "https://groww.in/indices/nifty",
    "user-agent": "Mozilla/5.0",
    "x-app-id": "growwWeb"
}

# -------- APIs --------
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

print("NIFTY OPEN:", nifty_open)
print("ATM STRIKE:", atm_strike)

# -------- GENERATE STRIKE LIST (FOR OI) --------
def generate_symbols(expiry, atm, steps=10):

    symbols = []

    for i in range(-steps, steps+1):

        strike = atm + i*50

        symbols.append(f"NIFTY{expiry}{strike}CE")
        symbols.append(f"NIFTY{expiry}{strike}PE")

    return symbols


symbols = generate_symbols(latest_expiry, atm_strike)

ce_symbol = f"NIFTY{latest_expiry}{atm_strike}CE"
pe_symbol = f"NIFTY{latest_expiry}{atm_strike}PE"

# -------- GET OPEN PRICE --------
payload = json.dumps(symbols)

r2 = requests.post(option_url, headers=headers, data=payload)
option_data = r2.json()

ce_open = option_data.get(ce_symbol, {}).get("open", 0)
pe_open = option_data.get(pe_symbol, {}).get("open", 0)

print("Tracking:", ce_symbol, "/", pe_symbol)
print("CE OPEN:", ce_open)
print("PE OPEN:", pe_open)

# -------- MARKET RESULT --------
def get_result(nifty_move, ce_diff, pe_diff):

    if mode == "buyer":

        if nifty_move > 0 and ce_diff > 0 and pe_diff < 0:
            if ce_diff >= threshold:
                return "SUPER BULLISH"
            return "BULLISH"

        if nifty_move < 0 and pe_diff > 0 and ce_diff < 0:
            if pe_diff >= threshold:
                return "SUPER BEARISH"
            return "BEARISH"

        if ce_diff < 0 and pe_diff < 0:
            if abs(ce_diff) >= threshold or abs(pe_diff) >= threshold:
                return "SUPER NEUTRAL"
            return "NEUTRAL"

    if mode == "seller":

        if nifty_move > 0 and pe_diff < 0:
            if pe_diff <= -threshold:
                return "SUPER BULLISH"
            return "BULLISH"

        if nifty_move < 0 and ce_diff < 0:
            if ce_diff <= -threshold:
                return "SUPER BEARISH"
            return "BEARISH"

        if ce_diff < 0 and pe_diff < 0:
            return "SUPER NEUTRAL"

    return "NEUTRAL"


# -------- OI EXTRACTION --------
def extract_oi(data):

    call_oi = {}
    put_oi = {}

    for symbol, d in data.items():

        strike = int(re.search(r'(\d{5})(CE|PE)', symbol).group(1))

        if oi_mode == "1":
            oi = d.get("openInterest",0)
        else:
            oi = d.get("oiDayChange",0)

        if "CE" in symbol:
            call_oi[strike] = oi
        else:
            put_oi[strike] = oi

    return call_oi, put_oi


# -------- SUPPORT / RESISTANCE --------
def get_sr(call_oi, put_oi):

    resistance = sorted(call_oi.items(), key=lambda x:x[1], reverse=True)[:3]
    support = sorted(put_oi.items(), key=lambda x:x[1], reverse=True)[:3]

    return resistance, support


print("\nLIVE DATA\n")

print(f"{'Time':<10} {'NIFTY':<8} | {'CE':<7} {'CE%':<7} | {'PE':<7} {'PE%':<7} | RESULT")
print("-"*80)


# -------- LOOP --------
while True:

    r = requests.get(nifty_url, headers=headers)
    data = r.json()

    nifty_ltp = data["value"]
    nifty_move = nifty_ltp - nifty_open

    payload = json.dumps(symbols)

    r2 = requests.post(option_url, headers=headers, data=payload)
    option_data = r2.json()

    ce = option_data.get(ce_symbol,{})
    pe = option_data.get(pe_symbol,{})

    ce_ltp = ce.get("ltp",0)
    pe_ltp = pe.get("ltp",0)

    ce_diff = round((ce_ltp-ce_open)/ce_open*100,2) if ce_open else 0
    pe_diff = round((pe_ltp-pe_open)/pe_open*100,2) if pe_open else 0

    result = get_result(nifty_move, ce_diff, pe_diff)

    # -------- COLORS --------
    color = Fore.WHITE

    if result == "BULLISH":
        color = Fore.GREEN

    if result == "SUPER BULLISH":
        color = Fore.LIGHTGREEN_EX

    if result == "BEARISH":
        color = Fore.RED

    if result == "SUPER BEARISH":
        color = Fore.LIGHTRED_EX

    if result == "NEUTRAL":
        color = Fore.WHITE

    if result == "SUPER NEUTRAL":
        color = Fore.YELLOW

    now = datetime.now().strftime("%H:%M:%S")

    print(f"{now:<10} {nifty_ltp:<8} | {ce_ltp:<7} {ce_diff:<7} | {pe_ltp:<7} {pe_diff:<7} | {color}{result}{Style.RESET_ALL}")

    # -------- OI STRUCTURE --------
    call_oi, put_oi = extract_oi(option_data)

    resistance, support = get_sr(call_oi, put_oi)

    print("\nOI STRUCTURE")

    print("R3:", resistance[2][0])
    print("R2:", resistance[1][0])
    print("R1:", resistance[0][0])

    print("PRICE:", atm_strike)

    print("S1:", support[0][0])
    print("S2:", support[1][0])
    print("S3:", support[2][0])

    print("-"*80)

    time.sleep(interval)
