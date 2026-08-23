from pathlib import Path

import httpx

base = "http://127.0.0.1:8000/api"
client = httpx.Client(timeout=60.0)

email = "demo@example.com"
password = "demo1234"
r = client.post(
    f"{base}/auth/register",
    json={"email": email, "full_name": "Demo User", "password": password},
)
if r.status_code >= 400:
    r = client.post(f"{base}/auth/login", json={"email": email, "password": password})
r.raise_for_status()
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("auth ok")

rp = client.post(
    f"{base}/business/profile",
    headers=headers,
    json={
        "business_name": "Demo Electronics",
        "business_type": "Retail",
        "industry": "Electronics",
        "location": "Pune",
        "currency": "INR",
        "business_size": "SME",
    },
)
rp.raise_for_status()
print("profile ok")

sample = Path("sample_data")
for name, dtype in [
    ("sales.csv", "sales"),
    ("expenses.csv", "expenses"),
    ("inventory.csv", "inventory"),
    ("reviews.csv", "reviews"),
    ("customers.csv", "customers"),
    ("business_policy.txt", "auto"),
]:
    files = {"file": (name, (sample / name).read_bytes())}
    data = {"data_type": dtype}
    up = client.post(f"{base}/upload", headers=headers, files=files, data=data)
    up.raise_for_status()
    print("uploaded", name, up.json()["data_type"])

dash = client.get(f"{base}/analytics/dashboard", headers=headers)
dash.raise_for_status()
kpis = dash.json()["kpis"]
print("revenue", kpis["total_revenue"], "profit", kpis["net_profit"])

fore = client.get(f"{base}/ml/forecast", headers=headers)
fore.raise_for_status()
print("forecast", fore.json().get("next_month_revenue"))

ins = client.get(f"{base}/ai/insights", headers=headers)
ins.raise_for_status()
summary = ins.json()["summary"][:120].encode("ascii", "replace").decode("ascii")
print("insights", summary, "...")

chat = client.post(
    f"{base}/ai/assistant",
    headers=headers,
    json={"question": "Which products need to be reordered?"},
)
chat.raise_for_status()
answer = chat.json()["answer"][:160].encode("ascii", "replace").decode("ascii")
print("assistant", answer)
print("SMOKE_OK")
