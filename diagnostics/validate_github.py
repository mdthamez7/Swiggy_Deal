import os, json

required = ["SWIGGY_ACCESS_TOKEN"]
missing = [x for x in required if not os.getenv(x, "").strip()]
if missing:
    raise SystemExit("Missing required GitHub Secrets: " + ", ".join(missing))

raw = os.getenv("TARGET_LOCATIONS_JSON", "").strip()
if raw:
    try:
        locations = json.loads(raw)
    except Exception as e:
        raise SystemExit(f"TARGET_LOCATIONS_JSON is invalid JSON: {e}")
else:
    locations = []

if locations and not isinstance(locations, list):
    raise SystemExit("TARGET_LOCATIONS_JSON must be a JSON array.")

for i, item in enumerate(locations):
    if not isinstance(item, dict):
        raise SystemExit(f"TARGET_LOCATIONS_JSON item {i} must be an object.")
    for field in ("state", "city", "pincode"):
        if not str(item.get(field, "")).strip():
            raise SystemExit(f"TARGET_LOCATIONS_JSON item {i} is missing '{field}'.")

mcp_url = os.getenv('SWIGGY_IM_MCP_URL', '').strip() or 'https://mcp.swiggy.com/im'
if not (mcp_url.startswith('https://') or mcp_url.startswith('http://')):
    raise SystemExit("SWIGGY_IM_MCP_URL must start with http:// or https://. Current value is invalid.")

print(f"Configuration OK. GitHub target variable contains {len(locations)} locations.")
print(f"Swiggy MCP endpoint: {mcp_url}")
print("Address IDs will be resolved at runtime from the authenticated Swiggy account's saved addresses.")
