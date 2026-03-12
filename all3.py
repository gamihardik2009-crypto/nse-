import requests
import json
import time
import re
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# ---------------- USER INPUT ----------------

index = input("Select Index (nifty / banknifty / sensex): ").upper()

interval = float(input("Refresh time (seconds): "))
mode = input("Mode (buyer/seller): ").lower()
threshold = float(input("Threshold %: "))
oi_mode = int(input("OI Mode (1 = Total OI , 2 = OI Change): "))


# ---------------- INDEX SETTINGS ----------------

if index == "NIFTY":
    exchange = "NSE"
    strike_step = 50
    option_page = "https://groww.in/options/nifty"

elif index == "BANKNIFTY":
    exchange = "NSE"
    strike_step = 100
    option_page = "https://groww.in/options/nifty-bank"

elif index == "SENSEX":
    exchange = "BSE"
    strike_step = 100
    option_page = "https://groww.in/options/sp-bse-sensex"

else:
    print("Invalid Index")
    exit()


# ---------------- API URLS ----------------

index_url = f"https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/{exchange}/segment/CASH/latest_indices_ohlc/{index}"

option_url = f"https://groww.in/v1/api/stocks_fo_data/v1/tr_live_prices/exchange/{exchange}/segment/FNO/latest_prices_batch"


headers = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "x-app-id": "growwWeb",
    "user-agent": "Mozilla/5.0"
}


session = requests.Session()


# ---------------- EXPIRY DETECTION ----------------

r = session.get(option_page, headers=headers)

html = r.text

if index == "BANKNIFTY":
    match = re.search(r'BANKNIFTY(\d{2}[A-Z]{3})', html)
else:
    match = re.search(rf'{index}(\d{{5}})', html)

if not match:
    print("Expiry detection failed")
    exit()

latest_expiry = match.group(1)

print("\nIndex:", index)
print("Expiry Code:", latest_expiry)


# ---------------- INDEX OPEN ----------------

r = session.get(index_url, headers=headers)

index_open = r.json()["open"]

atm_strike = round(index_open / strike_step) * strike_step


# ---------------- SYMBOL LIST ----------------

symbols = []

# wider scan range
scan_range = 25

for i in range(-scan_range, scan_range + 1):

    strike = atm_strike + (i * strike_step)

    symbols.append(f"{index}{latest_expiry}{strike}CE")
    symbols.append(f"{index}{latest_expiry}{strike}PE")


ce_symbol = f"{index}{latest_expiry}{atm_strike}CE"
pe_symbol = f"{index}{latest_expiry}{atm_strike}PE"


# ---------------- GET OPEN PRICES ----------------

payload = json.dumps(symbols)

r = session.post(option_url, headers=headers, data=payload)

option_data = r.json()

ce_open = option_data.get(ce_symbol, {}).get("open", 0)
pe_open = option_data.get(pe_symbol, {}).get("open", 0)


print("Index Open:", index_open)
print("ATM Strike:", atm_strike)

print()
print(f"{'Time':<9} {'INDEX':<9} | {'CE':<7} {'CE%':<7} | {'PE':<7} {'PE%':<7} | {'CE_OI':<8} {'PE_OI':<8} | {'R1':<6} {'R2':<6} {'R3':<6} | {'S1':<6} {'S2':<6} {'S3':<6} | RESULT")
print("-"*140)


# ---------------- RESULT LOGIC ----------------

def calculate_result(mode, ce_diff, pe_diff, threshold):

    result = "NEUTRAL"

    if mode == "buyer":

        if ce_diff > 0 and pe_diff < 0:
            result = "BULLISH"

            if ce_diff >= threshold:
                result = "SUPER BULLISH"

        elif pe_diff > 0 and ce_diff < 0:
            result = "BEARISH"

            if pe_diff >= threshold:
                result = "SUPER BEARISH"

    elif mode == "seller":

        if pe_diff < 0 and ce_diff > 0:
            result = "BULLISH"

            if pe_diff <= -threshold:
                result = "SUPER BULLISH"

        elif ce_diff < 0 and pe_diff > 0:
            result = "BEARISH"

            if ce_diff <= -threshold:
                result = "SUPER BEARISH"

    return result


# ---------------- LOOP ----------------

try:

    while True:

        r = session.get(index_url, headers=headers)

        index_ltp = r.json()["value"]


        payload = json.dumps(symbols)

        r = session.post(option_url, headers=headers, data=payload)

        option_data = r.json()


        ce = option_data.get(ce_symbol, {})
        pe = option_data.get(pe_symbol, {})


        ce_ltp = ce.get("ltp", 0)
        pe_ltp = pe.get("ltp", 0)


        ce_diff = round((ce_ltp - ce_open) / ce_open * 100, 2)
        pe_diff = round((pe_ltp - pe_open) / pe_open * 100, 2)


        if oi_mode == 1:
            ce_oi = ce.get("openInterest", 0)
            pe_oi = pe.get("openInterest", 0)
        else:
            ce_oi = round(ce.get("oiDayChange", 0))
            pe_oi = round(pe.get("oiDayChange", 0))


        ce_list = []
        pe_list = []

        for sym, val in option_data.items():

            strike = int(re.search(r'(\d+)(?=CE|PE)', sym).group(1)[-5:])

            if oi_mode == 1:
                oi_val = val.get("openInterest", 0)
            else:
                oi_val = round(val.get("oiDayChange", 0))

            if "CE" in sym:
                ce_list.append((strike, oi_val))

            if "PE" in sym:
                pe_list.append((strike, oi_val))


        ce_sorted = sorted(ce_list, key=lambda x: x[1], reverse=True)
        pe_sorted = sorted(pe_list, key=lambda x: x[1], reverse=True)


        R1, R2, R3 = ce_sorted[0][0], ce_sorted[1][0], ce_sorted[2][0]
        S1, S2, S3 = pe_sorted[0][0], pe_sorted[1][0], pe_sorted[2][0]


        result = calculate_result(mode, ce_diff, pe_diff, threshold)


        if "BEARISH" in result:
            result = Fore.RED + result + Style.RESET_ALL

        elif "BULLISH" in result:
            result = Fore.GREEN + result + Style.RESET_ALL


        now = datetime.now().strftime("%H:%M:%S")


        print(f"{now:<9} {index_ltp:<9} | "
              f"{ce_ltp:<7} {ce_diff:<7} | "
              f"{pe_ltp:<7} {pe_diff:<7} | "
              f"{ce_oi:<8} {pe_oi:<8} | "
              f"{R1:<6} {R2:<6} {R3:<6} | "
              f"{S1:<6} {S2:<6} {S3:<6} | "
              f"{result}")


        time.sleep(interval)


except KeyboardInterrupt:

    print("\nScript stopped by user.")
