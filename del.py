
from datetime import datetime

def get_hours_difference(datetime_str1, datetime_str2):
    # positive when datetime_str1 > datetime_str2
    
    # Convert the strings to datetime objects
    dt1 = datetime.fromisoformat(datetime_str1)
    dt2 = datetime.fromisoformat(datetime_str2)

    # Calculate the difference
    datediff = dt1 - dt2

    # Get total difference in hours
    hours_diff = (datediff.days * 24) + (datediff.seconds // 3600)
    print("Total Hours Difference:", hours_diff)
    return hours_diff


def get_env(path=".env"):
    env = {}
    with open(path, "r") as f:
        for line in f.readlines():
            if not line.strip():
                continue
            if line[0] == "#":
                continue
            items = line[:-1].split("=")
            name = items[0]
            value = "=".join(items[1:])
            env[name] = value
    return env









import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets

key_name = get_env()["CDP_API_KEY"]
key_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]

def build_jwt():
    private_key_bytes = key_secret.encode('utf-8')
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

    jwt_payload = {
        'sub': key_name,
        'iss': "cdp",
        'nbf': int(time.time()),
        'exp': int(time.time()) + 120,
    }

    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm='ES256',
        headers={'kid': key_name, 'nonce': secrets.token_hex()},
    )

    return jwt_token

def main():
    jwt_token = build_jwt()

    print(f"export JWT={jwt_token}")

if __name__ == "__main__":
    main()





import http.client
import json

conn = http.client.HTTPSConnection("api.coinbase.com")
payload = ''
headers = {
  'Content-Type': 'application/json'
}
conn.request("GET", "/api/v3/brokerage/products", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

