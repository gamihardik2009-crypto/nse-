import requests
import re

url = "https://groww.in/options/nifty"

headers = {
    "user-agent": "Mozilla/5.0"
}

r = requests.get(url, headers=headers)

html = r.text

matches = re.findall(r'NIFTY(\d{5})\d{4,5}(CE|PE)', html)

expiry_codes = [m[0] for m in matches]

latest_expiry = expiry_codes[0]

print("Latest expiry code:", latest_expiry)

print(html)
