import requests
import json
import time
import re
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

interval = float(input("Refresh time (seconds): "))
mode = input("Mode (buyer/seller): ").lower()
threshold = float(input("Threshold % (example 50): "))
oi_mode = int(input("OI Mode (1 = Total OI , 2 = OI Change): "))

headers = {
    "accept": "application/json, text/plain, */*",
    "referer": "https://groww.in/",
    "user-agent": "Mozilla/5.0",
    "x-app-id": "growwWeb"
}

nifty_url = "https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/NIFTY"

option_url = "https://groww.in/v1/api/stocks_fo_data/v1/tr_live_prices/exchange/NSE/segment/FNO/latest_prices_batch"


# -------- FIND EXPIRY --------

expiry_page = "https://groww.in/options/nifty"

r = requests.get(expiry_page, headers=headers)

matches = re.findall(r'NIFTY(\d{5})\d{4,5}(CE|PE)', r.text)

latest_expiry = matches[0][0]

print("Latest Expiry:", latest_expiry)


# -------- GET NIFTY OPEN --------

r = requests.get(nifty_url, headers=headers)

nifty_open = r.json()["open"]

atm_strike = round(nifty_open / 50) * 50


symbols = []

for i in range(-10, 11):

    strike = atm_strike + (i * 50)

    symbols.append(f"NIFTY{latest_expiry}{strike}CE")

    symbols.append(f"NIFTY{latest_expiry}{strike}PE")


ce_symbol = f"NIFTY{latest_expiry}{atm_strike}CE"

pe_symbol = f"NIFTY{latest_expiry}{atm_strike}PE"


payload = json.dumps(symbols)

r = requests.post(option_url, headers=headers, data=payload)

option_data = r.json()


ce_open = option_data.get(ce_symbol, {}).get("open", 0)

pe_open = option_data.get(pe_symbol, {}).get("open", 0)


print("NIFTY OPEN:", nifty_open)

print("ATM STRIKE:", atm_strike)

print("Tracking:", ce_symbol, "/", pe_symbol)

print("CE OPEN:", ce_open)

print("PE OPEN:", pe_open)

print()


print(f"{'Time':<9} {'NIFTY':<9} | {'CE':<7} {'CE%':<7} | {'PE':<7} {'PE%':<7} | {'CE_OI':<8} {'PE_OI':<8} | {'R1':<6} {'R2':<6} {'R3':<6} | {'S1':<6} {'S2':<6} {'S3':<6} | RESULT")

print("-"*140)


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


        elif ce_diff < 0 and pe_diff < 0:

            result = "NEUTRAL"

            if abs(ce_diff) >= threshold or abs(pe_diff) >= threshold:

                result = "SUPER NEUTRAL"



    elif mode == "seller":

        if pe_diff < 0 and ce_diff > 0:

            result = "BULLISH"

            if pe_diff <= -threshold and ce_diff >= 0:

                result = "SUPER BULLISH"


        elif ce_diff < 0 and pe_diff > 0:

            result = "BEARISH"

            if ce_diff <= -threshold and pe_diff >= 0:

                result = "SUPER BEARISH"


        elif ce_diff < 0 and pe_diff < 0:

            result = "NEUTRAL"

            if abs(ce_diff) >= threshold or abs(pe_diff) >= threshold:

                result = "SUPER NEUTRAL"


    return result



try:

    while True:


        r = requests.get(nifty_url, headers=headers)

        nifty_ltp = r.json()["value"]


        payload = json.dumps(symbols)

        r = requests.post(option_url, headers=headers, data=payload)

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

            strike = int(re.search(r'(\d{5})(CE|PE)', sym).group(1))


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

        elif "SUPER NEUTRAL" in result:

            result = Fore.YELLOW + result + Style.RESET_ALL


        now = datetime.now().strftime("%H:%M:%S")


        print(f"{now:<9} {nifty_ltp:<9} | "

              f"{ce_ltp:<7} {ce_diff:<7} | "

              f"{pe_ltp:<7} {pe_diff:<7} | "

              f"{ce_oi:<8} {pe_oi:<8} | "

              f"{R1:<6} {R2:<6} {R3:<6} | "

              f"{S1:<6} {S2:<6} {S3:<6} | "

              f"{result}")


        time.sleep(interval)



except KeyboardInterrupt:

    print("\nScript stopped by user.")
