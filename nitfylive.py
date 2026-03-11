import requests

url = "https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/NSE/segment/CASH/latest_indices_ohlc/NIFTY"

headers = {
    "accept": "application/json, text/plain, */*",
    "referer": "https://groww.in/indices/nifty",
    "user-agent": "Mozilla/5.0",
    "x-app-id": "growwWeb"
}

response = requests.get(url, headers=headers)

data = response.json()

# values
ltp = data["value"]
open_price = data["open"]

# ATM strike
atm = round(open_price / 50) * 50

print("NIFTY Current:", ltp)
print("NIFTY Open:", open_price)
print("ATM Strike:", atm)
