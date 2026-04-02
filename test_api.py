import requests
import json

base_url = "http://localhost:8888/api/v1"

# Login
r = requests.post(
    f"{base_url}/auth/login",
    data={"username": "admin", "password": "password"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get enterprises
r = requests.get(f"{base_url}/enterprises", headers=headers)
enterprises = r.json()["data"]
if not enterprises:
    print("No enterprises found")
    exit(1)
ent_id = enterprises[0]["id"]

# Fetch notices
print(f"Fetching notices for enterprise {ent_id} from 安徽...")
r = requests.post(f"{base_url}/tender-notices/fetch", 
    headers=headers, 
    json={"enterprise_id": ent_id, "region": "安徽", "keywords": "配送"}
)
print("Status Code:", r.status_code)
# Only print first 500 characters of response to avoid huge outputs
print("Response:", str(r.json())[:500])

